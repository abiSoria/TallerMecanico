# Taller Mecánico

Proyecto académico con SPA Vue 3 + TypeScript + Vite + Vuetify 3, API FastAPI y MySQL. Incluye alta de clientes, login JWT, consulta de perfil y cambio autenticado de contraseña. El registro público siempre crea usuarios con rol `cliente`; la asignación de roles internos requiere una acción administrativa protegida que deberá añadirse al módulo de administración.

## Estructura

```text
TallerMecanico/
├── database/
│   └── init.sql
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── auth.py          # identidad JWT y guardas RBAC reutilizables
│       ├── config.py        # configuración desde variables de entorno
│       ├── database.py      # motor y sesión SQLAlchemy/MySQL
│       ├── main.py          # endpoints auth y salud
│       ├── models.py        # usuarios, roles, clientes, autos, órdenes, auditoría
│       ├── schemas.py       # modelos y validación de API
│       └── security.py      # BCrypt y tokens JWT
└── frontend/
    ├── .env.example
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── api.ts
        ├── main.ts
        ├── router.ts
        ├── session.ts
        ├── validation.ts
        ├── style.css
        └── views/
            ├── AuthView.vue
            └── DashboardView.vue
```

## Seguridad implementada

- BCrypt con costo 12; sólo se persiste el hash. La política acepta de 12 a 72 bytes y exige mayúscula, minúscula, dígito y símbolo.
- JWT firmado HS256, vencimiento configurable y rol incluido en el token; `current_user` comprueba además que la cuenta siga activa. `require_roles(...)` protege futuros endpoints por rol.
- El alta pública fuerza el rol cliente en el servidor. Los usuarios no pueden elegir ni elevar su rol desde el formulario.
- Los errores de login no revelan si una cuenta existe; cambio de clave exige sesión y clave actual y revoca la sesión de frontend al terminar.
- Las reglas de nombre, correo, teléfono y clave están duplicadas en el frontend y backend. El backend es la autoridad final.
- El token se mantiene en memoria para reducir exposición a XSS por almacenamiento web persistente; al recargar la pestaña, se solicita login de nuevo. En producción, usar HTTPS, secretos gestionados, rate limiting, políticas de respaldo y revisión de dependencias.

## Requisitos

- Python 3.11 o superior.
- Node.js 20.19+ o 22.12+ (requisito de las versiones actuales de Vite).
- MySQL 8.0+ y npm.

## Arranque local en Windows PowerShell

### 1. Base MySQL

Inicia el servicio MySQL. En una terminal con acceso administrativo:

```powershell
cmd /c "mysql -u root -p < database\init.sql"
```

El script crea `taller_mecanico`, el usuario local `taller_app`, las tablas e inserta los seis roles. Antes de ejecutarlo, cambia `CAMBIA_ESTA_CLAVE` tanto en el script como en el `.env` del backend. Si tu usuario de aplicación necesita conectarse desde otro host, ajusta `'taller_app'@'localhost'` según tu política local.

### 2. Backend FastAPI

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `backend/.env`: establece la clave de MySQL y `JWT_SECRET_KEY` con un valor aleatorio secreto (por ejemplo, genera uno con `py -c "import secrets; print(secrets.token_urlsafe(48))"`). Luego arranca:

```powershell
uvicorn app.main:app --reload
```

API: `http://localhost:8000`; OpenAPI interactivo: `http://localhost:8000/docs`; salud: `http://localhost:8000/health`.

### 3. Frontend Vue/Vite

En otra terminal desde la carpeta del proyecto:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Abre `http://localhost:5173`. Configura `VITE_API_URL` en `frontend/.env` si FastAPI no está en `http://localhost:8000/api/v1`. Para generar el bundle: `npm run build`.

## Endpoints de autenticación

| Método | Ruta | Acceso | Resultado |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | público | Crea cliente + perfil e inicia sesión |
| `POST` | `/api/v1/auth/login` | público | Valida BCrypt y emite JWT |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Devuelve el usuario y rol actuales |
| `POST` | `/api/v1/auth/change-password` | Bearer JWT | Valida clave actual y sustituye el hash |
| `GET` | `/api/v1/admin/users` | Administrador | Lista las cuentas internas |
| `POST` | `/api/v1/admin/users` | Administrador | Crea cuentas internas con un rol asignado |

## Primer acceso administrativo

Después de aplicar el SQL y configurar `backend/.env`, crea el primer administrador desde `backend`:

```powershell
.\.venv\Scripts\Activate.ps1
py -m app.bootstrap_admin
```

El asistente solicita nombre, correo y contraseña de forma interactiva. Sólo funciona si aún no existe un administrador. Después, inicia sesión en el portal y usa **Agregar al equipo** para crear accesos de recepcionista, asesor de servicio y técnico. Cada persona inicia sesión con su propio correo y contraseña. El perfil `sistema` se reserva para procesos internos y no se ofrece como cuenta humana.

El panel muestra una experiencia adecuada para cada perfil. Las secciones de clientes, vehículos, órdenes, diagnósticos, refacciones y notificaciones son la siguiente ampliación funcional del proyecto.

### Recorrido manual de verificación

Con MySQL y FastAPI encendidos, abre `/docs` y prueba en orden:

1. `POST /auth/register` con un correo nuevo y clave segura. Debe responder `201`, devolver un token y asignar `role: cliente`. Repite el mismo correo: debe responder `409`.
2. `POST /auth/login` con la clave correcta: `200` y JWT. Con una clave incorrecta: `401` con mensaje genérico.
3. Pulsa **Authorize** en Swagger con el token y llama `GET /auth/me`: debe devolver el usuario autenticado.
4. Llama `POST /auth/change-password` con `current_password` y otra clave válida: debe responder `204`. Clave actual incorrecta debe dar `400`.
5. Inicia sesión con la clave anterior: `401`. Inicia con la clave nueva: `200`. En el panel, el cambio de clave también borra la sesión de frontend y redirige a login.
6. Prueba contraseñas cortas o sin mayúscula, número o símbolo en el formulario y directamente en la API. El formulario las marca y FastAPI debe rechazar la petición con `422`.

Este recorrido se ejecutó localmente: registro asigna el rol cliente, login y perfil responden correctamente, el cambio de contraseña invalida la clave anterior y un técnico no puede listar usuarios administrativos.

Ejemplo de alta:

```json
{
  "full_name": "Ana López",
  "email": "ana@example.com",
  "phone": "+52 55 1234 5678",
  "password": "EjemploSeguro#2026"
}
```

El panel ofrece navegación visual por rol. La consulta real de órdenes requiere implementar endpoints operativos y asociar vehículos; los modelos y tablas iniciales ya están definidos. Diagnósticos, autorizaciones, refacciones y notificaciones quedan como ampliaciones del ciclo operativo.

## Roles iniciales

El SQL crea `administrador`, `recepcionista`, `asesor_servicio`, `tecnico`, `cliente` y `sistema`. El asistente local `python -m app.bootstrap_admin` crea el primer administrador una sola vez; las cuentas internas posteriores se administran desde el panel y el servidor exige el rol `administrador`.
