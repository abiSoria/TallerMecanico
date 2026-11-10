---
name: python-fastapi-best-practices
description: Guía para diseñar, implementar y revisar servicios FastAPI en este repositorio.
version: 1.1.0
language: es
---
# Buenas prácticas de Python y FastAPI

## Propósito y alcance

Usa esta guía para tareas de backend Python/FastAPI. Respeta primero el alcance solicitado y la arquitectura que ya existe. El árbol de ejemplo es una posible evolución para módulos que lo necesiten, no una orden de reorganizar todo el backend en cada cambio.

## Principios

- Mantén responsabilidades claras y dependencias explícitas; aplica SOLID, DRY y KISS con criterio.
- Usa type hints y modelos Pydantic v2 para entradas y salidas de API.
- Mantén validación y autorización en el servidor, aunque el frontend también valide o esconda acciones.
- No agregues abstracciones, dependencias o endpoints que no resuelvan una necesidad concreta.

## Estructura existente y evolución

El backend actual organiza módulos por responsabilidad dentro de `backend/app/` (`administration.py`, `client_registration.py`, `vehicle_registration.py`, entre otros). Continúa ese patrón cuando sea suficiente. Si un módulo crece y la separación aporta claridad, se puede dividir gradualmente en routers, servicios y repositorios; evita una migración global ajena al alcance.

Una separación posible para módulos complejos:

```text
app/
├── api/             # Routers y endpoints
├── services/        # Reglas y coordinación de casos de uso
├── repositories/    # Consultas y persistencia
├── models.py        # Entidades SQLAlchemy del proyecto
├── schemas.py       # Contratos Pydantic del proyecto
├── core/            # Configuración y seguridad compartida
└── main.py          # Ensamble de la aplicación
```

Adapta el ejemplo a la estructura real antes de crear archivos. No mantengas dos definiciones del mismo contrato.

## Endpoints y dependencias

- Mantén cada endpoint enfocado en HTTP: validar contrato, invocar el caso de uso y traducir resultados a respuestas.
- Inyecta sesiones y contexto autenticado mediante dependencias de FastAPI (`Depends`).
- Reutiliza dependencias existentes para usuario actual, permisos y sesión de base de datos.
- Devuelve códigos HTTP coherentes y errores seguros, sin filtrar SQL, credenciales ni trazas al cliente.

## Persistencia y rendimiento

- Usa sesiones SQLAlchemy de alcance acotado y transacciones explícitas en operaciones que escriben varios registros.
- Selecciona los campos necesarios; evita consultas sin límite cuando los conjuntos puedan crecer.
- Añade índices según filtros, uniones y restricciones reales; revisa duplicados tanto en lógica de aplicación como con restricciones de base de datos.
- Evita N+1 y round trips innecesarios; mide antes de añadir optimizaciones o operaciones por lotes.
- La capa actual usa SQLAlchemy síncrono y MySQL síncrono: conserva el modelo síncrono en ese flujo. No mezcles I/O síncrono con rutas `async`; adopta async solo junto con dependencias y driver asíncronos compatibles.

## Seguridad

- Carga secretos desde entorno/configuración; no los guardes en código ni logs.
- Verifica identidad, estado activo y rol del lado servidor en cada operación protegida.
- Valida formato, tamaño y contenido real de archivos subidos; usa nombres generados por servidor y limpia temporales al fallar.
- Usa hash de contraseña diseñado para credenciales y no registres contraseñas ni tokens.
- Evita SQL dinámico no parametrizado y mensajes de error que revelen datos sensibles.

## Pruebas y revisión

Cubre reglas de negocio, permisos, errores y límites. Prefiere pruebas aisladas y repetibles, y pruebas de integración para contratos o persistencia relevantes. No afirmes un porcentaje mínimo universal sin medir cobertura y acordar alcance. Ejecuta las pruebas pertinentes y comunica cuáles corriste y el resultado real.

## Secuencia de trabajo

1. Lee el caso de uso y los contratos existentes.
2. Define comportamiento, permisos, persistencia y errores esperados.
3. Implementa el cambio mínimo siguiendo los patrones locales.
4. Añade o actualiza pruebas del comportamiento afectado.
5. Revisa seguridad, transacciones, consultas y documentación.
6. Resume archivos, validaciones ejecutadas y limitaciones conocidas.
