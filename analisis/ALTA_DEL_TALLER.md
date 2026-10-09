# UC-TM-01 — Dar de alta un taller mecánico

## Objetivo y alcance

Registrar un taller con datos fiscales, contacto, dirección y fotografía. El RFC normalizado es la clave de unicidad; el nombre puede repetirse. El taller nuevo queda Activo (id_estatus = 1). La API consulta un catálogo postal local para autocompletar dirección y valida la coherencia de la dirección al guardar cuando el CP existe en ese catálogo.

El listado de talleres permite consultar el estado y la fotografía de los registros; no se implementa en este caso una operación para suspender talleres.

## Actores y precondiciones

- Administrador o Recepcionista autenticado, con cuenta y rol activos.
- Migración database/migrations/002_roles_workshops_postal.sql aplicada.
- Para búsqueda de códigos postales, tabla postal_codes creada con 003_postal_codes.sql y catálogo cargado. Sin filas postales se permite captura manual.
- Para validar imágenes reales, Pillow instalado; python-multipart habilita el formulario multipart.
- La carpeta backend/uploads/workshops debe ser escribible por el proceso.

## Flujo principal

1. El actor abre Dar de alta un taller.
2. La sesión y el código de rol se validan en backend. Solo Administrador o Recepcionista pueden continuar.
3. El actor captura nombre, RFC, correo, dirección y fotografía.
4. Durante la captura puede buscar por CP con Enter o el botón: la interfaz consulta el catálogo local, completa estado/municipio/colonia si hay un resultado y pide seleccionar una colonia si existen varias.
5. También puede buscar por estado, municipio/alcaldía y colonia. Si hay un CP único se completa; si hay varios se ofrecen opciones. Si hay cero resultados, permite captura manual.
6. Si la selección va a reemplazar una dirección manual distinta, se solicita confirmación antes de sobrescribirla.
7. Al guardar, backend valida obligatoriedad, EmailStr, CP de cinco dígitos, formato estructural del RFC y fotografía. Si el CP está presente en el catálogo, estado, municipio y colonia deben corresponder a ese CP.
8. Normaliza RFC a mayúsculas y sin espacios exteriores, comprueba duplicidad y revisa la imagen por extensión, tipo MIME, firma y decodificación de Pillow.
9. Guarda la imagen temporal y la mueve a nombre aleatorio dentro de uploads/workshops. Inserta el taller con estado 1 y el evento workshop.created con workshop_id en una transacción de base de datos.
10. Si DB falla, revierte la transacción y el manejador elimina el temporal y el archivo final creado en esta solicitud. Tras commit, responde éxito.
11. Administrador o Recepcionista pueden abrir Talleres registrados. El GET devuelve dirección y Valor del estado mediante INNER JOIN; la fotografía se sirve en un endpoint con la misma autorización. El estado queda visible como Activo o Suspendido.

## Flujos alternativos y errores

- Falta sesión, cuenta inactiva o rol inactivo: HTTP 401.
- Rol distinto de Administrador/Recepcionista: HTTP 403.
- Campo obligatorio, correo, RFC, CP o dirección no válidos: HTTP 422, con código específico cuando aplica.
- RFC ya existente: HTTP 409 DUPLICATE_RFC; la UNIQUE en workshops.rfc protege solicitudes concurrentes.
- Imagen con extensión/formato no autorizado, MIME o contenido no coincidente o corrupto: HTTP 422 INVALID_IMAGE.
- Imagen de más de 10 MiB (10 × 1024 × 1024 bytes): HTTP 413 IMAGE_TOO_LARGE.
- CP conocido pero combinación de estado/municipio/colonia que no corresponde: HTTP 422 ADDRESS_MISMATCH.
- Error durante la verificación o persistencia: HTTP 500 PERSISTENCE_ERROR, con mensaje general y sin datos internos.
- Archivo de catálogo desconocido/catálogo vacío: no hay sugerencia; el usuario completa manualmente. Si el CP sí existe, se exige coherencia al registrar.
- El nombre repetido con RFC distinto se acepta.
- El listado puede mostrar talleres en estado Suspendido si el dato existe en DB; este UC no crea la transición a Suspendido ni proporciona endpoint para ella.

## Campos de entrada y restricciones

| Campo | Regla de servidor |
|---|---|
| name | Obligatorio; hasta 160 caracteres; no es único. |
| rfc | Obligatorio; se recorta y pasa a mayúsculas; patrón estructural de 12 caracteres para moral o 13 para física: letras permitidas, fecha de seis dígitos y homoclave alfanumérica de tres. No verifica situación fiscal ante SAT. |
| contact_email | Obligatorio; validación EmailStr; máximo 254 caracteres en base. |
| street | Obligatorio; hasta 160 caracteres. |
| number | Obligatorio; hasta 30 caracteres. |
| postal_code | Obligatorio; exactamente cinco dígitos. |
| state | Obligatorio; hasta 100 caracteres. |
| municipality | Obligatorio; hasta 120 caracteres. |
| neighborhood | Obligatorio; hasta 120 caracteres. |
| photo | Obligatoria; JPG/JPEG, PNG o WebP; extensión, MIME y firma permitidos, decoder confirma el formato; máximo 10 MiB; se guarda con nombre UUID. |

## Catálogo postal y actualizaciones

La aplicación no depende de una API externa en tiempo de ejecución. La fuente configurada es la descarga nacional de Correos de México/SEPOMEX en TXT delimitado por |. El importador reconoce encabezados SEPOMEX, normaliza CP de cuatro dígitos con cero inicial, descarta registros incompletos y duplicados equivalentes, reemplaza el catálogo en transacción y revierte si no hay filas válidas.

