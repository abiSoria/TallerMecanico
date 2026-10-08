"""Caso de uso UC-CV-01: registrar un cliente."""
import re
from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models import AuditLog, Client, User


class ClientRegistrationIn(BaseModel):
    full_name: str
    street: str
    number: str
    neighborhood: str
    municipality: str
    state: str
    primary_phone: str
    alternate_phone: str
    email: EmailStr
    confirm_duplicate: bool = False


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    street: str
    number: str
    neighborhood: str
    municipality: str
    state: str
    primary_phone: str
    alternate_phone: str
    email: EmailStr
    is_active: bool


class ClientRegistrationAuditOut(BaseModel):
    client_name: str
    registered_by: str
    registered_at: datetime


class ClientValidationStrategy(ABC):
    @abstractmethod
    def validate(self, client: ClientRegistrationIn) -> None: ...


class ContactFormatStrategy(ClientValidationStrategy):
    _phone = re.compile(r"^(?=(?:\D*\d){7,})[+0-9() -]{7,20}$")

    def validate(self, client: ClientRegistrationIn) -> None:
        required = (client.full_name, client.street, client.number, client.neighborhood,
                    client.municipality, client.state, client.primary_phone,
                    client.alternate_phone, str(client.email))
        if any(not value.strip() for value in required):
            raise HTTPException(422, detail={"code": "INVALID_DATA", "message": "Todos los datos obligatorios deben tener contenido."})
        if not self._phone.fullmatch(client.primary_phone.strip()):
            raise HTTPException(422, detail={"code": "INVALID_DATA", "message": "El teléfono principal no tiene un formato válido."})
        if not self._phone.fullmatch(client.alternate_phone.strip()):
            raise HTTPException(422, detail={"code": "INVALID_DATA", "message": "El teléfono alterno no tiene un formato válido."})


class ClientBuilder:
    def __init__(self):
        self._values: dict = {}

    def from_input(self, data: ClientRegistrationIn) -> "ClientBuilder":
        self._values = self.normalize(data)
        return self

    @staticmethod
    def normalize(data: ClientRegistrationIn) -> dict:
        return {
            "full_name": data.full_name.strip(), "street": data.street.strip(),
            "number": data.number.strip(), "neighborhood": data.neighborhood.strip(),
            "municipality": data.municipality.strip(), "state": data.state.strip(),
            "primary_phone": data.primary_phone.strip(),
            "alternate_phone": data.alternate_phone.strip(),
            "email": str(data.email).strip().lower(), "is_active": True,
        }

    def build(self) -> Client:
        return Client(**self._values)


class ClientRegistrationFacade:
    _roles = {"recepcionista", "administrador"}

    def __init__(self, validation: ClientValidationStrategy | None = None):
        self.validation = validation or ContactFormatStrategy()

    def register(self, db: Session, actor: User, data: ClientRegistrationIn) -> tuple[Client, bool]:
        if actor.role.name not in self._roles:
            raise HTTPException(403, detail={"code": "UNAUTHORIZED", "message": "El rol no está autorizado para registrar clientes."})

        self.validation.validate(data)
        normalized = ClientBuilder.normalize(data)
        try:
            possible = db.query(Client).filter(
                or_(
                    Client.email == normalized["email"],
                    Client.primary_phone.in_([normalized["primary_phone"], normalized["alternate_phone"]]),
                    Client.alternate_phone.in_([normalized["primary_phone"], normalized["alternate_phone"]]),
                    and_(
                        Client.full_name == normalized["full_name"],
                        Client.street == normalized["street"],
                        Client.number == normalized["number"],
                        Client.neighborhood == normalized["neighborhood"],
                        Client.municipality == normalized["municipality"],
                        Client.state == normalized["state"],
                    ),
                )
            ).first()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(500, detail={
                "code": "PERSISTENCE_ERROR",
                "message": "No fue posible comprobar los datos del cliente. Contacta al administrador del sistema.",
            }) from exc
        if possible and not data.confirm_duplicate:
            raise HTTPException(409, detail={
                "code": "POSSIBLE_DUPLICATE",
                "message": "Posible cliente duplicado detectado. Confirme para continuar.",
                "possible_client_id": possible.id,
            })

        client = ClientBuilder().from_input(data).build()
        try:
            db.add(client)
            db.flush()
            db.add(AuditLog(user_id=actor.id, action="client.registered", detail=f"client_id={client.id}"))
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(500, detail={"code": "PERSISTENCE_ERROR", "message": "No fue posible registrar el cliente."}) from exc
        return client, bool(possible)
