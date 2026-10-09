# UC-SEG-02 — Administrar roles

## Objetivo y alcance

Permitir al Administrador consultar roles con su estado, editar nombre y descripción, y suspender roles mediante baja lógica. Los registros no se borran físicamente. La autorización efectiva y las reglas de integridad se aplican en backend.

No contempla asignar permisos a roles personalizados ni administrar talleres.

## Actor y precondiciones

- Actor: Administrador autenticado, con usuario y rol activos.
- La migración de roles debe estar aplicada y el catálogo Estatus debe contener Activo (1) y Suspendido (2).
- Los roles se consultan junto con Estatus mediante INNER JOIN.

## Flujo principal

1. El Administrador abre Administrar roles.
2. El frontend solicita GET /api/v1/admin/roles.
3. El backend valida sesión y rol; devuelve cada rol con Valor y Descripcion de Estatus.
4. Para editar, el Administrador elige un rol y envía el nuevo nombre y descripción con PUT /api/v1/admin/roles/{id}.
5. El backend verifica existencia, valida y recorta los campos, calcula normalized_name y comprueba que no pertenezca a otro rol.
6. Actualiza name, normalized_name y description; conserva id, code y relaciones de usuarios. Registra admin.role_updated y confirma la transacción.
7. Para suspender, el Administrador elige Suspender y confirma en la interfaz.
8. El backend vuelve a comprobar autorización, bloquea la fila para actualización cuando la base admite FOR UPDATE, comprueba existencia, estado, asignaciones y protección del Administrador.
9. Si es elegible, cambia id_estatus de 1 a 2, registra admin.role_suspended y confirma. No elimina la fila.
10. Los roles suspendidos se muestran como tales, se excluyen de la lista de roles asignables y no autorizan sesiones existentes.

## Flujos alternativos y excepciones

- Sesión o usuario/rol inactivo: HTTP 401.
- Actor distinto de Administrador: HTTP 403.
- Rol solicitado inexistente: HTTP 404 ROLE_NOT_FOUND.
- Nombre de edición inválido: HTTP 422.
- Nombre normalizado que ya pertenece a otro rol: HTTP 409 DUPLICATE_ROLE.
- Intento de suspender un rol ya suspendido: HTTP 409 ALREADY_SUSPENDED; no se repite la transición.
- Rol asignado a cualquier usuario: HTTP 409 ROLE_IN_USE.
- Rol con code administrador: HTTP 409 ROLE_IN_USE, aun cuando no se encuentre asignado.
- Error de base de datos en actualización o suspensión: rollback y HTTP 500 PERSISTENCE_ERROR.
- Si la unión de catálogo no encontrara un Estatus válido, la consulta INNER JOIN no devolvería esa fila; la FK debe impedir esa inconsistencia en operación normal.

## Entradas, permisos y endpoints

| Operación | Endpoint | Entrada |
|---|---|---|
| Consultar todos | GET /api/v1/admin/roles | Ninguna |
| Consultar asignables | GET /api/v1/admin/roles/active | Ninguna; devuelve roles activos |
| Actualizar | PUT /api/v1/admin/roles/{role_id} | name obligatorio de 2–40 caracteres; description opcional de hasta 200 |
| Suspender | DELETE /api/v1/admin/roles/{role_id} | Identificador en ruta |

Para name se aplican los mismos caracteres permitidos, recorte y casefold descritos en UC-SEG-01. El código estable code no se modifica al renombrar. Solo Administrador activo puede usar estas operaciones.

## Reglas de negocio e integridad

- Suspender significa cambiar id_estatus de 1 a 2, no borrar.
- No se suspende ningún rol que tenga usuarios asignados, ni siquiera cuentas inactivas; tampoco se suspende el rol administrador.
- Un rol suspendido no puede asignarse al crear una cuenta interna: la API busca id_estatus = 1. Backend también deniega autenticación/autorización para un rol suspendido.
- Editar conserva relaciones históricas de users.role_id.
- El cambio y el evento de auditoría se escriben en la misma transacción.
- La interfaz desactiva el botón para roles ya suspendidos; el backend sigue siendo autoridad ante peticiones directas.

## Tablas, claves y relaciones

- roles(id PK, code UNIQUE, name UNIQUE, normalized_name UNIQUE, description, id_estatus FK).
- Estatus(IdEstatus PK, Valor UNIQUE, Descripcion); roles y users guardan únicamente el identificador de estado.
- users.role_id FK a roles.id; users.id_estatus FK a Estatus.IdEstatus.
- audit_logs(id PK, user_id FK nullable, action, detail, created_at).
- Lectura de roles y estatus: INNER JOIN. Lectura de roles asignables: mismo catálogo con id_estatus = 1.
- Valores del catálogo: 1 Activo; 2 Suspendido.

## Diagramas

- Actividad: diagramas/administrar-roles.activity.mmd; fuente Archify diagramas/administrar-roles.workflow.json.
- Secuencia: diagramas/administrar-roles.sequence.mmd.
- Relaciones persistentes: diagrama compartido diagramas/modelo-datos.mmd.

## Criterios de aceptación y casos límite

1. Administrador consulta roles y ve el estado y descripción provenientes de Estatus.
2. Actualizar nombre conserva code, ID, estado y usuarios asignados.
3. Actualizar al nombre normalizado de otro rol devuelve 409 y no cambia el registro.
4. Suspender rol libre cambia estado a 2 y conserva su fila.
5. Repetir suspensión devuelve 409 ALREADY_SUSPENDED.
6. Suspender rol asignado o Administrador devuelve 409 y no modifica su estado.
7. Un rol suspendido no aparece en GET /admin/roles/active ni puede asignarse o autorizar operaciones.
8. Un rol sin fila asociada en Estatus no se oculta accidentalmente por otro tipo de unión: el contrato usa INNER JOIN y la integridad depende de la FK.

## Verificación registrada

La suite SQLite existente cubre suspensión lógica y repetida, rechazo de roles asignados y del rol Administrador, asignación de rol suspendido y rechazo de autenticación con rol suspendido. También prueba duplicidad de nombre al crear, no al renombrar. No contiene pruebas automatizadas de los endpoints de listado ni de actualización de nombre; tampoco prueba el bloqueo FOR UPDATE o concurrencia en MySQL. La documentación anterior registra ocho pruebas satisfactorias y una omitida en la suite combinada. No se ejecutó nuevamente en esta actualización documental.

## Archivos relacionados y responsabilidad

- backend/app/administration.py: listados, actualización, suspensión y auditoría.
- backend/app/auth.py: autenticación y denegación de usuarios o roles suspendidos.
- backend/app/main.py: solo permite asignar roles activos al crear cuentas internas.
- backend/app/models.py: Role, Status, User y AuditLog.
- frontend/src/views/RoleManagementView.vue: consulta, formulario de edición y acción de suspender.
- frontend/src/api.ts y frontend/src/router.ts: llamadas y guardia de la ruta administrativa.
- database/migrations/002_roles_workshops_postal.sql: catálogo, FK y restricciones únicas.
- backend/tests/test_roles_and_workshops.py: pruebas SQLite registradas para la lógica principal.

## Dependencias

FastAPI, Pydantic, SQLAlchemy, MySQL, Vue y Vuetify. No depende de proveedores externos.