- Tabla e índices: database/migrations/003_postal_codes.sql.
- Importador: backend/app/import_postal_codes.py.
- Fuente: [Correos de México — consulta y exportación de códigos postales](https://www.correosdemexico.gob.mx/sslservicios/consultacp/CodigoPostal_Exportar.aspx).
- Para actualizar: descargar el TXT oficial y ejecutar desde backend: python -m app.import_postal_codes "C:\ruta\al\CodigoPostal_Exportar.txt".
- La documentación previa registra 158,308 filas importadas. Esta cifra describe aquella carga; actualizarla después de cada nueva importación.

## Tablas, claves y relaciones

- workshops: id PK; name; rfc UNIQUE; contact_email; street; number; postal_code; state; municipality; neighborhood; photo_filename; id_estatus FK a Estatus.IdEstatus; created_at.
- Estatus: IdEstatus PK; Valor UNIQUE; Descripcion. El taller guarda solo el identificador 1/2; el alta fija el 1. La consulta usa INNER JOIN para recuperar el estado.
- audit_logs: id PK; user_id FK nullable a users.id; action; detail; created_at. El evento de alta es workshop.created y detail contiene workshop_id.
- postal_codes: clave primaria id; clave única compuesta postal_code, neighborhood, municipality, state; índices por CP y dirección inversa. No existe FK de workshops a postal_codes: se guardan los valores de dirección capturados y se valida consistencia en aplicación.

## API y consulta del registro

| Operación | Endpoint | Autorización |
|---|---|---|
| Autocompletar por CP | GET /api/v1/postal-codes/by-code/{postal_code} | Administrador o Recepcionista |
| Buscar CP por dirección | GET /api/v1/postal-codes/search | Administrador o Recepcionista |
| Dar de alta | POST /api/v1/workshops | Administrador o Recepcionista |
| Consultar talleres y estado | GET /api/v1/workshops | Administrador o Recepcionista |
| Consultar foto | GET /api/v1/workshops/{workshop_id}/photo | Administrador o Recepcionista |

## Diagramas

- Actividad: diagramas/alta-taller.activity.mmd; especificación Archify: diagramas/alta-taller.workflow.json.
- Secuencia: diagramas/alta-taller.sequence.mmd.
- Modelo relacional pertinente a los tres procesos: diagramas/modelo-datos.mmd.

## Criterios de aceptación y casos límite

1. Administrador y Recepcionista activos pueden registrar; otro rol recibe 403 y no persiste.
2. RFC en minúsculas/espacios se guarda normalizado; la segunda solicitud equivalente devuelve 409.
3. El mismo nombre con otro RFC válido se permite.
4. RFC con estructura o longitud incorrecta se rechaza; RFC estructuralmente válido no equivale a consulta fiscal SAT.
5. JPG, JPEG, PNG y WebP cuyo contenido real coincide se aceptan; extensión o MIME falsos, datos corruptos o formato distinto se rechazan.
6. Archivo exactamente de 10 MiB se acepta; 10 MiB más un byte se rechaza.
7. Un CP con una colonia completa dirección; con varias obliga a elegir y no selecciona arbitrariamente.
8. Búsqueda inversa única devuelve CP; múltiples coincidencias solicitan selección; cero resultados permiten captura manual.
9. Si existe CP en el catálogo, una combinación postal incongruente no se guarda.
10. RFC duplicado y errores de DB no generan taller parcial; la auditoría de alta queda en la misma transacción SQL.
11. El listado presenta el estado persistido y la foto solo se entrega a roles autorizados.

## Verificación registrada

La suite SQLite existente cubre rechazo de rol no autorizado mediante la dependencia de autorización, RFC duplicado y rechazo de una imagen mayor de 10 MiB. La prueba de imagen válida exactamente de 10 MiB está condicionada a Pillow y fue registrada como omitida por faltar esa dependencia en el entorno de la ejecución documentada. No hay pruebas del endpoint de alta exitosa ni del listado/fotografía. También se registra un build frontend satisfactorio y una carga SEPOMEX anterior de 158,308 filas. No se documenta una prueba punta a punta en MySQL con sesión y fotografía válida; no se ejecutó de nuevo la suite ni la migración durante esta actualización documental.

## Archivos relacionados y responsabilidad

- backend/app/administration.py: permisos, validaciones, consultas postales, alta, duplicidad, archivo, transacción, auditoría, lista y foto protegida.
- backend/app/auth.py: validación de sesión y rol activo.
- backend/app/models.py: Workshop, Status, PostalCode y AuditLog.
- backend/app/import_postal_codes.py: importación transaccional del catálogo.
- frontend/src/views/WorkshopCreateView.vue: formulario, autocompletado y selección postal.
- frontend/src/views/WorkshopListView.vue: lista de talleres con estado y fotografía.
- frontend/src/api.ts: llamadas a catálogo, alta, listado y foto.
- frontend/src/router.ts y frontend/src/views/DashboardView.vue: rutas y acceso desde el panel.
- database/migrations/002_roles_workshops_postal.sql: esquema de workshops y Estatus.
- database/migrations/003_postal_codes.sql: catálogo postal local.
- backend/tests/test_roles_and_workshops.py: verificaciones de RFC, permisos y límite fotográfico.

## Dependencias

FastAPI, Pydantic EmailStr, SQLAlchemy, MySQL, python-multipart, Pillow, Vue/Vuetify. El catálogo SEPOMEX se descarga y mantiene localmente; no hay servicio postal remoto en tiempo de ejecución.

