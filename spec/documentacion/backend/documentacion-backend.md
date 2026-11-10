---
name: fastapi-backend-reference
description: Referencia de arquitectura y operación del backend FastAPI de Taller Mecánico.
version: 1.1.0
language: es
---
# Referencia del backend

## Propósito

Describe la implementación de este repositorio. Para principios reutilizables consulta la [guía Python/FastAPI](../../skills/Python_FastAPI_Best_Practices_Skill.md); para procesos del negocio consulta [análisis](../../../analisis/README.md).

## Arquitectura actual

El backend es una aplicación FastAPI en `backend/app/` con SQLAlchemy síncrono y MySQL. Los módulos se separan por responsabilidad de dominio, sin una estructura universal `api/services/repositories` impuesta:

| Módulo | Responsabilidad |
| --- | --- |
| `main.py` | Construcción de la app y registro de endpoints. |
| `auth.py`, `security.py` | Identidad JWT, permisos y operaciones criptográficas. |
| `config.py` | Configuración de entorno y validación de secretos. |
| `database.py`, `models.py` | Motor/sesiones y entidades ORM. |
| `schemas.py` | Validación y contratos Pydantic. |
| `administration.py` | Roles, usuarios internos, talleres y catálogo postal. |
| `client_registration.py` | Registro de clientes y auditoría relacionada. |
| `vehicle_registration.py` | Registro/consulta de vehículos según el flujo implementado. |
| `password_recovery.py` | Flujo de recuperación de contraseña. |
| `bootstrap_admin.py` | Alta local inicial del administrador. |
| `import_postal_codes.py` | Importación del catálogo SEPOMEX local. |

Verifica el código antes de asumir que una ruta o comportamiento descrito en documentos históricos sigue activo.

## Contratos y acceso

- El prefijo de API se configura mediante `API_PREFIX`; el valor documentado por defecto es `/api/v1`.
- Las entradas y salidas se validan con Pydantic; la autenticación usa Bearer JWT.
- Las rutas protegidas deben comprobar cuenta activa y rol requerido en backend.
- `DATABASE_URL` y `JWT_SECRET_KEY` se configuran en `backend/.env`, que no debe versionarse.

## Persistencia y transacciones

`database/init.sql` sirve para inicializar una base nueva. Los cambios posteriores viven en `database/migrations/`; revisa la secuencia e historial local antes de aplicar. Usa transacciones cuando un caso de uso escriba entidades y auditoría como una unidad. La cuenta de aplicación no debe necesitar permisos DDL en operación ordinaria.

## Comandos

Desde `backend/`, con entorno virtual activado:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
uvicorn app.main:app --reload
```

La suite y sus requisitos deben instalarse desde `requirements.txt`. Informa cualquier prueba omitida, fallo ambiental o dependencia faltante; no extrapoles un resultado anterior al estado actual.

## Evolución

Separa routers, servicios o repositorios cuando el tamaño y las dependencias lo hagan más claro. Mantén el comportamiento existente y la migración de datos revisable; evita refactorizaciones generales al implementar un caso de uso acotado.
