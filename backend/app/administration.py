"""Casos de uso de roles, talleres y consulta del catálogo postal local."""
from pathlib import Path
from io import BytesIO
from uuid import uuid4
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.config import settings
from app.database import get_db
from app.models import AuditLog, PostalCode, Role, Status, User, Workshop

router = APIRouter(prefix=settings.api_prefix)
ROLE_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "workshops"
MAX_PHOTO_BYTES = 10 * 1024 * 1024
IMAGE_TYPES = {
    ".jpg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    ".jpeg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    ".png": ("image/png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    ".webp": ("image/webp", lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
}
RFC_PATTERN = re.compile(r"^(?:[A-ZÑ&]{3}|[A-ZÑ&]{4})\d{6}[A-Z0-9]{3}$")


class RoleIn(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    description: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value or not re.fullmatch(r"[\wÀ-ÿ .'-]+", value):
            raise ValueError("Escribe un nombre de rol válido.")
        if len(value.casefold()) > 40:
            raise ValueError("El nombre normalizado no puede superar 40 caracteres.")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


def role_data(role: Role, status_row: Status) -> dict:
    return {"id": role.id, "code": role.code, "name": role.name, "description": role.description,
            "id_estatus": role.id_estatus, "estatus": status_row.valor, "estatus_descripcion": status_row.descripcion}


def role_conflict(db: Session, name: str, exclude_id: int | None = None) -> bool:
    query = db.query(Role.id).filter(Role.normalized_name == name.strip().casefold())
    if exclude_id is not None:
        query = query.filter(Role.id != exclude_id)
    return query.first() is not None


@router.get("/admin/roles")
def list_roles(db: Session = Depends(get_db), _admin: User = Depends(require_roles("administrador"))):
    rows = db.query(Role, Status).join(Status, Role.id_estatus == Status.id_estatus).order_by(Role.name).all()
    return [role_data(role, status_row) for role, status_row in rows]


@router.get("/admin/roles/active")
def list_active_roles(db: Session = Depends(get_db), _admin: User = Depends(require_roles("administrador"))):
    rows = db.query(Role, Status).join(Status, Role.id_estatus == Status.id_estatus).filter(Role.id_estatus == 1).order_by(Role.name).all()
    return [role_data(role, status_row) for role, status_row in rows]


@router.post("/admin/roles", status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleIn, db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    if role_conflict(db, payload.name):
        raise HTTPException(409, detail={"code": "DUPLICATE_ROLE", "message": "Ya existe un rol con ese nombre."})
    role = Role(code=f"custom_{uuid4().hex}", name=payload.name, normalized_name=payload.name.casefold(), description=payload.description, id_estatus=1)
    try:
        db.add(role); db.flush()
        db.add(AuditLog(user_id=admin.id, action="admin.role_created", detail=f"role_id={role.id}"))
        db.commit(); db.refresh(role)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail={"code": "DUPLICATE_ROLE", "message": "Ya existe un rol con ese nombre."}) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo guardar el rol."}) from exc
    return role_data(role, db.query(Status).filter(Status.id_estatus == role.id_estatus).one())


@router.put("/admin/roles/{role_id}")
def update_role(role_id: int, payload: RoleIn, db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(404, detail={"code": "ROLE_NOT_FOUND", "message": "No se encontró ese rol."})
    if role_conflict(db, payload.name, role_id):
        raise HTTPException(409, detail={"code": "DUPLICATE_ROLE", "message": "Ya existe otro rol con ese nombre."})
    role.name, role.normalized_name, role.description = payload.name, payload.name.casefold(), payload.description
    try:
        db.add(AuditLog(user_id=admin.id, action="admin.role_updated", detail=f"role_id={role.id}"))
        db.commit(); db.refresh(role)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail={"code": "DUPLICATE_ROLE", "message": "Ya existe otro rol con ese nombre."}) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo actualizar el rol."}) from exc
    return role_data(role, db.query(Status).filter(Status.id_estatus == role.id_estatus).one())


@router.delete("/admin/roles/{role_id}")
def suspend_role(role_id: int, db: Session = Depends(get_db), admin: User = Depends(require_roles("administrador"))):
    role = db.query(Role).filter(Role.id == role_id).with_for_update().first()
    if not role:
        raise HTTPException(404, detail={"code": "ROLE_NOT_FOUND", "message": "No se encontró ese rol."})
    if role.id_estatus == 2:
        raise HTTPException(409, detail={"code": "ALREADY_SUSPENDED", "message": "Ese rol ya está suspendido."})
    if role.code == "administrador" or db.query(User.id).filter(User.role_id == role_id).first():
        raise HTTPException(409, detail={"code": "ROLE_IN_USE", "message": "No se puede suspender un rol asignado a usuarios ni el rol administrador."})
    role.id_estatus = 2
    db.add(AuditLog(user_id=admin.id, action="admin.role_suspended", detail=f"role_id={role.id}"))
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo suspender el rol."}) from exc
    return {"code": "ROLE_SUSPENDED", "message": "El rol quedó suspendido."}


def postal_row(row: PostalCode) -> dict:
    return {"postal_code": row.postal_code, "neighborhood": row.neighborhood, "municipality": row.municipality, "state": row.state}


@router.get("/postal-codes/by-code/{postal_code}")
def postal_lookup(postal_code: str, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    if not re.fullmatch(r"\d{5}", postal_code):
        raise HTTPException(422, detail="El código postal debe tener cinco dígitos.")
    return [postal_row(row) for row in db.query(PostalCode).filter(PostalCode.postal_code == postal_code).order_by(PostalCode.neighborhood).all()]


@router.get("/postal-codes/search")
def postal_reverse_search(state: str, municipality: str, neighborhood: str, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    query = db.query(PostalCode).filter(
        func.lower(func.trim(PostalCode.state)) == state.strip().casefold(),
        func.lower(func.trim(PostalCode.municipality)) == municipality.strip().casefold(),
        func.lower(func.trim(PostalCode.neighborhood)) == neighborhood.strip().casefold(),
    ).order_by(PostalCode.postal_code)
    return [postal_row(row) for row in query.limit(100).all()]


@router.get("/workshops")
def list_workshops(db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    rows = db.query(Workshop, Status).join(Status, Workshop.id_estatus == Status.id_estatus).order_by(Workshop.created_at.desc(), Workshop.id.desc()).all()
    return [{
        "id": workshop.id,
        "name": workshop.name,
        "rfc": workshop.rfc,
        "contact_email": workshop.contact_email,
        "street": workshop.street,
        "number": workshop.number,
        "postal_code": workshop.postal_code,
        "state": workshop.state,
        "municipality": workshop.municipality,
        "neighborhood": workshop.neighborhood,
        "photo_filename": workshop.photo_filename,
        "id_estatus": workshop.id_estatus,
        "status": status_row.valor,
        "created_at": workshop.created_at,
    } for workshop, status_row in rows]


@router.get("/workshops/{workshop_id}/photo")
def workshop_photo(workshop_id: int, db: Session = Depends(get_db), _user: User = Depends(require_roles("administrador", "recepcionista"))):
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(404, detail={"code": "WORKSHOP_NOT_FOUND", "message": "No se encontró ese taller."})
    photo_path = (ROLE_UPLOAD_DIR / workshop.photo_filename).resolve()
    if photo_path.parent != ROLE_UPLOAD_DIR.resolve() or not photo_path.is_file():
        raise HTTPException(404, detail={"code": "WORKSHOP_PHOTO_NOT_FOUND", "message": "No se encontró la fotografía del taller."})
    media_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(photo_path.suffix.lower())
    if not media_type:
        raise HTTPException(404, detail={"code": "WORKSHOP_PHOTO_NOT_FOUND", "message": "No se encontró la fotografía del taller."})
    return FileResponse(photo_path, media_type=media_type)


@router.post("/workshops", status_code=status.HTTP_201_CREATED)
async def create_workshop(
    name: str = Form(...), rfc: str = Form(...), contact_email: EmailStr = Form(...),
    street: str = Form(...), number: str = Form(...), postal_code: str = Form(...),
    state_name: str = Form(..., alias="state"), municipality: str = Form(...), neighborhood: str = Form(...),
    photo: UploadFile = File(...), db: Session = Depends(get_db),
    actor: User = Depends(require_roles("administrador", "recepcionista")),
):
    values = {"Nombre del taller": name, "RFC": rfc, "Correo": str(contact_email), "Calle": street,
              "Número": number, "Código postal": postal_code, "Estado": state_name,
              "Municipio": municipality, "Colonia": neighborhood}
    if any(not value.strip() for value in values.values()):
        raise HTTPException(422, detail={"code": "INVALID_DATA", "message": "Completa todos los campos obligatorios."})
    clean_rfc = rfc.strip().upper()
    if not RFC_PATTERN.fullmatch(clean_rfc):
        raise HTTPException(422, detail={"code": "INVALID_RFC", "message": "El RFC no tiene una estructura válida para México."})
    postal_code = postal_code.strip()
    if not re.fullmatch(r"\d{5}", postal_code):
        raise HTTPException(422, detail={"code": "INVALID_POSTAL_CODE", "message": "El código postal debe tener cinco dígitos."})
    try:
        known_postal = db.query(PostalCode).filter(PostalCode.postal_code == postal_code).first()
        if known_postal:
            address_match = db.query(PostalCode.id).filter(
                PostalCode.postal_code == postal_code,
                func.lower(func.trim(PostalCode.state)) == state_name.strip().casefold(),
                func.lower(func.trim(PostalCode.municipality)) == municipality.strip().casefold(),
                func.lower(func.trim(PostalCode.neighborhood)) == neighborhood.strip().casefold(),
            ).first()
            if not address_match:
                raise HTTPException(422, detail={"code": "ADDRESS_MISMATCH", "message": "La colonia, municipio y estado no corresponden al código postal seleccionado."})
        if db.query(Workshop.id).filter(Workshop.rfc == clean_rfc).first():
            raise HTTPException(409, detail={"code": "DUPLICATE_RFC", "message": "Ya existe un taller registrado con ese RFC."})
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo verificar la información del taller."}) from exc

    suffix = Path(photo.filename or "").suffix.lower()
    spec = IMAGE_TYPES.get(suffix)
    if not spec:
        raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": "La fotografía debe ser JPG, JPEG, PNG o WebP."})
    content = await photo.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(413, detail={"code": "IMAGE_TOO_LARGE", "message": "La fotografía no puede superar 10 MB."})
    expected_mime, signature_check = spec
    if not signature_check(content) or photo.content_type not in (expected_mime, "application/octet-stream"):
        raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": "El contenido de la fotografía no coincide con un formato permitido."})
    try:
        from PIL import Image, UnidentifiedImageError
        with Image.open(BytesIO(content)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Formato de imagen no permitido")
            image.verify()
            if image.format != {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[expected_mime]:
                raise ValueError("La extensión no corresponde a la imagen")
    except ImportError as exc:
        raise HTTPException(500, detail={"code": "DEPENDENCY_NOT_CONFIGURED", "message": "La validación de fotografías no está disponible; instala las dependencias del backend."}) from exc
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": "El archivo no es una imagen válida del formato indicado."}) from exc

    filename = f"{uuid4().hex}{suffix}"
    ROLE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temporary = ROLE_UPLOAD_DIR / f".{filename}.tmp"
    destination = ROLE_UPLOAD_DIR / filename
    try:
        temporary.write_bytes(content)
        temporary.replace(destination)
        workshop = Workshop(name=name.strip(), rfc=clean_rfc, contact_email=str(contact_email).strip().lower(),
                            street=street.strip(), number=number.strip(), postal_code=postal_code,
                            state=state_name.strip(), municipality=municipality.strip(), neighborhood=neighborhood.strip(),
                            photo_filename=filename, id_estatus=1)
        db.add(workshop); db.flush()
        db.add(AuditLog(user_id=actor.id, action="workshop.created", detail=f"workshop_id={workshop.id}"))
        db.commit(); db.refresh(workshop)
    except IntegrityError as exc:
        db.rollback()
        destination.unlink(missing_ok=True); temporary.unlink(missing_ok=True)
        if "rfc" in str(getattr(exc, "orig", "")).lower():
            raise HTTPException(409, detail={"code": "DUPLICATE_RFC", "message": "Ya existe un taller registrado con ese RFC."}) from exc
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo registrar el taller."}) from exc
    except (OSError, SQLAlchemyError) as exc:
        db.rollback()
        destination.unlink(missing_ok=True); temporary.unlink(missing_ok=True)
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo guardar el taller y su fotografía."}) from exc
    return {"id": workshop.id, "name": workshop.name, "rfc": workshop.rfc, "id_estatus": workshop.id_estatus, "message": "Taller registrado correctamente."}
