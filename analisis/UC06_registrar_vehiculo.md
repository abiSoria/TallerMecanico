# UC-06 — Registrar vehículo

## Objetivo y alcance

Registrar un vehículo desde la fila de un cliente activo, guardarlo relacionado con ese cliente y con estatus Activo. Incluye validación de entrada, permisos, control de VIN/placa duplicados, fotografía opcional y persistencia. No incluye órdenes de reparación ni otras operaciones sobre vehículos.

La implementación de la funcionalidad ya estaba presente en el árbol de trabajo antes de este registro. En esta tarea se inspeccionó y verificó esa implementación; no se modificaron archivos de aplicación ni se añadió otro endpoint. Los cambios de esta entrega son esta documentación y los diagramas específicos de UC-06.

## Actores y precondiciones

- **Actores autorizados:** Administrador y Recepcionista autenticados.
- El cliente seleccionado existe y su `id_estatus` es `1` (Activo).
- El formulario incluye VIN, placa, marca, modelo, año, versión, color y kilometraje. La fotografía es opcional.
- El esquema de la migración `005_vehicle_registration.sql` está instalado.

El frontend limita la acción a clientes activos y a los roles que ven el módulo. El backend vuelve a comprobar autenticación y rol. El servicio bloquea y comprueba el cliente dentro de la operación; no confía en el estado enviado por el navegador.

## Flujo principal

1. En Administración de clientes, seleccionar **Asociar vehículo** en la fila de un cliente activo.
2. El modal muestra el nombre del cliente seleccionado y los campos del vehículo; el `client_id` no puede elegirse en el formulario.
3. Capturar los campos requeridos y, si se desea, una fotografía.
4. El frontend valida campos y archivo y evita un segundo envío mientras la primera solicitud está en curso.
5. Enviar `multipart/form-data` a `POST /api/v1/clients/{client_id}/vehicles`.
6. El backend autentica y autoriza; valida y normaliza datos e imagen, vuelve a comprobar que el cliente exista y esté activo, y busca duplicados por VIN o placa.
7. Crear el vehículo con el `client_id` de la ruta y `id_estatus = 1`; ejecutar `flush`, guardar la imagen con un nombre UUID si existe y confirmar la transacción.
8. Responder `201`; el frontend presenta éxito, cierra el modal y actualiza la tabla.

## Flujos alternativos y errores

- Sin sesión: `401`. Rol no permitido: `403`; no se persiste el vehículo.
- Cliente inexistente: `404`. Cliente inactivo: `409`; el guardado se cancela.
- Campos no válidos: `422`. VIN o placa ya registrados: `409 DUPLICATE_VEHICLE`.
- Imagen con extensión, MIME o contenido inválido: `422`; mayor de 10 MiB: `413`.
- Falla al escribir el archivo o guardar en base de datos: `500`; se revierte la sesión y se retira el archivo no confirmado.
- La restricción única de base de datos también resuelve carreras: placa tiene índice único y VIN tiene `uq_vehicles_vin`.

## Campos y validaciones

| Campo | Restricción comprobada |
|---|---|
| VIN | Obligatorio, 5–32 caracteres; patrón configurable por `VEHICLE_VIN_PATTERN`; se recorta y pasa a mayúsculas. |
| Placa | Obligatoria, 2–12 letras/números/guiones según patrón del proyecto; recorte y mayúsculas. |
| Marca, modelo, versión, color | Obligatorios, longitudes limitadas por el esquema; se recortan y normalizan a minúsculas. |
| Año | Entero entre 1886 y el año actual más uno. |
| Kilometraje | Entero no negativo. |
| Fotografía | Opcional; JPG/JPEG, PNG o WebP; máximo 10 MiB. Valida extensión, MIME, firma y formato/contenido real. Nombre de almacenamiento UUID. |
| Cliente | Identificador de la fila seleccionada; debe existir y tener `id_estatus = 1`. |
| Permisos | Administrador o Recepcionista; validación backend obligatoria. |

## Persistencia y relaciones verificadas

