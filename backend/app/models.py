"""Modelos persistentes de identidad y operación del taller."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Status(Base):
    __tablename__ = "Estatus"
    id_estatus: Mapped[int] = mapped_column("IdEstatus", Integer, primary_key=True)
    valor: Mapped[str] = mapped_column("Valor", String(20), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column("Descripcion", String(120), nullable=False)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    id_estatus: Mapped[int] = mapped_column(ForeignKey("Estatus.IdEstatus"), default=1, nullable=False)
    status: Mapped[Status] = relationship()
    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    id_estatus: Mapped[int] = mapped_column(ForeignKey("Estatus.IdEstatus"), default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    role: Mapped[Role] = relationship(back_populates="users")

    @property
    def is_active(self) -> bool:
        return self.id_estatus == 1


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    street: Mapped[str] = mapped_column(Text, nullable=False)
    number: Mapped[str] = mapped_column(Text, nullable=False)
    neighborhood: Mapped[str] = mapped_column(Text, nullable=False)
    municipality: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    primary_phone: Mapped[str] = mapped_column(Text, nullable=False)
    alternate_phone: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    id_estatus: Mapped[int] = mapped_column(ForeignKey("Estatus.IdEstatus"), default=1, nullable=False)
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="client")

    @property
    def is_active(self) -> bool:
        return self.id_estatus == 1


class Workshop(Base):
    __tablename__ = "workshops"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    rfc: Mapped[str] = mapped_column(String(13), unique=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(254), nullable=False)
    street: Mapped[str] = mapped_column(String(160), nullable=False)
    number: Mapped[str] = mapped_column(String(30), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(5), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[str] = mapped_column(String(120), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(120), nullable=False)
    photo_filename: Mapped[str] = mapped_column(String(80), nullable=False)
    id_estatus: Mapped[int] = mapped_column(ForeignKey("Estatus.IdEstatus"), default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class PostalCode(Base):
    __tablename__ = "postal_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    postal_code: Mapped[str] = mapped_column(String(5), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(120), nullable=False)
    municipality: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (
        UniqueConstraint("postal_code", "neighborhood", "municipality", "state", name="uq_postal_location"),
        Index("idx_postal_code", "postal_code"),
        Index("idx_postal_reverse", "state", "municipality", "neighborhood"),
    )


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    plate: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    make: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer)
    client: Mapped[Client] = relationship(back_populates="vehicles")
    orders: Mapped[list["RepairOrder"]] = relationship(back_populates="vehicle")


class RepairOrder(Base):
    __tablename__ = "repair_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="recibido", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    vehicle: Mapped[Vehicle] = relationship(back_populates="orders")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
