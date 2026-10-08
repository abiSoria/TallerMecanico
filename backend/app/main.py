"""API inicial para registro, autenticación, cambio de contraseña y salud."""
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.auth import current_user, require_roles
from app.config import settings
from app.database import get_db
from app.models import AuditLog, Client, Role, User
from app.schemas import AuthOut, ChangePasswordIn, LoginIn, RegisterIn, StaffUserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.client_registration import ClientOut, ClientRegistrationAuditOut, ClientRegistrationFacade, ClientRegistrationIn
from app.password_recovery import ForgotPasswordIn, ResetPasswordIn, request_password_reset, reset_password

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
client_registration = ClientRegistrationFacade()


def user_output(user: User) -> UserOut:
    return UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role.name)


def auth_output(user: User) -> AuthOut:
    return AuthOut(access_token=create_access_token(user.id, user.role.name), expires_in=settings.access_token_minutes * 60, user=user_output(user))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(f"{settings.api_prefix}/clients", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_client(payload: ClientRegistrationIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    client, duplicate_confirmed = client_registration.register(db, user, payload)
    return {"code": "SUCCESS", "message": "Cliente registrado correctamente.", "data": ClientOut.model_validate(client), "duplicate_confirmed": duplicate_confirmed}


@app.get(f"{settings.api_prefix}/admin/client-registrations", response_model=list[ClientRegistrationAuditOut])
def list_client_registrations(db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    entries = db.query(AuditLog, User).outerjoin(User, User.id == AuditLog.user_id).filter(
        AuditLog.action == "client.registered"
    ).order_by(AuditLog.created_at.desc()).all()
    client_ids = {
        int(match.group(1))
        for entry, _actor in entries
        if entry.detail and (match := re.fullmatch(r"client_id=(\d+)", entry.detail))
    }
    if not client_ids:
        return []

    clients = {client.id: client for client in db.query(Client).filter(Client.id.in_(client_ids)).all()}
    result = []
    for entry, actor in entries:
        match = re.fullmatch(r"client_id=(\d+)", entry.detail or "")
        client = clients.get(int(match.group(1))) if match else None
        if client:
            result.append(ClientRegistrationAuditOut(
                client_name=client.full_name,
                registered_by=actor.full_name if actor else "Usuario no disponible",
                registered_at=entry.created_at,
            ))
    return result


@app.post(f"{settings.api_prefix}/auth/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    # Los registros públicos siempre son clientes: nunca aceptamos el rol desde el cliente.
    role = db.query(Role).filter(Role.name == "cliente").first()
    if not role:
        raise HTTPException(status_code=500, detail="Falta configurar el rol cliente en la base de datos")
    user = User(role_id=role.id, full_name=payload.full_name, email=email, password_hash=hash_password(payload.password))
    try:
        db.add(user)
        db.flush()
        db.add(AuditLog(user_id=user.id, action="auth.register", detail="Cuenta de cliente creada"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    db.refresh(user)
    user = db.query(User).options(joinedload(User.role)).get(user.id)
    return auth_output(user)


@app.post(f"{settings.api_prefix}/auth/login", response_model=AuthOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.role)).filter(User.email == str(payload.email).lower()).first()
    # Respuesta genérica evita revelar si el correo está registrado.
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos", headers={"WWW-Authenticate": "Bearer"})
    db.add(AuditLog(user_id=user.id, action="auth.login", detail="Inicio de sesión correcto"))
    db.commit()
    return auth_output(user)


@app.post(f"{settings.api_prefix}/auth/forgot-password")
def forgot_password(payload: ForgotPasswordIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return request_password_reset(db, payload, background_tasks)


@app.post(f"{settings.api_prefix}/auth/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_account_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    reset_password(db, payload)


@app.get(f"{settings.api_prefix}/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user_output(user)


@app.post(f"{settings.api_prefix}/auth/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ChangePasswordIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="La nueva contraseña debe ser distinta")
    user.password_hash = hash_password(payload.new_password)
    db.add(AuditLog(user_id=user.id, action="auth.password_changed", detail="Contraseña actualizada"))
    db.commit()


@app.get(f"{settings.api_prefix}/admin/users", response_model=list[UserOut])
def list_staff_users(db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    users = db.query(User).options(joinedload(User.role)).filter(
        User.role.has(Role.name != "cliente")
    ).order_by(User.created_at.desc()).all()
    return [user_output(item) for item in users]


@app.post(f"{settings.api_prefix}/admin/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff_user(payload: StaffUserCreate, db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role:
        raise HTTPException(status_code=422, detail="El rol todavía no está configurado en la base de datos")
    user = User(role_id=role.id, full_name=payload.full_name, email=email, password_hash=hash_password(payload.password))
    try:
        db.add(user)
        db.flush()
        db.add(AuditLog(user_id=admin.id, action="admin.user_created", detail=f"Cuenta {payload.role} creada para {email}"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    db.refresh(user)
    created = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).one()
    return user_output(created)