La tabla existente `vehicles` conserva la relación `client_id → clients.id` y agrega los atributos de UC-06 mediante `database/migrations/005_vehicle_registration.sql`: `vin`, `version`, `color`, `mileage`, `photo_filename` e `id_estatus`. El estatus referencia `Estatus.IdEstatus`; el alta usa el valor `1` (Activo). En el esquema MySQL consultado se verificaron las claves foráneas `client_id → clients.id` y `id_estatus → estatus.IdEstatus`, así como las restricciones únicas `plate` y `uq_vehicles_vin`.

La foto se guarda en `backend/uploads/vehicles/` y se conserva su nombre seguro en `vehicles.photo_filename`. El registro del vehículo y su asociación se confirman en la misma transacción; la escritura del archivo se compensa si falla la confirmación.

## Archivos existentes inspeccionados

| Archivo | Responsabilidad dentro de UC-06 |
|---|---|
| `frontend/src/views/ClientManagementView.vue` | Acción por cliente activo, modal, datos del cliente seleccionado, validación y bloqueo de doble envío. |
| `frontend/src/api.ts` | Envío de la solicitud de registro con el cliente seleccionado. |
| `frontend/src/router.ts` | Restringe las vistas relacionadas a Administrador y Recepcionista. |
| `backend/app/main.py` | Endpoint multipart y guardia de roles; expone además el listado/foto usado por la vista de vehículos. |
| `backend/app/vehicle_registration.py` | Validación, normalización, control de duplicidad, almacenamiento, transacción y respuesta. |
| `backend/app/auth.py` | Autenticación y roles efectivos en backend. |
| `backend/app/models.py` | Modelo y relaciones de Cliente, Vehículo y Estatus. |
| `database/migrations/005_vehicle_registration.sql` | Cambios del esquema requeridos por los datos de vehículo. |
| `frontend/src/views/VehicleListView.vue` | Vista complementaria para visualizar vehículos registrados, fotografía, cliente y estatus. |
| `backend/tests/test_roles_and_workshops.py` | Pruebas de registro, permisos, cliente inactivo, validaciones, duplicados, imagen y rollback. |

No se detectó ni creó dependencia externa nueva para esta implementación. La lectura de imágenes usa Pillow, que ya forma parte del entorno del backend.

## Diagramas

Fuentes editables Mermaid:

- [Caso de uso](diagramas/uc06-caso-uso-registrar-vehiculo.mmd)
- [Actividad](diagramas/uc06-actividad-registrar-vehiculo.mmd)
- [Secuencia](diagramas/uc06-secuencia-registrar-vehiculo.mmd)
- [Relación Cliente–Vehículo](diagramas/uc06-er-cliente-vehiculo.mmd)

Render Archify: [diagrama interactivo HTML](diagramas/uc06-registrar-vehiculo-archify.html). La revisión visual PNG, sus temas claro/oscuro y tamaños, está en [uc06-visual-check](diagramas/uc06-visual-check/). El workflow editable de Archify está en [uc06-registrar-vehiculo.workflow.json](diagramas/uc06-registrar-vehiculo.workflow.json).

## Comandos ejecutados y propósito

Ejecutados desde `backend` salvo donde se indique:

| Comando | Propósito |
|---|---|
| `python -m unittest discover -s tests -p test_roles_and_workshops.py -k <método> -v` (cinco métodos de vehículo, uno por ejecución) | Aislar registro exitoso, roles/cliente inactivo, datos y duplicados, foto y rollback. |
| `python -m unittest discover -s tests -p test_roles_and_workshops.py -v` | Suite relacionada completa. |
| `npm run build` (en `frontend`) | Compilar el frontend y comprobar integración. |
| Consulta de solo lectura `SHOW INDEX FROM vehicles WHERE Non_unique=0` y claves foráneas de `information_schema.KEY_COLUMN_USAGE` | Verificar restricciones y relaciones reales de MySQL. |
| Consultas agregadas de conteo y `SHOW COLUMNS FROM vehicles` | Comprobar esquema y evidencia existente sin imprimir información personal. |
| `GET /health`, preflight CORS de `/api/v1/vehicles` y `GET /api/v1/vehicles` sin token | Comprobar que la API responde, permite el origen del frontend y protege el listado. |
| Archify `deliver`, `check`, `browser-check`, `visual-check` | Validar el workflow y generar HTML y capturas revisables. |

