# UC-07 — Consultar vehículo

**Versión de la documentación:** 1.2.0 · **Revisada:** 2026-11-10

## Objetivo y alcance

Consultar los vehículos registrados desde la vista de administración. El usuario puede buscar por VIN, placa o ID, ver los datos asociados y distinguir los vehículos activos de los inactivos. Una búsqueda usa coincidencia exacta del identificador después de normalizar espacios, guiones y mayúsculas; no realiza búsqueda parcial. Administrador y Recepcionista pueden abrir el modal de detalle para activar o desactivar el vehículo según [UC-09](UC09_gestionar_estado_vehiculo.md), y el modal independiente de actualización descrito en [UC-08](UC08_actualizar_vehiculo.md).

## Actores y permisos

- Administrador y Recepcionista con sesión activa.
- El endpoint vuelve a validar los roles en backend. La protección del router frontend solo mejora la navegación y no sustituye esta autorización.
- Los vehículos de ambos estatus se pueden consultar.

## Flujo

1. Abrir **Vehículos registrados** desde el panel.
2. La vista carga los vehículos junto con el nombre del cliente y la descripción del estatus.
3. Para filtrar, ingresar VIN, placa o ID y enviar la búsqueda.
4. El frontend recorta espacios exteriores y envía `search` al endpoint existente.
5. El backend normaliza la entrada y compara VIN y placa sin distinguir mayúsculas, espacios o guiones. Si la entrada es decimal, también compara el ID entero.
6. La interfaz muestra las coincidencias exactas con los datos del vehículo y su estatus; si la lista está vacía, muestra “No se encontraron vehículos”.
7. Limpiar la búsqueda vuelve a mostrar todos los vehículos, activos e inactivos.
8. Seleccionar **Ver vehículo** abre el modal de detalle. Administrador y Recepcionista pueden solicitar el cambio de estado; la vista exige confirmación antes de enviar la operación a la API.
9. Administrador o Recepcionista selecciona **Editar** para abrir el modal de UC-08 con los datos del vehículo seleccionado.

## Normalización y coincidencia

La API quita espacios al inicio/final y elimina espacios y guiones ASCII antes de convertir VIN/placa a mayúsculas. La comparación aplica la misma transformación a los valores almacenados, por lo que también tolera formato heredado con espacios o minúsculas. Para ID, se recortan los extremos y se acepta solo una entrada decimal que pueda convertirse a entero.

La comparación es exacta sobre el identificador normalizado. Una coincidencia parcial no se devuelve como resultado. El endpoint devuelve `[]` cuando no hay coincidencias; una entrada compuesta únicamente por separadores tampoco provoca que se liste todo.

## Contrato y datos mostrados

| Elemento | Contrato |
|---|---|
| Consulta | `GET /api/v1/vehicles?search={VIN\|placa\|ID}`; `search` es opcional y admite hasta 64 caracteres. |
| Acceso | Bearer JWT; roles `administrador` o `recepcionista`. Sin sesión: `401`; rol no permitido: `403`. |
| Sin filtro | Lista completa ordenada por ID descendente, incluyendo ambos estatus. |
| Con filtro | Lista de coincidencias exactas; puede contener más de una fila si un valor coincide entre la columna VIN de un vehículo y la placa de otro. |
| Sin coincidencia | `200` con arreglo vacío. |
| Campos | ID, cliente, VIN, placa, marca, modelo, año, versión, color, kilometraje, estatus, bandera de actividad y referencia de foto. |
| Fotografía | `GET /api/v1/vehicles/{vehicle_id}/photo`, protegido con los mismos roles. |

## Archivos y responsabilidades

- `backend/app/main.py`: endpoint protegido, parámetro de búsqueda, consulta y respuesta tipada.
- `backend/app/vehicle_registration.py`: normalización compartida de VIN/placa y expresión SQL para comparar valores existentes.
- `frontend/src/api.ts`: serializa el parámetro `search` en el cliente API.
- `frontend/src/views/VehicleListView.vue`: formulario, estados de carga/error/vacío, resultados y limpieza de fotos temporales.
- `frontend/src/style.css`: disposición adaptable del campo de búsqueda.
- `backend/tests/test_roles_and_workshops.py`: pruebas de normalización, ID, estatus, cero resultados y guardia de permisos.

## Persistencia e índices

No se requiere alterar tablas ni agregar una migración para esta consulta. Las restricciones únicas existentes de VIN y placa se conservan. La búsqueda normalizada aplica funciones sobre esas columnas, por lo que una tabla grande podría requerir columnas canónicas indexadas o índices funcionales compatibles con el motor; no se añade ese costo sin evidencia de volumen o lentitud.

## Verificación de esta implementación

- La suite `backend/tests/test_roles_and_workshops.py` pasó con **23 pruebas**; tres cubren la búsqueda y su autorización.
- `npm run build` completó correctamente.
- La consulta se probó con SQLite en memoria, incluyendo registros activos e inactivos. No se ejecutó una consulta contra MySQL real ni una prueba de navegador punta a punta en esta verificación.
