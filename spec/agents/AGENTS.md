# Guía del repositorio

**Versión de la documentación:** 1.1.0 · **Revisada:** 2026-11-05

## Estructura

- `frontend/src/`: SPA Vue 3 y TypeScript. Las vistas están en `views/`; cliente HTTP, sesión, rutas y validación están en los módulos raíz de `src/`.
- `backend/app/`: API FastAPI. `main.py` registra rutas; `auth.py` autentica y autoriza; `administration.py` atiende administración, talleres y catálogo postal; `client_registration.py`, `vehicle_registration.py` y `password_recovery.py` agrupan sus flujos; `models.py`, `schemas.py`, `database.py` y `security.py` implementan modelos, contratos, persistencia y seguridad.
- `backend/tests/`: pruebas Python.
- `database/init.sql`: esquema para instalaciones nuevas. `database/migrations/`: cambios incrementales; revisa historial y esquema antes de aplicar una migración.
- `analisis/`: casos de uso y evidencia; `spec/`: guías, skills y documentación técnica.

## Comandos de desarrollo

Ejecuta desde la carpeta indicada:

- Backend: activa `.venv` dentro de `backend/` y ejecuta `uvicorn app.main:app --reload`.
- Pruebas backend: desde `backend/`, `python -m unittest discover -s tests -v`.
- Frontend: desde `frontend/`, `npm install` y `npm run dev`.
- Build frontend: desde `frontend/`, `npm run build` (ejecuta `vue-tsc -b` y Vite).
- Preview: desde `frontend/`, `npm run preview` después del build.

Configura `backend/.env` y `frontend/.env` usando sus `.env.example`. La API necesita MySQL y un esquema compatible; el frontend puede iniciar aunque la API o MySQL no estén disponibles, pero las operaciones remotas fallarán.

## Convenciones

- Python: cuatro espacios, `snake_case` para funciones/variables y `PascalCase` para clases.
- Vue: componentes y vistas `PascalCase.vue`; TypeScript tipado y composición acorde a los patrones existentes.
- Mantén autenticación, autorización y validación autoritativa en backend. No inventes contratos API; contrasta `schemas.py`, rutas y cliente HTTP.
- Prefiere cambios pequeños que sigan el diseño actual. Introduce capas, abstracciones o dependencias solo cuando la complejidad del caso lo justifique.
- Cambios de datos deben preservar relaciones y datos existentes; las migraciones deben ser explícitas, revisables y aplicadas en orden.

## Verificación

Al cambiar backend, ejecuta las pruebas pertinentes; para cambios de frontend, ejecuta `npm run build`. Si no se ejecutaron, dilo claramente. No describas un resultado histórico como verificación actual. El proyecto no declara un script frontend de test o lint en `package.json`.

## Seguridad

No versionar `.env`, contraseñas, secretos JWT ni archivos de clientes/talleres. Usa placeholders seguros en `.env.example`. Evita incluir secretos o detalles internos de infraestructura en respuestas de API y logs.
