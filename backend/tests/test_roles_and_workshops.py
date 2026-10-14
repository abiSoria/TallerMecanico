"""Pruebas de reglas API/servicios con SQLite en memoria; sin MySQL ni red."""
import importlib.util
import unittest
from pathlib import Path
import tempfile

from fastapi import HTTPException
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, joinedload, sessionmaker
from sqlalchemy.pool import StaticPool

from app import administration, main
from app.administration import RoleIn
from app.auth import current_user, require_roles
from app.database import Base
from app.models import Client, Role, Status, User, Vehicle, Workshop
from app.client_registration import ClientRegistrationIn, ClientUpdateIn, ClientWorkshopIn
from app.schemas import StaffUserCreate
from app.security import create_access_token
from app.vehicle_registration import VehicleCreateIn, register_vehicle
import app.vehicle_registration as vehicle_registration


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

    def client(self, email="cliente@example.com", workshop_id=None):
        client = Client(
            full_name="Cliente Prueba", street="Hidalgo", number="25", neighborhood="Centro",
            municipality="Jilotepec", state="Estado de México", primary_phone="5551234567",
            alternate_phone="5557654321", email=email, id_estatus=1, workshop_id=workshop_id,
        )
        self.db.add(client); self.db.commit()
        return client

    def workshop(self, status=1):
        workshop = Workshop(
            name="Taller Activo" if status == 1 else "Taller Suspendido", rfc="ABC123456AB1" if status == 1 else "XYZ123456AB1",
            contact_email="taller@example.com", street="Hidalgo", number="25", postal_code="06000",
            state="Ciudad de México", municipality="Cuauhtémoc", neighborhood="Centro",
            photo_filename="foto.jpg", id_estatus=status,
        )
        self.db.add(workshop); self.db.commit()
        return workshop

    def client_fields(self, **overrides):
        data = {
            "full_name": "Cliente Editado", "street": "Reforma", "number": "8",
            "neighborhood": "Centro", "municipality": "Jilotepec", "state": "Estado de México",
            "primary_phone": "5551234567", "alternate_phone": "5557654321", "email": "nuevo@example.com",
        }
        data.update(overrides)
        return data

    def test_client_registration_allows_only_receptionist_and_admin_roles(self):
        payload = ClientRegistrationIn(**self.client_fields())
        with self.assertRaises(HTTPException) as rejected:
            main.register_client(payload, self.db, self.suspended_user)
        self.assertEqual(rejected.exception.status_code, 403)
        client, _ = main.client_registration.register(self.db, self.receptionist, payload)
        self.assertEqual(client.full_name, "Cliente Editado")

    def test_registration_and_association_reject_inactive_workshops(self):
        inactive = self.workshop(status=2)
        with self.assertRaises(HTTPException) as registration_error:
            main.client_registration.register(
                self.db, self.receptionist,
                ClientRegistrationIn(**self.client_fields(workshop_id=inactive.id)),
            )
        self.assertEqual(registration_error.exception.status_code, 422)
        client = self.client()
        with self.assertRaises(HTTPException) as association_error:
            main.associate_client_workshop(client.id, ClientWorkshopIn(workshop_id=inactive.id), self.db, self.receptionist)
        self.assertEqual(association_error.exception.status_code, 409)
        self.assertIsNone(self.db.query(Client).filter_by(id=client.id).one().workshop_id)

    def test_association_rejects_inactive_or_missing_client_and_missing_workshop(self):
        workshop = self.workshop()
        inactive_client = self.client()
        inactive_client.id_estatus = 2
        self.db.commit()
        with self.assertRaises(HTTPException) as inactive_error:
            main.associate_client_workshop(
                inactive_client.id, ClientWorkshopIn(workshop_id=workshop.id), self.db, self.receptionist,
            )
        self.assertEqual(inactive_error.exception.status_code, 409)
        self.assertIsNone(self.db.query(Client).filter_by(id=inactive_client.id).one().workshop_id)

        with self.assertRaises(HTTPException) as missing_client_error:
            main.associate_client_workshop(9999, ClientWorkshopIn(workshop_id=workshop.id), self.db, self.admin)
        self.assertEqual(missing_client_error.exception.status_code, 404)

        active_client = self.client(email="otro-cliente@example.com")
        with self.assertRaises(HTTPException) as missing_workshop_error:
            main.associate_client_workshop(active_client.id, ClientWorkshopIn(workshop_id=9999), self.db, self.admin)
        self.assertEqual(missing_workshop_error.exception.status_code, 404)
        self.assertIsNone(self.db.query(Client).filter_by(id=active_client.id).one().workshop_id)

    def test_client_edit_cannot_change_workshop_and_soft_delete_preserves_relations(self):
        workshop = self.workshop()
        client = self.client(workshop_id=workshop.id)
        vehicle = Vehicle(client_id=client.id, plate="ABC123", make="Marca", model="Modelo", year=2020)
        self.db.add(vehicle); self.db.commit()

        updated = main.update_client(client.id, ClientUpdateIn(**self.client_fields()), self.db, self.receptionist)
        saved = self.db.query(Client).filter_by(id=client.id).one()
        self.assertEqual(updated.workshop_id, workshop.id)
        self.assertEqual(saved.workshop_id, workshop.id)
        self.assertEqual(saved.full_name, "Cliente Editado")

        result = main.deactivate_client(client.id, self.db, self.admin)
        self.db.expire_all()
        saved = self.db.query(Client).filter_by(id=client.id).one()
        self.assertIn("desactivado", result["message"])
        self.assertEqual(saved.id_estatus, 2)
        self.assertEqual(saved.workshop_id, workshop.id)
        self.assertIsNotNone(self.db.query(Vehicle).filter_by(client_id=client.id).first())

    def test_client_list_and_association_keep_workshop_data_out_of_edit_contract(self):
        workshop = self.workshop()
        client = self.client()
        result = main.associate_client_workshop(client.id, ClientWorkshopIn(workshop_id=workshop.id), self.db, self.receptionist)
        self.assertEqual(result.workshop_name, workshop.name)
        rows = main.list_clients(self.db, self.admin)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].workshop_id, workshop.id)
        self.assertNotIn("workshop_id", ClientUpdateIn.model_fields)

    def test_existing_duplicate_detection_remains_active(self):
        self.client()
        payload = ClientRegistrationIn(**self.client_fields(email="cliente@example.com"))
        with self.assertRaises(HTTPException) as duplicate:
            main.client_registration.register(self.db, self.receptionist, payload)
        self.assertEqual(duplicate.exception.status_code, 409)
        self.assertEqual(duplicate.exception.detail["code"], "POSSIBLE_DUPLICATE")

    def vehicle_fields(self, **overrides):
        data = {
            "vin": "1HGCM82633A004352", "plate": "ABC-123", "make": " Honda ",
            "model": " Civic ", "year": 2022, "version": " Touring ",
            "color": " Azul ", "mileage": 1000,
        }
        data.update(overrides)
        return data

    def test_vehicle_registration_persists_normalized_vehicle_for_active_client(self):
        client = self.client()
        payload = VehicleCreateIn(**self.vehicle_fields())
        vehicle = run_immediate(register_vehicle(self.db, self.receptionist, client.id, payload))
        self.db.refresh(vehicle)
        self.assertEqual(vehicle.client_id, client.id)
        self.assertEqual(vehicle.id_estatus, 1)
        self.assertEqual((vehicle.vin, vehicle.plate), ("1HGCM82633A004352", "ABC-123"))
        self.assertEqual((vehicle.make, vehicle.model, vehicle.version, vehicle.color), ("honda", "civic", "touring", "azul"))
        self.assertEqual((vehicle.year, vehicle.mileage), (2022, 1000))

    def test_vehicle_registration_rejects_unauthorized_or_inactive_client(self):
        client = self.client()
        payload = VehicleCreateIn(**self.vehicle_fields())
        with self.assertRaises(HTTPException) as unauthorized:
            run_immediate(register_vehicle(self.db, self.suspended_user, client.id, payload))
        self.assertEqual(unauthorized.exception.status_code, 403)
        client.id_estatus = 2; self.db.commit()
        with self.assertRaises(HTTPException) as inactive:
            run_immediate(register_vehicle(self.db, self.receptionist, client.id, payload))
        self.assertEqual(inactive.exception.status_code, 409)
        self.assertEqual(self.db.query(Vehicle).count(), 0)

    def test_vehicle_registration_rejects_missing_client_invalid_data_and_duplicates(self):
        with self.assertRaises(ValidationError):
            VehicleCreateIn(**self.vehicle_fields(year=1800))
        with self.assertRaises(ValidationError):
            VehicleCreateIn(**self.vehicle_fields(mileage=-1))
        with self.assertRaises(HTTPException) as missing:
            run_immediate(register_vehicle(self.db, self.receptionist, 9999, VehicleCreateIn(**self.vehicle_fields())))
        self.assertEqual(missing.exception.status_code, 404)
        client = self.client()
        run_immediate(register_vehicle(self.db, self.receptionist, client.id, VehicleCreateIn(**self.vehicle_fields())))
        with self.assertRaises(HTTPException) as duplicate_vin:
            run_immediate(register_vehicle(self.db, self.receptionist, client.id, VehicleCreateIn(**self.vehicle_fields(plate="ZZZ-888"))))
        self.assertEqual(duplicate_vin.exception.status_code, 409)
        with self.assertRaises(HTTPException) as duplicate_plate:
            run_immediate(register_vehicle(self.db, self.receptionist, client.id, VehicleCreateIn(**self.vehicle_fields(vin="9BWZZZ377VT004251"))))
        self.assertEqual(duplicate_plate.exception.status_code, 409)
        self.assertEqual(self.db.query(Vehicle).count(), 1)

    def test_vehicle_photo_is_validated_and_saved_with_reference(self):
        old_upload_dir = vehicle_registration.VEHICLE_UPLOAD_DIR
        vehicle_registration.VEHICLE_UPLOAD_DIR = Path(self.temp_dir.name) / "vehicles"
        try:
            client = self.client()
            photo = self.valid_png()
            vehicle = run_immediate(register_vehicle(
                self.db, self.receptionist, client.id, VehicleCreateIn(**self.vehicle_fields()), photo,
            ))
            self.assertTrue(vehicle.photo_filename)
            self.assertTrue((vehicle_registration.VEHICLE_UPLOAD_DIR / vehicle.photo_filename).is_file())
            with self.assertRaises(HTTPException) as oversized:
                run_immediate(register_vehicle(
                    self.db, self.receptionist, client.id,
                    VehicleCreateIn(**self.vehicle_fields(vin="9BWZZZ377VT004251", plate="XYZ-999")),
                    self.photo(10 * 1024 * 1024 + 1),
                ))
            self.assertEqual(oversized.exception.status_code, 413)
            with self.assertRaises(HTTPException) as invalid:
                run_immediate(register_vehicle(
                    self.db, self.receptionist, client.id,
                    VehicleCreateIn(**self.vehicle_fields(vin="9BWZZZ377VT004251", plate="XYZ-999")),
                    FakeUpload(b"not an image", "foto.exe", "application/octet-stream"),
                ))
            self.assertEqual(invalid.exception.status_code, 422)
        finally:
            vehicle_registration.VEHICLE_UPLOAD_DIR = old_upload_dir

    def test_vehicle_storage_failure_rolls_back_database_registration(self):
        old_upload_dir = vehicle_registration.VEHICLE_UPLOAD_DIR
        blocked_path = Path(self.temp_dir.name) / "not-a-directory"
        blocked_path.write_text("block", encoding="utf-8")
        vehicle_registration.VEHICLE_UPLOAD_DIR = blocked_path
        try:
            client = self.client()
            with self.assertRaises(HTTPException) as storage_error:
                run_immediate(register_vehicle(
                    self.db, self.receptionist, client.id, VehicleCreateIn(**self.vehicle_fields()), self.valid_png(),
                ))
            self.assertEqual(storage_error.exception.status_code, 500)
            self.assertEqual(self.db.query(Vehicle).count(), 0)
        finally:
            vehicle_registration.VEHICLE_UPLOAD_DIR = old_upload_dir

    def valid_png(self, size=128):
        import struct
        import zlib
        from io import BytesIO
        from PIL import Image

        image_buffer = BytesIO()
        Image.new("RGB", (1, 1), color="white").save(image_buffer, format="PNG")
        png = image_buffer.getvalue()
        iend_offset = len(png) - 12
        chunk_type = b"tEXt"
        padding_size = size - len(png) - 12
        if padding_size < len(b"Comment\0"):
            raise ValueError("El tamaño solicitado es demasiado pequeño para el PNG de prueba.")
        chunk_data = b"Comment\0" + b"x" * (padding_size - len(b"Comment\0"))
        chunk = (
            struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data
            + struct.pack(">I", zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
        )
        content = png[:iend_offset] + chunk + png[iend_offset:]
        if len(content) != size:
            raise AssertionError("El PNG de prueba no tiene el tamaño solicitado.")
        Image.open(BytesIO(content)).verify()
        return FakeUpload(content, "foto.png", "image/png")

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
