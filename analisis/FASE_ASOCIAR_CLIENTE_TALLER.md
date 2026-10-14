# Asociar un cliente a un taller mecánico activo

## Identificación, objetivo y alcance

**Caso de uso:** Asociar un cliente a un taller mecánico activo. La documentación existente consultada no asigna un identificador UC a este proceso; se mantiene el nombre y no se inventa un código.

Permite asignar o cambiar la relación de un cliente activo con un taller que también esté activo. La relación se almacena en `clients.workshop_id`. El proceso no crea talleres ni clientes y no cambia sus otros datos.

## Actores y precondiciones

- **Administrador** o **Recepcionista**, con sesión autenticada y rol vigente.
- Cliente existente con `id_estatus = 1`.
- Taller seleccionado existente con `id_estatus = 1`.
- Existe en base de datos la relación opcional de `clients.workshop_id` a `workshops.id`.

La ruta del frontend `/clientes` limita el módulo a Administrador y Recepcionista. Las operaciones HTTP están protegidas además por `require_roles` en el backend. La consulta de talleres requiere los mismos roles; el frontend filtra para el selector los registros cuyo `id_estatus` es `1`.

## Flujo principal

1. Abrir **Administrar clientes** y elegir **Asociar a taller** en la fila del cliente activo.
2. El diálogo identifica al cliente seleccionado y presenta el selector de talleres activos.
3. Seleccionar un taller y pulsar **Asociar**. El botón indica el procesamiento y bloquea envíos repetidos.
4. El frontend envía `PUT /api/v1/clients/{client_id}/workshop` con `{ "workshop_id": número }`.
5. El backend comprueba autenticación y rol; bloquea el cliente y confirma que existe y está activo.
6. El backend bloquea el taller y confirma que existe y está activo.
7. Asigna `clients.workshop_id`, confirma la transacción y devuelve la información del cliente con el nombre del taller.
8. El frontend muestra éxito, cierra el diálogo y vuelve a cargar la lista para reflejar la asociación.

El flujo de alta de cliente también permite incluir un `workshop_id` opcional. En ese flujo, el servicio rechaza una referencia a taller que no esté activo. Esta fase no cambia ese comportamiento.

## Flujos alternativos y errores

- Sin sesión válida: `401`; rol no autorizado: `403`; no se cambia la relación.
- Cliente inexistente: `404 CLIENT_NOT_FOUND`.
- Cliente inactivo: `409 CLIENT_INACTIVE`.
- Taller inexistente: `404 WORKSHOP_NOT_FOUND`.
- Taller suspendido/inactivo: `409 WORKSHOP_NOT_ACTIVE`.
- ID inválido o no positivo: validación de entrada `422`.
- Error de base de datos: rollback y `500 PERSISTENCE_ERROR`; la interfaz presenta el error y no afirma que se guardó.
- Si el cliente ya tenía taller, la selección aceptada sustituye `workshop_id` por la nueva referencia activa. La asociación previa no se borra si una validación o escritura falla.

## Entrada, tablas y relaciones

| Entrada | Restricción |
|---|---|
| `client_id` de la ruta | Entero de la fila seleccionada; el cliente debe existir y estar activo. |
| `workshop_id` del cuerpo | Entero mayor que cero; el taller debe existir y estar activo. |

| Tabla/campo | Uso y relación |
|---|---|
| `clients.id` | Clave primaria del cliente seleccionado. |
| `clients.id_estatus` | Debe ser `1` para permitir asociar. |
| `clients.workshop_id` | FK nullable a `workshops.id`; aquí se guarda la asociación. |
| `workshops.id` | Clave primaria del taller escogido. |
| `workshops.id_estatus` | Debe ser `1` para permitir una nueva asociación. |
| `Estatus.IdEstatus` | Referencia para los estados de cliente y taller. |

La migración existente [004_client_workshop.sql](../database/migrations/004_client_workshop.sql) agrega `clients.workshop_id` como nullable y su clave foránea. El modelo SQLAlchemy declara la misma relación. No se requiere una migración nueva para esta fase.

## Archivos existentes inspeccionados

| Archivo | Responsabilidad |
|---|---|
| `frontend/src/views/ClientManagementView.vue` | Acción por fila, selector filtrado a talleres activos, bloqueo mientras guarda, mensajes y recarga. |
| `frontend/src/router.ts` | Restringe `/clientes` a Administrador y Recepcionista. |
| `frontend/src/api.ts` | Métodos `workshops`, `clients` y `associateClientWorkshop`. |
| `backend/app/main.py` | `GET /clients`, `PUT /clients/{client_id}/workshop`; exige Administrador/Recepcionista, valida estados y persiste. |
| `backend/app/auth.py` | Autenticación y `require_roles` usado por los endpoints. |
| `backend/app/client_registration.py` | Contrato `ClientWorkshopIn`; alta de cliente con taller activo opcional. |
| `backend/app/administration.py` | `GET /workshops`, consulta estados y protege acceso por rol. |
| `backend/app/models.py` | FK y relaciones entre Cliente y Taller, estado. |
| `database/migrations/004_client_workshop.sql` | Columna FK nullable para asociar cliente y taller. |
| `backend/tests/test_roles_and_workshops.py` | Pruebas de asociación, estados, integridad y relaciones. Se amplió cobertura de objetivos faltantes e inactivos. |

No se creó ni modificó la lógica de la asociación. El único cambio de código de esta entrega es una prueba que cubre explícitamente cliente inactivo, cliente inexistente y taller inexistente.

## Diagramas

Fuentes Mermaid editables:

