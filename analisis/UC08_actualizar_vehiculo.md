# UC-08 — Actualizar vehículo

**Versión de la documentación:** 1.0.0 · **Revisada:** 2026-11-05

## Objetivo y alcance

Editar desde un modal independiente los datos principales de un vehículo mostrado en [UC-07 — Consultar vehículo](UC07_consultar_vehiculo.md). El VIN se muestra para identificación y es inmutable. No se editan el cliente asociado, el estatus ni la fotografía.

## Actores y control de acceso

- Administrador y Recepcionista con sesión activa.
- La interfaz muestra la acción de edición solo para esos roles.
- `PUT /api/v1/vehicles/{vehicle_id}` vuelve a validar los roles mediante `require_roles`; una petición directa no autorizada recibe `403`.

## Flujo

1. Abrir la administración de vehículos y elegir **Editar** en una tarjeta.
2. Abrir un modal independiente precargado con el VIN, la placa, marca, modelo, año, versión, color y kilometraje del vehículo, además del cliente asociado como contexto.
3. Mostrar el VIN como `readonly`; no incluirlo en el cuerpo de actualización.
4. Validar que placa, marca, modelo, año, versión, color y kilometraje contengan valores válidos antes de enviar.
5. Enviar los campos editables mediante `PUT /api/v1/vehicles/{vehicle_id}`.
6. El backend valida el esquema, actualiza únicamente esos campos en una transacción y conserva VIN, cliente, estatus y fotografía.
7. Si la placa ya pertenece a otro vehículo, responder `409`; si el ID no existe, responder `404`.
8. Ante éxito, cerrar el modal, informar al usuario y recargar los resultados respetando el filtro actual.

## Campos y reglas

| Campo | Regla |
|---|---|
| VIN | Solo lectura en la UI y excluido del esquema `VehicleUpdateIn`. Un campo `vin` adicional enviado por el cliente no forma parte de `model_dump()` ni se asigna al modelo. |
| Placa | Obligatoria; se recorta, pasa a mayúsculas y valida con el patrón configurado (2–12 caracteres alfanuméricos o guiones). La restricción UNIQUE existente evita duplicados. |
| Marca, modelo, versión, color | Obligatorios, no vacíos tras recorte; se normalizan a minúsculas y respetan las longitudes del esquema. |
| Año | Entero entre 1886 y el año actual más uno. |
| Kilometraje | Entero no negativo. |
| Cliente, estatus, foto | No editables en este caso de uso; se conservan sus valores existentes. |

## Contrato API

```http
PUT /api/v1/vehicles/{vehicle_id}
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "plate": "ABC-123",
  "make": "honda",
  "model": "civic",
  "year": 2023,
  "version": "touring",
  "color": "azul",
  "mileage": 25000
}
```

La respuesta incluye el vehículo actualizado con el nombre del cliente y el estatus. Errores relevantes: `401` sin sesión, `403` por rol, `404` si el vehículo no existe, `409 DUPLICATE_VEHICLE` por placa duplicada y `422` ante datos incompletos o inválidos. No se requiere migración.

## Archivos y responsabilidades

- `backend/app/vehicle_registration.py`: esquema estricto de edición y transacción que asigna exclusivamente sus campos editables.
- `backend/app/main.py`: endpoint PUT protegido y respuesta enriquecida para la tarjeta de consulta.
- `frontend/src/views/VehicleListView.vue`: acción por tarjeta, modal independiente, precarga, validación y avisos.
- `frontend/src/api.ts`: contrato `VehicleUpdateData` y llamada `updateVehicle`.
- `frontend/src/style.css`: disposición responsiva de la acción de edición.
- `backend/tests/test_roles_and_workshops.py`: campos, normalización, VIN inmutable, relación/estatus, duplicidad, ID inexistente y roles.

## Verificación registrada

- Suite `backend/tests/test_roles_and_workshops.py`: **27 pruebas aprobadas**, incluyendo cuatro nuevas de UC-08.
- `npm run build`: correcto.
- Inspección manual en `/vehiculos`: el modal abre con datos precargados y el VIN no aparece editable. Se cerró con **Cancelar** para no modificar el registro real del usuario.
- La persistencia y respuestas se probaron en SQLite aislado; no se guardó una actualización en MySQL real durante esta verificación.
