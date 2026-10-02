"""Configuración centralizada: los secretos siempre llegan desde el entorno."""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Taller Mecánico API"
    api_prefix: str = "/api/v1"
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("jwt_secret_key")
    @classmethod
    def require_strong_secret(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32 or value.startswith("REEMPLAZA_"):
            raise ValueError("JWT_SECRET_KEY debe ser un secreto aleatorio de al menos 32 bytes")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
