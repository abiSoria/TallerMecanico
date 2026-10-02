"""Modelos de identidad y taller; roles se asignan explícitamente."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    role: Mapped[Role] = relationship(back_populates="users")
    client: Mapped["Client | None"] = relationship(back_populates="user", uselist=False)


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    user: Mapped[User | None] = relationship(back_populates="client")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="client")


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
