"""Hash BCrypt y JWT de corta duración con identidad y rol."""
from datetime import datetime, timedelta, timezone
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


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Token inválido o expirado") from exc
