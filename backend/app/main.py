"""API inicial para registro, autenticación, cambio de contraseña y salud."""
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import re
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from pydantic import ValidationError
from app.auth import current_user, require_roles
from app.config import settings
from app.database import get_db
from app.models import AuditLog, Client, Role, Status, User, Vehicle, Workshop
from app.schemas import AuthOut, ChangePasswordIn, LoginIn, RegisterIn, StaffUserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.client_registration import ClientAdminOut, ClientBuilder, ClientOut, ClientRegistrationAuditOut, ClientRegistrationFacade, ClientRegistrationIn, ClientUpdateIn, ClientWorkshopIn, ContactFormatStrategy
from app.password_recovery import ForgotPasswordIn, ResetPasswordIn, request_password_reset, reset_password
from app.administration import router as administration_router
from app.vehicle_registration import VEHICLE_UPLOAD_DIR, VehicleCreateIn, VehicleOut, register_vehicle

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(administration_router)
client_registration = ClientRegistrationFacade()


def user_output(user: User) -> UserOut:
    return UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role.code, role_name=user.role.name)


def auth_output(user: User) -> AuthOut:
    return AuthOut(access_token=create_access_token(user.id, user.role.code), expires_in=settings.access_token_minutes * 60, user=user_output(user))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(f"{settings.api_prefix}/clients", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_client(payload: ClientRegistrationIn, db: Session = Depends(get_db), user: User = Depends(require_roles("administrador", "recepcionista"))):
    client, duplicate_confirmed = client_registration.register(db, user, payload)
    return {"code": "SUCCESS", "message": "Cliente registrado correctamente.", "data": ClientOut.model_validate(client), "duplicate_confirmed": duplicate_confirmed}


def client_admin_output(client: Client, workshop_name: str | None) -> ClientAdminOut:
    return ClientAdminOut(
        id=client.id, full_name=client.full_name, street=client.street, number=client.number,
        neighborhood=client.neighborhood, municipality=client.municipality, state=client.state,
        primary_phone=client.primary_phone, alternate_phone=client.alternate_phone, email=client.email,
        is_active=client.id_estatus == 1, workshop_id=client.workshop_id, workshop_name=workshop_name,
    )


@app.get(f"{settings.api_prefix}/clients", response_model=list[ClientAdminOut])
def list_clients(db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    try:
        rows = db.query(Client, Workshop.name).outerjoin(Workshop, Workshop.id == Client.workshop_id).order_by(Client.id.desc()).all()
        return [client_admin_output(client, workshop_name) for client, workshop_name in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo consultar la lista de clientes."}) from exc


@app.put(f"{settings.api_prefix}/clients/{{client_id}}", response_model=ClientAdminOut)
def update_client(client_id: int, payload: ClientUpdateIn, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    try:
        client = db.query(Client).filter(Client.id == client_id).with_for_update().first()
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND", "message": "No se encontró el cliente."})
        ContactFormatStrategy().validate(payload)
        changes = ClientBuilder.normalize(payload)
        changes.pop("id_estatus")
        for field, value in changes.items():
            setattr(client, field, value)
        db.commit()
        db.refresh(client)
        workshop_name = db.query(Workshop.name).filter(Workshop.id == client.workshop_id).scalar() if client.workshop_id else None
        return client_admin_output(client, workshop_name)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudieron guardar los cambios del cliente."}) from exc


@app.delete(f"{settings.api_prefix}/clients/{{client_id}}")
def deactivate_client(client_id: int, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    try:
        client = db.query(Client).filter(Client.id == client_id).with_for_update().first()
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND", "message": "No se encontró el cliente."})
        if client.id_estatus == 2:
            raise HTTPException(status_code=409, detail={"code": "CLIENT_ALREADY_INACTIVE", "message": "El cliente ya está inactivo."})
        client.id_estatus = 2
        db.commit()
        return {"message": "Cliente desactivado correctamente."}
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo desactivar el cliente."}) from exc


@app.put(f"{settings.api_prefix}/clients/{{client_id}}/workshop", response_model=ClientAdminOut)
def associate_client_workshop(client_id: int, payload: ClientWorkshopIn, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    try:
        client = db.query(Client).filter(Client.id == client_id).with_for_update().first()
        if not client:
            raise HTTPException(status_code=404, detail={"code": "CLIENT_NOT_FOUND", "message": "No se encontró el cliente."})
        if client.id_estatus != 1:
            raise HTTPException(status_code=409, detail={"code": "CLIENT_INACTIVE", "message": "No se puede asociar un cliente inactivo."})
        workshop = db.query(Workshop).filter(Workshop.id == payload.workshop_id).with_for_update().first()
        if not workshop:
            raise HTTPException(status_code=404, detail={"code": "WORKSHOP_NOT_FOUND", "message": "No se encontró el taller."})
        if workshop.id_estatus != 1:
            raise HTTPException(status_code=409, detail={"code": "WORKSHOP_NOT_ACTIVE", "message": "Solo se puede asociar un taller activo."})
        client.workshop_id = workshop.id
        db.commit()
        db.refresh(client)
        return client_admin_output(client, workshop.name)
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo asociar el cliente al taller."}) from exc


@app.post(f"{settings.api_prefix}/clients/{{client_id}}/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_client_vehicle(
    client_id: int,
    vin: str = Form(...), plate: str = Form(...), make: str = Form(...), model: str = Form(...),
    year: int = Form(...), version: str = Form(...), color: str = Form(...), mileage: int = Form(...),
    photo: UploadFile | None = File(default=None),
    db: Session = Depends(get_db), actor: User = Depends(require_roles("administrador", "recepcionista")),
):
    try:
        payload = VehicleCreateIn(vin=vin, plate=plate, make=make, model=model, year=year,
                                  version=version, color=color, mileage=mileage)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail={
            "code": "INVALID_DATA", "message": "Revisa los datos del vehículo.",
            "errors": [{"field": str(error["loc"][0]), "message": error["msg"]} for error in exc.errors()],
        }) from exc
    vehicle = await register_vehicle(db, actor, client_id, payload, photo)
    return VehicleOut.model_validate(vehicle)


@app.get(f"{settings.api_prefix}/vehicles")
def list_vehicles(db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    try:
        rows = db.query(Vehicle, Client.full_name, Status.valor).join(Client, Client.id == Vehicle.client_id).join(
            Status, Status.id_estatus == Vehicle.id_estatus
        ).order_by(Vehicle.id.desc()).all()
        return [{
            **VehicleOut.model_validate(vehicle).model_dump(),
            "client_name": client_name,
            "status": status_name,
        } for vehicle, client_name, status_name in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo consultar la lista de vehículos."}) from exc


@app.get(f"{settings.api_prefix}/vehicles/{{vehicle_id}}/photo")
def vehicle_photo(vehicle_id: int, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle or not vehicle.photo_filename:
        raise HTTPException(404, detail={"code": "VEHICLE_PHOTO_NOT_FOUND", "message": "No se encontró la fotografía del vehículo."})
    photo_path = (VEHICLE_UPLOAD_DIR / vehicle.photo_filename).resolve()
    if photo_path.parent != VEHICLE_UPLOAD_DIR.resolve() or not photo_path.is_file():
        raise HTTPException(404, detail={"code": "VEHICLE_PHOTO_NOT_FOUND", "message": "No se encontró la fotografía del vehículo."})
    media_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(photo_path.suffix.lower())
    if not media_type:
        raise HTTPException(404, detail={"code": "VEHICLE_PHOTO_NOT_FOUND", "message": "No se encontró la fotografía del vehículo."})
    return FileResponse(photo_path, media_type=media_type)


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
    role = db.query(Role).filter(Role.code == "cliente", Role.id_estatus == 1).first()
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
    if not user or not user.is_active or user.role.id_estatus != 1 or not verify_password(payload.password, user.password_hash):
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
        User.role.has(Role.code != "cliente")
    ).order_by(User.created_at.desc()).all()
    return [user_output(item) for item in users]


@app.post(f"{settings.api_prefix}/admin/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff_user(payload: StaffUserCreate, db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    role = db.query(Role).filter(Role.id == payload.role_id, Role.id_estatus == 1).with_for_update().first()
    if not role:
        raise HTTPException(status_code=422, detail="El rol no existe o está suspendido")
    if role.code in {"cliente", "sistema"}:
        raise HTTPException(status_code=422, detail="Ese rol no puede asignarse a una cuenta del equipo")
    user = User(role_id=role.id, full_name=payload.full_name, email=email, password_hash=hash_password(payload.password), id_estatus=1)
    try:
        db.add(user)
        db.flush()
        db.add(AuditLog(user_id=admin.id, action="admin.user_created", detail=f"Cuenta {role.code} creada para {email}"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    db.refresh(user)
    created = db.query(User).options(joinedload(User.role)).filter(User.id == user.id).one()
    return user_output(created)
