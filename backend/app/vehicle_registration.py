"""Caso de uso 6: registrar vehículo asociado a un cliente activo."""
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.administration import IMAGE_TYPES, MAX_PHOTO_BYTES
from app.config import settings
from app.models import Client, User, Vehicle

VEHICLE_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "vehicles"
VIN_PATTERN = re.compile(settings.vehicle_vin_pattern)
PLATE_PATTERN = re.compile(settings.vehicle_plate_pattern)
MAX_YEAR = date.today().year + 1


class VehicleCreateIn(BaseModel):
    vin: str = Field(min_length=5, max_length=32)
    plate: str = Field(min_length=2, max_length=12)
    make: str = Field(min_length=1, max_length=60)
    model: str = Field(min_length=1, max_length=60)
    year: int = Field(ge=1886, le=MAX_YEAR)
    version: str = Field(min_length=1, max_length=80)
    color: str = Field(min_length=1, max_length=40)
    mileage: int = Field(ge=0)

    @field_validator("vin")
    @classmethod
    def validate_vin(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not VIN_PATTERN.fullmatch(normalized):
            raise ValueError("El VIN no cumple el formato configurado para este proyecto.")
        return normalized

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not PLATE_PATTERN.fullmatch(normalized):
            raise ValueError("La placa debe contener de 2 a 12 letras, números o guiones.")
        return normalized

    @field_validator("make", "model", "version", "color")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Este dato es obligatorio.")
        return normalized


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    vin: str | None
    plate: str
    make: str
    model: str
    year: int | None
    version: str | None
    color: str | None
    mileage: int | None
    photo_filename: str | None
    id_estatus: int
    is_active: bool


async def read_vehicle_photo(photo: UploadFile | None) -> tuple[bytes | None, str | None]:
    if photo is None or not photo.filename:
        return None, None
    suffix = Path(photo.filename).suffix.lower()
    image_spec = IMAGE_TYPES.get(suffix)
    if image_spec is None:
        raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": "La fotografía debe ser JPG, JPEG, PNG o WebP."})
    content = await photo.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(413, detail={"code": "IMAGE_TOO_LARGE", "message": "La fotografía no puede superar 10 MiB."})
    expected_mime, signature_check = image_spec
    if not signature_check(content) or photo.content_type not in (expected_mime, "application/octet-stream"):
        raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": "El contenido de la fotografía no coincide con un formato permitido."})
    try:
        from PIL import Image, UnidentifiedImageError
        with Image.open(BytesIO(content)) as image:
            expected_format = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[expected_mime]
            if image.format != expected_format:
                raise ValueError("La extensión no corresponde con el formato real.")
            image.verify()
    except ImportError as exc:
        raise HTTPException(500, detail={"code": "DEPENDENCY_NOT_CONFIGURED", "message": "La validación de fotografías no está disponible."}) from exc
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, detail={"code": "INVALID_IMAGE", "message": "El archivo no es una imagen válida del formato indicado."}) from exc
    return content, suffix


async def register_vehicle(
    db: Session,
    actor: User,
    client_id: int,
    data: VehicleCreateIn,
    photo: UploadFile | None = None,
) -> Vehicle:
    if actor.role.code not in {"administrador", "recepcionista"}:
        raise HTTPException(403, detail={"code": "UNAUTHORIZED", "message": "No tienes permiso para registrar vehículos."})
    content, suffix = await read_vehicle_photo(photo)
    destination: Path | None = None
    temporary: Path | None = None
    committed = False
    try:
        client = db.query(Client).filter(Client.id == client_id).with_for_update().first()
        if client is None:
            raise HTTPException(404, detail={"code": "CLIENT_NOT_FOUND", "message": "No se encontró el cliente seleccionado."})
        if client.id_estatus != 1:
            raise HTTPException(409, detail={"code": "CLIENT_INACTIVE", "message": "No se pueden registrar vehículos para un cliente inactivo."})
        duplicate = db.query(Vehicle.id).filter((Vehicle.vin == data.vin) | (Vehicle.plate == data.plate)).first()
        if duplicate:
            raise HTTPException(409, detail={"code": "DUPLICATE_VEHICLE", "message": "Ya existe un vehículo registrado con ese VIN o placa."})

        filename = f"{uuid4().hex}{suffix}" if content is not None and suffix is not None else None
        vehicle = Vehicle(
            client_id=client.id, vin=data.vin, plate=data.plate, make=data.make, model=data.model,
            year=data.year, version=data.version, color=data.color, mileage=data.mileage,
            photo_filename=filename, id_estatus=1,
        )
        db.add(vehicle)
        db.flush()
        destination = VEHICLE_UPLOAD_DIR / filename if filename else None
        temporary = VEHICLE_UPLOAD_DIR / f".{filename}.tmp" if filename else None
        if content is not None and destination is not None and temporary is not None:
            VEHICLE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            temporary.write_bytes(content)
            temporary.replace(destination)
        db.commit()
        committed = True
        db.refresh(vehicle)
        return vehicle
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        if "vehicle" in str(getattr(exc, "orig", "")).lower() or "vin" in str(getattr(exc, "orig", "")).lower() or "plate" in str(getattr(exc, "orig", "")).lower():
            raise HTTPException(409, detail={"code": "DUPLICATE_VEHICLE", "message": "Ya existe un vehículo registrado con ese VIN o placa."}) from exc
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo registrar el vehículo."}) from exc
    except (OSError, SQLAlchemyError) as exc:
        db.rollback()
        raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No se pudo guardar el vehículo y su fotografía."}) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if destination is not None and not committed:
            destination.unlink(missing_ok=True)
