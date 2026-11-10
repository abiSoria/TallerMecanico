# Taller Mecánico

**Versión de la documentación:** 1.3.0 · **Revisada:** 2026-11-10

Aplicación web para administrar operaciones de un taller mecánico. El repositorio contiene una SPA Vue, una API FastAPI y un esquema MySQL. La autorización se aplica en el backend; la interfaz adapta la navegación al rol activo.

## Funcionalidad

- Registro público de cuentas de cliente e inicio de sesión con JWT.
- Consulta de perfil, cambio y recuperación de contraseña.
- Administración de usuarios internos y roles por parte de un administrador.
- Registro y consulta de clientes, talleres y vehículos; la administración de vehículos permite actualizarlos mediante un modal con VIN inmutable.
- Búsqueda local de códigos postales SEPOMEX para apoyar el alta de talleres.
- Auditoría de operaciones de administración y registro.

Las órdenes de trabajo, diagnósticos, refacciones y notificaciones forman parte del dominio previsto, pero no se deben considerar flujos operativos completos solo porque existan entidades o secciones visuales. Revisa los casos de uso para conocer el alcance implementado y sus pruebas pendientes.

## Tecnologías

| Capa | Tecnologías | Responsabilidad |
| --- | --- | --- |
| Interfaz | Vue 3, TypeScript, Vite, Vuetify 3 | Formularios, navegación, validación de experiencia de usuario y consumo de API. |
| API | Python 3.11+, FastAPI, Pydantic, SQLAlchemy | Validación autoritativa, autenticación, autorización, lógica de aplicación y persistencia. |
| Datos | MySQL 8+ | Usuarios, roles, clientes, talleres, vehículos y auditoría. |

## Estructura principal

```text
TallerMecanico/
├── analisis/                 # Casos de uso, decisiones y evidencia
├── backend/
│   ├── app/                  # API, autenticación, administración y servicios de dominio
│   └── tests/                # Pruebas del backend
├── database/
│   ├── init.sql              # Esquema para una base nueva
│   └── migrations/           # Cambios incrementales de esquema
├── frontend/
│   └── src/
│       ├── api.ts            # Cliente y contratos HTTP
│       ├── router.ts         # Rutas y guardas de navegación
│       ├── session.ts        # Estado de sesión
│       ├── validation.ts     # Validaciones de formularios
│       └── views/            # Pantallas de la aplicación
└── spec/                     # Orquestador, skills y documentación técnica
```

Módulos de backend relevantes: `main.py` registra rutas; `auth.py` valida identidad y roles; `administration.py` contiene operaciones administrativas, talleres y catálogo postal; `client_registration.py` y `vehicle_registration.py` implementan flujos de dominio; `password_recovery.py` gestiona recuperación; `models.py`, `schemas.py`, `database.py` y `security.py` definen persistencia, contratos, sesiones y seguridad.

## Requisitos

- Python 3.11 o posterior.
- Node.js 20.19+ o 22.12+ y npm.
- MySQL 8.0 o posterior.

## Inicio local en Windows PowerShell

### 1. Base de datos

Para una instalación nueva, inicia MySQL y aplica `database/init.sql` desde una terminal con el cliente `mysql` instalado. En PowerShell:

```powershell
Get-Content -Raw .\database\init.sql | mysql -u root -p
```

Para una base ya existente, **no vuelvas a aplicar `init.sql`**. Revisa las migraciones en `database/migrations/` y el caso de uso correspondiente; algunas requieren permisos DDL. Cambia los valores de ejemplo antes de usar credenciales locales.

### 2. API

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configura `DATABASE_URL` y `JWT_SECRET_KEY` en `backend/.env`. Genera un secreto aleatorio de al menos 32 bytes, por ejemplo:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Inicia la API desde `backend/`:

```powershell
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`; documentación OpenAPI en `/docs` y comprobación de disponibilidad en `/health`.

### 3. Interfaz

En otra terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Abre `http://127.0.0.1:5173`. Configura `VITE_API_URL` en `frontend/.env` si la API usa otro origen o prefijo.

## Primer administrador

Con el esquema aplicado y el backend configurado, ejecuta desde `backend/`:

```powershell
python -m app.bootstrap_admin
```

El asistente crea el primer administrador si aún no existe. Las cuentas internas posteriores se crean desde la administración protegida. El rol `sistema` se reserva para procesos internos.

## Seguridad y límites

- El alta pública asigna siempre el rol `cliente`; la asignación de roles internos requiere autorización administrativa en el servidor.
- Las contraseñas se almacenan como hash BCrypt; el secreto JWT y la conexión de base de datos deben configurarse fuera del control de versiones.
- El frontend mantiene el token en memoria; recargar la pestaña puede requerir iniciar sesión de nuevo.
- Validaciones y controles visuales del frontend no sustituyen las validaciones ni permisos de la API.
- En despliegues se requieren HTTPS, secretos gestionados, respaldos, limitación de intentos y revisión de dependencias.

## Documentación relacionada

- [Índice y guía de análisis](analisis/README.md)
- [UC-CV-01: registro de clientes](README_UC-CV-01_Registrar_Cliente.md)
- [UC-CV-09: gestión del estado del vehículo](analisis/UC09_gestionar_estado_vehiculo.md)
- [Casos de uso y análisis](analisis/README.md)
- [Orquestador y mapa completo de Markdown](spec/orquestador/orquestador.md)
- [Guía técnica del backend](spec/documentacion/backend/documentacion-backend.md)
- [Guía técnica del frontend](spec/documentacion/frontend/documentacion-frontend.md)

Consulta esos documentos para límites funcionales, criterios de aceptación y evidencia. Los resultados de prueba citados en un caso de uso son históricos y no garantizan que el estado actual haya sido verificado de nuevo.
