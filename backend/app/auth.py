"""Dependencias para sesión Bearer y control de acceso basado en roles."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from app.config import settings
from app.database import get_db
from app.models import Role, User
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o expirada", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise unauthorized
    user = db.query(User).options(joinedload(User.role)).filter(
        User.id == user_id, User.id_estatus == 1, User.role.has(Role.id_estatus == 1)
    ).first()
    if not user:
        raise unauthorized
    return user


def require_roles(*roles: str):
    def guard(user: User = Depends(current_user)) -> User:
        if user.role.code not in roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para esta operación")
        return user
    return guard
