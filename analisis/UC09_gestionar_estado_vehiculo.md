# UC-CV-09 — Activar o desactivar vehículo

**Versión de la documentación:** 1.0.0 · **Revisada:** 2026-11-10

## Objetivo y alcance

Permitir que personal autorizado desactive o reactive un vehículo desde el modal **Ver vehículo**. La operación conserva el registro, su fotografía, sus relaciones y sus órdenes; representa la baja lógica mediante el estatus existente de `vehicles.id_estatus`.

## Actores y permisos

- Administrador y Recepcionista con sesión activa.
- El frontend muestra el control de cambio de estado solo a esos roles.
- El endpoint vuelve a aplicar `require_roles("administrador", "recepcionista")`. Ocultar el control no sustituye la autorización del servidor.
- Sin sesión, la API responde `401`; otro rol autenticado recibe `403`.

## Flujo principal

1. En **Vehículos registrados**, seleccionar **Ver vehículo**.
2. El modal muestra los datos del vehículo y un chip verde **Activo** o rojo **Inactivo**.
3. Seleccionar **Desactivar vehículo** o **Activar vehículo**.
4. La interfaz muestra una confirmación explícita con la acción y placa del vehículo. Cancelar cierra la confirmación sin enviar cambios.
5. Al confirmar, el frontend envía `PUT /api/v1/vehicles/{vehicle_id}/status` con `{"is_active": false}` para desactivar o `true` para reactivar.
6. La API valida sesión y rol, actualiza `id_estatus` a `2` (inactivo) o `1` (activo), registra la acción en `audit_logs` y devuelve la ficha actualizada.
7. El modal y la lista actualizan el texto y color del estado sin recargar la página.

## Contrato API

| Elemento | Contrato |
|---|---|
| Operación | `PUT /api/v1/vehicles/{vehicle_id}/status` |
| Entrada | `{ "is_active": boolean }` |
| Respuesta | `VehicleListOut` actualizado, con `status` igual a `Activo` o `Inactivo` |
| Permisos | Bearer JWT; roles `administrador` o `recepcionista` |
| Errores | `401` sesión inválida; `403` rol no autorizado; `404` vehículo inexistente; `422` entrada inválida; `500` error de persistencia |
| Repetición | Solicitar el estatus ya vigente no crea una segunda entrada de auditoría |

## Persistencia y auditoría

No se ejecuta `DELETE` ni se requiere una migración: `vehicles.id_estatus` y la tabla `Estatus` ya existen. Se preserva `id=1` como **Activo** y `id=2` como **Inactivo** en el contrato del vehículo. La acción que cambia el estado se registra como `vehicle.activated` o `vehicle.deactivated`, junto con el ID y la placa.

## Componentes

- `backend/app/vehicle_registration.py`: contrato de entrada, actualización transaccional de estatus y auditoría.
- `backend/app/main.py`: endpoint protegido y respuesta de la ficha.
- `frontend/src/api.ts`: contrato del cliente HTTP.
- `frontend/src/views/VehicleListView.vue`: modal de detalle, control, confirmación y actualización visual.
- `database/init.sql`: modelo existente de `vehicles.id_estatus`, clave foránea y estatus base.