El lanzador Python del entorno mostró un aviso de ruta de Python 3.14 al iniciar, pero las ejecuciones de unittest completaron y devolvieron resultados.

## Pruebas ejecutadas y resultados

- **5 pruebas individuales del vehículo:** todas satisfactorias.
- **Suite relacionada clientes/roles/talleres/vehículos:** 19 pruebas satisfactorias.
- **Build frontend:** satisfactorio; Vite transformó 596 módulos.
- **Esquema MySQL:** inspección de solo lectura satisfactoria; campos, FK y claves únicas presentes.
- **API y navegador:** `/health` respondió 200; CORS de la aplicación respondió 200; el listado sin token respondió 401. La vista `/vehiculos` cargó el registro existente con imagen, cliente y estatus.
- **Archify:** workflow validado (9 comprobaciones), revisión de navegador y revisión visual correctas; el HTML y PNG se generaron.

### Evidencia de persistencia disponible

La base MySQL local ya contenía un registro antes de esta verificación. Una consulta agregada confirmó: **1 vehículo**, **1 con cliente asociado**, **1 activo**, **1 referencia de fotografía** y **1 archivo correspondiente presente**. La interfaz `/vehiculos` mostró esa tarjeta. No se creó otro registro sobre datos reales durante la comprobación, para evitar alterar los datos del usuario. La prueba de éxito aislada verifica la relación con el cliente de prueba, `id_estatus = 1` y la normalización de campos; la prueba de foto confirma archivo y referencia.

Las pruebas funcionales del backend usan su base de pruebas; el esquema MySQL real y el registro ya existente se verificaron por separado. No se ejecutó una escritura de prueba en MySQL real.

## Estado de actividades

| actividad | acción realizada | comando o prueba ejecutada | resultado obtenido | estado | evidencia |
|---|---|---|---|---|---|
| Inspección de módulos | Revisados clientes, vehículos, autenticación, DB y almacenamiento | Lectura de módulos/modelos/migración | Se confirmó la implementación existente y su estructura | Implementado y verificado | Archivos enumerados arriba |
| Brechas e integración | Comprobada la acción contextual y el `client_id` seleccionado; no se duplicó funcionalidad | Inspección de `ClientManagementView.vue`, API y endpoint | Cliente activo queda fijado desde la ruta y se vuelve a comprobar en backend | Implementado y verificado | Prueba de éxito y de cliente inactivo |
| Reglas, permisos y guardado | Verificados roles, normalización, duplicidad, foto, transacción y estatus | 5 pruebas unitarias enfocadas | 5/5 correctas | Implementado y verificado | Suite `test_roles_and_workshops.py` |
| Integridad MySQL | Consultadas columnas, FK e índices únicos; lectura agregada | `SHOW COLUMNS`, `SHOW INDEX`, `information_schema`, conteos | FK y unicidad presentes; fila existente activa con foto | Implementado y verificado | Resultado agregado descrito arriba |
| Suite relacionada | Ejecutada completa | unittest discover | 19/19 correctas | Implementado y verificado | Salida de unittest de esta tarea |
| Compilación | Compilado el frontend | `npm run build` | Build correcto; 596 módulos | Implementado y verificado | Salida de Vite |
| Registro real nuevo | No se insertó un registro artificial en la base MySQL del usuario | No aplica; se evitó escritura sobre datos reales | Éxito de registro demostrado en DB de pruebas y fila real preexistente inspeccionada | Implementado sin verificación completa | Prueba backend y lectura agregada; no hay POST de alta contra MySQL real |
| Documentación/diagramas | Elaborado el informe, fuentes Mermaid y HTML/PNG Archify | `deliver`, `check`, `browser-check`, `visual-check` | Validación y revisión visual correctas | Implementado y verificado | `analisis/diagramas/` |

## Pendientes y limitaciones

- No se hizo una nueva alta real en MySQL; la escritura está cubierta por pruebas aisladas y la evidencia de producción local es una fila que ya existía.
- No se comprobó una carrera concurrente mediante dos solicitudes simultáneas; las restricciones únicas de placa/VIN de MySQL protegen el conflicto final y el servicio maneja `IntegrityError`.
- La versión instalada de la skill Archify indica que existe una actualización disponible; no se actualizó durante esta tarea.
