# UC-SEG-01 — Crear roles

## Objetivo y alcance

Permitir al Administrador crear un rol con nombre y descripción opcional. El backend recorta los espacios exteriores del nombre, calcula una forma normalizada para detectar duplicados, asigna un código interno estable al rol nuevo y lo guarda como Activo. La creación también deja un evento de auditoría en la misma transacción.

Este caso de uso no asigna permisos al rol personalizado, no crea cuentas de usuario y no administra talleres.

## Actor y precondiciones

- Actor principal: Administrador.
- El Administrador debe tener una sesión Bearer válida, la cuenta activa y el rol activo.
- La base debe tener la tabla roles y el catálogo Estatus con el identificador 1 para Activo.
- El nombre enviado debe cumplir las restricciones indicadas abajo.

La autorización real se comprueba en backend; la protección de rutas del frontend solo controla navegación.

## Flujo principal

1. El Administrador abre Administrar roles y elige Crear rol.
2. La interfaz captura el nombre y, opcionalmente, la descripción.
3. La API autentica al usuario, verifica que esté activo y comprueba el código de rol administrador.
4. Pydantic valida el nombre; la regla de dominio recorta sus espacios exteriores y valida los caracteres permitidos.
5. El backend calcula name.casefold() para normalized_name y consulta si ya existe.
6. Si no hay conflicto, crea el rol con un code interno custom_<uuid>, normalized_name único e id_estatus = 1.
7. En la misma transacción agrega el evento admin.role_created con el identificador del rol y confirma.
8. La interfaz vuelve a consultar el catálogo y muestra el rol activo.

## Flujos alternativos y excepciones

- Sesión ausente, vencida, usuario suspendido o rol suspendido: HTTP 401; no se crea el rol.
- Usuario autenticado que no es Administrador: HTTP 403; no se crea el rol.
- Nombre vacío, corto, largo o con caracteres no admitidos: HTTP 422.
- Nombre equivalente tras recortar espacios y aplicar casefold: HTTP 409 DUPLICATE_ROLE.
- Dos solicitudes concurrentes con el mismo nombre: la restricción única de normalized_name evita la segunda inserción; se responde como duplicidad.
- Error durante persistencia o auditoría: rollback y HTTP 500 PERSISTENCE_ERROR.

## Reglas, campos y contrato API

| Entrada | Reglas efectivas en servidor |
|---|---|
| name | Obligatorio; Pydantic exige inicialmente 2–40 caracteres en el texto recibido. Luego se recortan espacios y se permiten letras Unicode, números, guion bajo, espacios, punto, apóstrofo y guion. La forma casefold no debe superar 40 caracteres. |
| description | Opcional; hasta 200 caracteres; se recortan espacios exteriores y el texto vacío se guarda como nulo. |

- Endpoint: POST /api/v1/admin/roles.
- Autorización: Administrador activo.
- Éxito: HTTP 201; devuelve la representación del rol y su estado.
- Errores distinguibles: 401, 403, 409 DUPLICATE_ROLE, 422 y 500 PERSISTENCE_ERROR.
- normalized_name usa casefold para comparación; el nombre presentado conserva las mayúsculas/minúsculas capturadas una vez recortadas.
- Detalle de implementación: la longitud mínima de Pydantic se evalúa antes de recortar; por ello, una entrada de un carácter rodeada de espacios puede pasar esa comprobación. La regla de caracteres solo rechaza el nombre si queda vacío. La longitud exacta del campo normalizado no debe documentarse como mínimo garantizado por el backend actual.
- code se genera para ser estable al cambiar el nombre del rol.
- Los roles personalizados no reciben privilegios automáticamente. Las rutas siguen exigiendo códigos de rol autorizados explícitamente.

## Persistencia y relaciones

- roles: id PK; code UNIQUE; name UNIQUE; normalized_name UNIQUE; description nullable; id_estatus FK a Estatus.IdEstatus.
- Estatus: IdEstatus PK; Valor UNIQUE; Descripcion.
- audit_logs: id PK; user_id FK nullable a users.id; action; detail; created_at. El evento usa action admin.role_created y detail role_id=<id>.
- La fila de rol y su auditoría se agregan dentro de la misma transacción SQLAlchemy.

## Diagrama de actividad y secuencia

- Actividad: diagramas/crear-roles.activity.mmd; también existe la fuente Archify diagramas/crear-roles.workflow.json.
- Secuencia: diagramas/crear-roles.sequence.mmd.
- Modelo relacional compartido: diagramas/modelo-datos.mmd.

## Criterios de aceptación y casos límite

1. Administrador con sesión activa crea un nombre válido; se guarda como Activo y hay evento de auditoría.
2. Mecánico o Recepcionista recibe 403 y no se crea fila.
3. Un valor vacío, de menos de dos caracteres antes del recorte, mayor de cuarenta en la entrada o con símbolos no permitidos recibe 422. La entrada de un carácter rodeada de espacios es una limitación conocida del validador actual.
4. “Mecánico” y “ mecánico ” se consideran duplicados por normalización y reciben 409 en la segunda solicitud.
5. Dos altas simultáneas del mismo nombre no crean dos roles por la restricción UNIQUE de normalized_name.
6. El rol creado no permite por sí mismo acceder a operaciones protegidas.

## Verificación registrada

La documentación previa del proyecto registra que la suite SQLite combinada de roles y talleres tuvo ocho casos satisfactorios y uno omitido por una dependencia de imagen; los casos cubren creación/duplicidad normalizada y rechazo de un rol no administrador. El build Vue/Vite también se registró satisfactorio. En esta actualización se inspeccionó el código y el archivo de pruebas, pero no se volvió a ejecutar la suite ni se conectó a MySQL. No hay una prueba automatizada de límite mínimo posrecorte ni de concurrencia en MySQL.

## Archivos relacionados y responsabilidad

- backend/app/administration.py: esquema de entrada, normalización, detección de duplicidad, alta, auditoría y respuesta.
- backend/app/auth.py: valida sesión, usuario activo y rol activo; require_roles aplica el código autorizado.
- backend/app/models.py: modelos Role, Status, User y AuditLog.
- frontend/src/views/RoleManagementView.vue: formulario de alta y actualización visual de la lista.
- frontend/src/api.ts: POST de creación y GET de roles.
- frontend/src/router.ts: restringe /admin/roles a Administrador en la interfaz.
- database/migrations/002_roles_workshops_postal.sql: códigos, estado, restricciones únicas y FK.
- backend/tests/test_roles_and_workshops.py: pruebas SQLite de unicidad normalizada y permisos.

## Dependencias

FastAPI, Pydantic, SQLAlchemy y MySQL en backend; Vue y Vuetify en frontend. No hay dependencia externa para crear roles.