- [Caso de uso](diagramas/asociar-cliente-taller-caso-uso.mmd)
- [Actividad](diagramas/asociar-cliente-taller-actividad.mmd)
- [Secuencia](diagramas/asociar-cliente-taller-secuencia.mmd)
- [Relación de entidades](diagramas/asociar-cliente-taller-er.mmd)

Diagrama de proceso generado y validado con Archify: [HTML interactivo](diagramas/asociar-cliente-taller-archify.html). Se conserva la fuente editable en [asociar-cliente-taller.workflow.json](diagramas/asociar-cliente-taller.workflow.json). Se capturó y revisó la vista clara de 1440×900: [captura](diagramas/asociar-cliente-taller-visual-check/asociar-cliente-taller-archify.visual-check.1440x900.light.png); el chequeo también generó tema oscuro y capturas 2048×1320.

## Comandos y pruebas

Ejecutados desde `backend` salvo donde se indica:

| Comando o prueba | Finalidad y resultado |
|---|---|
| `python -m unittest discover -s tests -p test_roles_and_workshops.py -k test_registration_and_association_reject_inactive_workshops -v` | Asociación rechazada para taller inactivo; pasa. |
| `python -m unittest discover -s tests -p test_roles_and_workshops.py -k test_client_list_and_association_keep_workshop_data_out_of_edit_contract -v` | Asociación exitosa y listado actualizado; pasa. |
| `python -m unittest discover -s tests -p test_client_edit_cannot_change_workshop_and_soft_delete_preserves_relations -v` | Verifica que editar/desactivar al cliente preserve asociación e historial; pasa. |
| `python -m unittest discover -s tests -p test_roles_and_workshops.py -k test_association_rejects_inactive_or_missing_client_and_missing_workshop -v` | Rechazos de cliente inactivo, cliente inexistente y taller inexistente; pasa. |
| Comprobación del guard de la ruta `PUT /api/v1/clients/{client_id}/workshop` | Guard real de FastAPI: Administrador y Recepcionista aceptados; rol suspendido rechazado con `403`. |
| `python -m unittest discover -s tests -p test_roles_and_workshops.py -v` | Suite relacionada: **20 pruebas correctas**. |
| `npm run build` desde `frontend` | Build de Vue/Vite correcto; 596 módulos transformados. |
| Consulta MySQL agregada de `information_schema` y conteos | Confirma `clients.workshop_id`, FK a `workshops.id`, y conteos sin leer datos personales. |
| Archify `finalize workflow` | Validación, entrega, strict check y browser-check correctos, sin diagnósticos. |
| Archify `visual-check` + inspección de captura | Contención, legibilidad, UI y temas pasaron; captura clara de 1440×900 inspeccionada y legible. |

El entorno imprime un aviso de ruta del Python 3.14 al iniciar; las ejecuciones del intérprete del entorno virtual terminaron con código cero.

## Evidencia real y estado

En la base MySQL local, consultada en solo lectura, se verificó que `clients.workshop_id` existe y que apunta con FK a `workshops.id`. El conteo agregado indicó **2 clientes**, **1 con taller asignado**, **1 cliente activo asociado** y **1 asociación activa a taller activo**. No se cambiaron datos reales en esta verificación. La escritura exitosa y las ramas de error se prueban en la base SQLite aislada de la suite.

| actividad | acción realizada | comando o prueba | resultado obtenido | estado | evidencia |
|---|---|---|---|---|---|
| Análisis de arquitectura | Revisados frontend, API, modelos, migración y permisos | Inspección de código fuente | La funcionalidad y sus relaciones ya existían | Implementado y verificado | Archivos enumerados arriba |
| UI y selección de datos | Confirmado cliente seleccionado y filtro de talleres activos | Inspección y build frontend | Modal y selector integrados; sin opción de taller inactivo | Implementado y verificado | `ClientManagementView.vue`; build correcto |
| Control de permisos | Confirmado el guard de endpoint y acceso a ruta/listado | Ejecución directa del guard de FastAPI | Admin/Recepción admitidos; rol suspendido recibe 403 | Implementado y verificado | Comprobación `ASSOCIATION_ROUTE_ROLE_GUARD` |
| Validación y asociación | Probados asociación correcta, estados y referencias inexistentes | 4 pruebas individuales | Todas pasan | Implementado y verificado | Tests listados arriba |
| Integridad MySQL | Consultadas columna, FK y conteos | Consulta de solo lectura | FK presente; una asociación activa existente, sin alterar datos | Implementado y verificado | Resultado agregado anterior |
| Regresiones | Ejecutada suite relacionada y build | unittest + `npm run build` | 20/20 pruebas y compilación correctas | Implementado y verificado | Salidas de comandos |
| Documentación/diagramas | Añadidos informe, cuatro fuentes Mermaid y workflow Archify | Archify finalize y visual-check | HTML/browser-check sin diagnósticos; captura inspeccionada y legible | Implementado y verificado | `analisis/diagramas/` y captura enlazada arriba |

## Pendientes y limitaciones

- No se realizó una asociación nueva en MySQL real; se evitó modificar datos del usuario. La ruta de escritura se comprobó con la suite aislada y se verificó una asociación activa preexistente mediante conteo.
- La integración HTTP completa mediante `TestClient` no está habilitada en este entorno porque falta el paquete opcional `httpx2`; se validó el guard de la dependencia de la ruta directamente y se ejercitó la función de asociación con SQLite. No se instaló una dependencia fuera del alcance.
- La asociación permite cambiar el taller existente seleccionando otro activo. El proyecto no elimina automáticamente relaciones históricas cuando un taller posteriormente se suspende; ese ciclo de vida no está especificado en esta fase.
- La skill Archify instalada es 3.0.1; se detectó 3.1.0 disponible. No se actualizó.
