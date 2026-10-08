"""Recuperación de contraseña mediante enlace temporal enviado por correo."""
from email.message import EmailMessage
import hmac
import logging
import smtplib
from urllib.parse import urlencode

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuditLog, User
from app.schemas import PASSWORD_RULE
from app.security import create_password_reset_token, decode_password_reset_token, hash_password, password_reset_fingerprint

logger = logging.getLogger(__name__)
TOKEN_LIFETIME_MINUTES = 30


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72 or not PASSWORD_RULE.fullmatch(value):
            raise ValueError("Usa 12–72 caracteres con mayúscula, minúscula, número y símbolo, sin espacios.")
        return value


def smtp_is_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from_email)


def send_reset_email(recipient: str, token: str) -> None:
    reset_url = f"{settings.frontend_url.rstrip('/')}/restablecer-contrasena?{urlencode({'token': token})}"
    message = EmailMessage()
    message["Subject"] = "Recupera tu contraseña del Taller Mecánico"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        "Recibimos una solicitud para recuperar la contraseña de tu cuenta. "
        f"Abre este enlace en los próximos {TOKEN_LIFETIME_MINUTES} minutos para elegir una nueva contraseña:\n\n"
        f"{reset_url}\n\nSi no solicitaste este cambio, puedes ignorar este mensaje."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password or "")
            server.send_message(message)
    except Exception:
        logger.exception("No se pudo enviar un correo de recuperación de contraseña.")


def request_password_reset(
    db: Session, payload: ForgotPasswordIn, background_tasks: BackgroundTasks,
) -> dict[str, str]:
    if not smtp_is_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "RECOVERY_NOT_CONFIGURED",
                "message": "La recuperación por correo aún no está configurada. Contacta al administrador del taller.",
            },
        )

    user = db.query(User).filter(User.email == str(payload.email).lower(), User.is_active.is_(True)).first()
    if user:
        reset_token = create_password_reset_token(user.id, user.password_hash)
        background_tasks.add_task(send_reset_email, user.email, reset_token)

    return {"code": "SUCCESS", "message": "Si existe una cuenta con ese correo, recibirá instrucciones para recuperar el acceso."}


def reset_password(db: Session, payload: ResetPasswordIn) -> None:
    try:
        claims = decode_password_reset_token(payload.token)
        user_id = int(claims["sub"])
        token_fingerprint = str(claims["pwd"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=400, detail={
            "code": "RESET_LINK_INVALID",
            "message": "El enlace ya no es válido. Solicita uno nuevo para recuperar tu contraseña.",
        })

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user or not hmac.compare_digest(token_fingerprint, password_reset_fingerprint(user.password_hash)):
        raise HTTPException(status_code=400, detail={
            "code": "RESET_LINK_INVALID",
            "message": "El enlace ya no es válido. Solicita uno nuevo para recuperar tu contraseña.",
        })

    try:
        user.password_hash = hash_password(payload.new_password)
        db.add(AuditLog(user_id=user.id, action="auth.password_reset", detail="Contraseña restablecida mediante enlace"))
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"code": "PERSISTENCE_ERROR", "message": "No pudimos guardar la nueva contraseña. Inténtalo de nuevo."},
        ) from exc
