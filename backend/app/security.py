"""Hash BCrypt y JWT de corta duración con identidad y rol."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import bcrypt
from jose import JWTError, jwt
from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, UnicodeError):
        return False


def create_access_token(user_id: int, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expires}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _reset_key(purpose: bytes) -> bytes:
    return hmac.new(settings.jwt_secret_key.encode("utf-8"), purpose, hashlib.sha256).digest()


def create_password_reset_token(user_id: int, password_hash: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    fingerprint = hmac.new(_reset_key(b"password-fingerprint"), password_hash.encode("utf-8"), hashlib.sha256).hexdigest()
    return jwt.encode(
        {"sub": str(user_id), "purpose": "password-reset", "pwd": fingerprint, "exp": expires},
        _reset_key(b"password-reset-signing"), algorithm=settings.jwt_algorithm,
    )


def decode_password_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _reset_key(b"password-reset-signing"), algorithms=[settings.jwt_algorithm])
        if payload.get("purpose") != "password-reset":
            raise ValueError("Token de recuperación no válido")
        return payload
    except JWTError as exc:
        raise ValueError("Token de recuperación no válido o vencido") from exc


def password_reset_fingerprint(password_hash: str) -> str:
    return hmac.new(_reset_key(b"password-fingerprint"), password_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token inválido o expirado") from exc
