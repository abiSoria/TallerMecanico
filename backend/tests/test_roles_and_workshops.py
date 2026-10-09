"""Pruebas de reglas API/servicios con SQLite en memoria; sin MySQL ni red."""
import importlib.util
import unittest
from pathlib import Path
import tempfile

from fastapi import HTTPException
from pydantic import TypeAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, joinedload, sessionmaker
from sqlalchemy.pool import StaticPool

from app import administration, main
from app.administration import RoleIn
from app.auth import current_user, require_roles
from app.database import Base
from app.models import Role, Status, User, Workshop
from app.schemas import StaffUserCreate
from app.security import create_access_token


def run_immediate(coroutine):
    """Ejecuta la ruta de prueba; FakeUpload.read no suspende ni usa I/O."""
    iterator = coroutine.__await__()
    try:
        yielded = iterator.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError(f"La corrutina requirió un event loop inesperado: {yielded!r}")


class FakeUpload:
    def __init__(self, content: bytes, filename: str, content_type: str):
        self.content = content
        self.filename = filename
        self.content_type = content_type

    async def read(self, size: int = -1) -> bytes:
        return self.content[:size] if size >= 0 else self.content


class RoleWorkshopApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db: Session = self.Session()
        self.db.add_all([
            Status(id_estatus=1, valor="Activo", descripcion="Rol habilitado para su uso"),
            Status(id_estatus=2, valor="Suspendido", descripcion="Rol deshabilitado para su uso"),
        ])
        self.admin_role = Role(code="administrador", name="Administrador", normalized_name="administrador", id_estatus=1)
        self.reception_role = Role(code="recepcionista", name="Recepcionista", normalized_name="recepcionista", id_estatus=1)
        self.suspended_role = Role(code="custom_off", name="Apagado", normalized_name="apagado", id_estatus=2)
        self.db.add_all([self.admin_role, self.reception_role, self.suspended_role]); self.db.flush()
        self.admin = User(role_id=self.admin_role.id, full_name="Admin", email="admin@example.com", password_hash="x", id_estatus=1)
        self.receptionist = User(role_id=self.reception_role.id, full_name="Recepción", email="reception@example.com", password_hash="x", id_estatus=1)
        self.suspended_user = User(role_id=self.suspended_role.id, full_name="Suspendido", email="suspended@example.com", password_hash="x", id_estatus=1)
        self.db.add_all([self.admin, self.receptionist, self.suspended_user]); self.db.commit()
        self.admin = self.db.query(User).options(joinedload(User.role)).filter_by(id=self.admin.id).one()
        self.receptionist = self.db.query(User).options(joinedload(User.role)).filter_by(id=self.receptionist.id).one()
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.old_upload_dir = administration.ROLE_UPLOAD_DIR
        administration.ROLE_UPLOAD_DIR = Path(self.temp_dir.name)

    def tearDown(self):
        administration.ROLE_UPLOAD_DIR = self.old_upload_dir
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    def workshop_payload(self, rfc="ABC123456AB1"):
        return {
            "name": "Taller Prueba", "rfc": rfc, "contact_email": TypeAdapter(administration.EmailStr).validate_python("contacto@example.com"),
            "street": "Hidalgo", "number": "25", "postal_code": "06000",
            "state_name": "Ciudad de México", "municipality": "Cuauhtémoc", "neighborhood": "Centro",
        }

    def photo(self, size=12):
        return FakeUpload(b"\xff\xd8\xff" + b"x" * (size - 3), "foto.jpg", "image/jpeg")

    def valid_png(self, size=70):
        import base64
        sample = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/X7sAAAAASUVORK5CYII=")
        return FakeUpload(sample + b"\x00" * max(0, size - len(sample)), "foto.png", "image/png")

    def test_role_name_duplicate_is_rejected_after_trim_and_casefold(self):
        first = administration.create_role(RoleIn(name="  Mecánico  ", description="Rol de prueba"), self.db, self.admin)
        with self.assertRaises(HTTPException) as error:
            administration.create_role(RoleIn(name="MECÁNICO", description="Otro"), self.db, self.admin)
        self.assertEqual(first["id_estatus"], 1)
        self.assertEqual(error.exception.status_code, 409)

    def test_non_admin_cannot_create_role(self):
        with self.assertRaises(HTTPException) as error:
            require_roles("administrador")(self.receptionist)
        self.assertEqual(error.exception.status_code, 403)

    def test_unapproved_role_cannot_create_workshop(self):
        with self.assertRaises(HTTPException) as error:
            require_roles("administrador", "recepcionista")(self.suspended_user)
        self.assertEqual(error.exception.status_code, 403)

    def test_suspended_role_cannot_be_assigned_to_staff_user(self):
        payload = StaffUserCreate(full_name="Cuenta Nueva", email="new@example.com", password="Password!123Abc", role_id=self.suspended_role.id)
        with self.assertRaises(HTTPException) as error:
            main.create_staff_user(payload, self.db, self.admin)
        self.assertEqual(error.exception.status_code, 422)
        self.assertIsNone(self.db.query(User).filter_by(email="new@example.com").first())

    def test_suspended_role_cannot_authenticate(self):
        token = create_access_token(self.suspended_user.id, self.suspended_role.code)
        with self.assertRaises(HTTPException) as error:
            current_user(token, self.db)
        self.assertEqual(error.exception.status_code, 401)

    def test_role_suspension_is_soft_and_repeat_is_reported(self):
        role = Role(code="custom_free", name="Temporal", normalized_name="temporal", id_estatus=1)
        self.db.add(role); self.db.commit()
        result = administration.suspend_role(role.id, self.db, self.admin)
        with self.assertRaises(HTTPException) as error:
            administration.suspend_role(role.id, self.db, self.admin)
        saved = self.db.query(Role).filter_by(id=role.id).one()
        self.assertEqual(result["code"], "ROLE_SUSPENDED")
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(saved.id_estatus, 2)

    def test_assigned_and_administrator_roles_cannot_be_suspended(self):
        for role_id in (self.reception_role.id, self.admin_role.id):
            with self.assertRaises(HTTPException) as error:
                administration.suspend_role(role_id, self.db, self.admin)
            self.assertEqual(error.exception.status_code, 409)

    def test_workshop_rfc_duplicate_and_ten_megabyte_image_limit(self):
        existing_data = self.workshop_payload()
        existing_data["state"] = existing_data.pop("state_name")
        existing = Workshop(**existing_data, photo_filename="already.jpg", id_estatus=1)
        self.db.add(existing); self.db.commit()
        with self.assertRaises(HTTPException) as duplicate:
            run_immediate(administration.create_workshop(**self.workshop_payload(), photo=self.photo(), db=self.db, actor=self.receptionist))
        self.assertEqual(duplicate.exception.status_code, 409)
        too_large = self.photo(10 * 1024 * 1024 + 1)
        with self.assertRaises(HTTPException) as oversized:
            run_immediate(administration.create_workshop(**self.workshop_payload("XYZ123456AB1"), photo=too_large, db=self.db, actor=self.receptionist))
        self.assertEqual(oversized.exception.status_code, 413)
        self.assertEqual(self.db.query(Workshop).count(), 1)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow no está instalado en el entorno local")
    def test_photo_exactly_ten_megabytes_is_accepted(self):
        maximum = 10 * 1024 * 1024
        response = run_immediate(administration.create_workshop(
            **self.workshop_payload(), photo=self.valid_png(maximum), db=self.db, actor=self.receptionist,
        ))
        self.assertEqual(response["id_estatus"], 1)
        row = self.db.query(Workshop).filter_by(id=response["id"]).one()
        self.assertEqual((Path(self.temp_dir.name) / row.photo_filename).stat().st_size, maximum)


if __name__ == "__main__":
    unittest.main()
