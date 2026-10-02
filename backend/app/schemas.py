"""Esquemas de entrada/salida: validación duplicada en la frontera API."""
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PASSWORD_RULE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d\s])\S{12,72}$")


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2 or not re.fullmatch(r"[\wÀ-ÿ .'-]+", value):
            raise ValueError("Ingresa un nombre válido.")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72 or not PASSWORD_RULE.fullmatch(value):
            raise ValueError("Usa 12–72 caracteres con mayúscula, minúscula, número y símbolo, sin espacios.")
        return value

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if value and not re.fullmatch(r"[+\d() -]{7,20}", value):
                raise ValueError("Ingresa un teléfono válido.")
        return value or None


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=12, max_length=72)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72 or not PASSWORD_RULE.fullmatch(value):
            raise ValueError("Usa 12–72 caracteres con mayúscula, minúscula, número y símbolo, sin espacios.")
        return value


class StaffUserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    role: str = Field(pattern=r"^(administrador|recepcionista|asesor_servicio|tecnico)$")

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2 or not re.fullmatch(r"[\wÀ-ÿ .'-]+", value):
            raise ValueError("Ingresa un nombre válido.")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72 or not PASSWORD_RULE.fullmatch(value):
            raise ValueError("Usa 12–72 caracteres con mayúscula, minúscula, número y símbolo, sin espacios.")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    role: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
