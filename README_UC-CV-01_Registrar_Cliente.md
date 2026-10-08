# UC-CV-01 Registrar Cliente

## Objetivo y alcance

Permitir que un usuario autenticado y autorizado registre un cliente del taller. Para este caso de uso, los únicos roles autorizados son **Administrador** y **Recepcionista**. La entidad `Cliente` contiene nombre completo, calle, número, colonia, municipio, estado, teléfono principal, teléfono alterno, correo electrónico y estado activo.

## Flujo implementado

| Paso | Resultado | Resumen |
| --- | --- | --- |
| Abrir alta | Implementado | El Administrador o Recepcionista abre el formulario desde el panel. |
| Capturar datos | Implementado | El formulario recibe los nueve datos del cliente; todos son obligatorios. |
| Validar acceso y datos | Implementado | La API requiere sesión autenticada, comprueba el rol permitido y valida obligatoriedad, formato de teléfonos y correo. |
| Normalizar | Implementado | Se recortan espacios en los campos y se convierte el correo a minúsculas antes de la búsqueda. |
| Buscar coincidencias | Implementado | Se buscan coincidencias por correo, teléfonos o nombre completo junto con domicilio. |
| Confirmar | Implementado | Si hay posible duplicado, la interfaz muestra una alerta y pide confirmación antes de continuar. |
| Persistir | Implementado y ejecutado | El cliente se construye con estado activo y se guarda dentro de una transacción; ante error de persistencia se revierte. Se observó una respuesta HTTP `201` en un registro exitoso. |
| Auditar | Implementado | Tras persistir, se agrega un evento `client.registered` con el usuario, el ID del cliente y la hora de la acción. |

El orden del flujo de negocio es: **Abrir alta → Capturar → Normalizar → Buscar coincidencias → Confirmar → Persistir → Auditar**.

## Patrones de diseño

- **Builder:** `ClientBuilder` normaliza la entrada y construye la entidad `Client` activa.
- **Facade:** `ClientRegistrationFacade` coordina permisos, validación, búsqueda de duplicados, confirmación, persistencia y auditoría.
- **Strategy:** `ContactFormatStrategy` valida datos obligatorios y formatos de teléfonos; `EmailStr` valida el correo.

## API y control de acceso

- `POST /api/v1/clients`: registra un cliente con sesión Bearer; solo permite los roles `administrador` y `recepcionista`.
- `GET /api/v1/admin/client-registrations`: entrega los registros de altas; requiere el rol `administrador`.
- Respuestas del registro distinguen éxito (`201`), datos inválidos (`422`), falta de autorización (`403`), posible duplicado (`409`) y error de persistencia (`500`).

## Apartado Registros

El panel del Administrador muestra una tabla titulada **Registros**, con las columnas **Cliente**, **Lo agregó** y **Fecha y hora**. La tabla usa espaciado y anchos definidos, y permite desplazamiento horizontal en pantallas pequeñas. Se carga al abrir el panel y se actualiza después de registrar un cliente desde esa sesión.

## Archivos de la implementación

- `backend/app/client_registration.py`: entrada, salida, validación, normalización, Builder, Strategy y Facade del registro.
- `backend/app/main.py`: endpoints de registro de cliente y consulta administrativa de registros.
- `frontend/src/api.ts`: contratos y llamadas HTTP.
- `frontend/src/views/DashboardView.vue`: formulario, confirmación de duplicado y apartado **Registros**.
- `frontend/src/style.css`: presentación responsiva de la tabla.
- `database/migrations/001_uc_cv_01_client.sql`: migración del esquema previo de clientes al requerido por UC-CV-01.
- `database/init.sql`: definición de la tabla `clients` para instalaciones nuevas.
- `.archify/workflow-uc-cv-01-20261007-115346/uc-cv-01.html`: diagrama generado con Archify, limitado al flujo de UC-CV-01.

## Ejecución y verificaciones

| Comprobación | Estado | Evidencia |
| --- | --- | --- |
| Backend | Comprobado | `python -m compileall -q app` terminó correctamente. La API respondió `200` en `/health` durante la ejecución local. |
| Frontend | Comprobado | `npm run build` terminó correctamente tras los cambios del panel y de la tabla. |
| Registro | Ejecutado | Se observó un registro exitoso con respuesta HTTP `201`. |
| Migración de esquema | Operativa | El esquema antiguo inicialmente impedía consultar `clients`; después se observó una alta `201`, lo que confirma que una ejecución posterior ya pudo persistir. El usuario de la aplicación no tiene permiso `ALTER`, por lo que la migración no se ejecutó con ese usuario. |
| Consulta y visualización de auditoría | Pendiente de comprobación manual | El endpoint y la tabla están implementados. La consulta recibió `404` antes de reiniciar la API con el endpoint nuevo; no se hizo una comprobación posterior del listado en el panel. |
| Duplicado y reversión ante fallo | Pendiente de comprobación manual | La rama de confirmación y la reversión transaccional están implementadas, pero no se documentó una ejecución manual de esos escenarios. |

No se agregaron casos de uso adicionales a este documento. Las comprobaciones pendientes corresponden a validación manual del comportamiento, no a componentes pendientes de implementación.
