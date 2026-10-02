"""Crea de forma interactiva el primer administrador; no deja credenciales por defecto."""
from getpass import getpass
from app.database import SessionLocal
from app.models import AuditLog, Role, User
from app.schemas import StaffUserCreate
from app.security import hash_password


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(User).join(Role).filter(Role.name == "administrador").first():
            raise SystemExit("Ya existe una cuenta administradora; el asistente de primer acceso se cerró.")
        print("Alta privada del primer administrador del taller")
        full_name = input("Nombre completo: ").strip()
        email = input("Correo: ").strip()
        password = getpass("Contraseña (12+ caracteres, mayúscula, minúscula, número y símbolo): ")
        validated = StaffUserCreate(full_name=full_name, email=email, password=password, role="administrador")
        admin_role = db.query(Role).filter(Role.name == "administrador").one_or_none()
        if not admin_role:
            raise SystemExit("No existen los roles. Ejecuta primero database/init.sql.")
        account = User(role_id=admin_role.id, full_name=validated.full_name, email=str(validated.email).lower(), password_hash=hash_password(validated.password))
        db.add(account)
        db.flush()
        db.add(AuditLog(user_id=account.id, action="admin.bootstrap", detail="Primer administrador creado por consola"))
        db.commit()
        db.refresh(account)
        print(f"Administrador creado: {account.email}. Ya puedes iniciar sesión en el portal.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
