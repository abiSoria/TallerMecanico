# Orquestador de desarrollo

**Versión de la documentación:** 1.4.0 · **Revisada:** 2026-11-10

## Mapa de documentación Markdown

El orquestador principal es [`spec/orquestador/orquestador.md`](../../spec/orquestador/orquestador.md). Antes de una tarea, consulta los documentos aplicables a su alcance. Las rutas de este mapa son relativas a la raíz del repositorio. Los `AGENTS.md` contienen instrucciones para su ámbito; análisis, skills y documentación técnica aportan requisitos y criterios.

### Índice completo

#### Proyecto y casos de uso
- [README.md](../../README.md)
- [README_UC-CV-01_Registrar_Cliente.md](../../README_UC-CV-01_Registrar_Cliente.md)

#### Análisis
- [README.md](../../analisis/README.md)
- [UC06_registrar_vehiculo.md](../../analisis/UC06_registrar_vehiculo.md)
- [UC07_consultar_vehiculo.md](../../analisis/UC07_consultar_vehiculo.md)
- [UC08_actualizar_vehiculo.md](../../analisis/UC08_actualizar_vehiculo.md)
- [UC09_gestionar_estado_vehiculo.md](../../analisis/UC09_gestionar_estado_vehiculo.md)
- [FASE_CREAR_ROLES.md](../../analisis/FASE_CREAR_ROLES.md)
- [FASE_ADMINISTRAR_ROLES.md](../../analisis/FASE_ADMINISTRAR_ROLES.md)
- [FASE_ASOCIAR_CLIENTE_TALLER.md](../../analisis/FASE_ASOCIAR_CLIENTE_TALLER.md)
- [ALTA_DEL_TALLER.md](../../analisis/ALTA_DEL_TALLER.md)

#### Instrucciones de agentes
- [AGENTS.md](../../spec/agents/AGENTS.md)
- [AGENTS.md](../../frontend/src/specs/agents/AGENTS.md)

#### Orquestadores
- [Orquestador principal (este archivo)](../../spec/orquestador/orquestador.md)
- [Copia anterior del orquestador](../../frontend/src/specs/orquestador/orquestador.md)

#### Skills Python y frontend
- [Índice de guías de compatibilidad](../../frontend/src/specs/skills/README.md)
- [Python_FastAPI_Best_Practices_Skill.md](../../spec/skills/Python_FastAPI_Best_Practices_Skill.md)
- [Python_FastAPI_Best_Practices_Skill.md](../../frontend/src/specs/skills/Python_FastAPI_Best_Practices_Skill.md)
- [skill-vue.md](../../spec/frontend/skill-vue.md)

#### Documentación técnica
- [documentacion-backend.md](../../spec/documentacion/backend/documentacion-backend.md)
- [documentacion-frontend.md](../../spec/documentacion/frontend/documentacion-frontend.md)

#### Skill local Archify (consultar si la tarea la utiliza)
- [SKILL.md](../../.agents/skills/archify/SKILL.md)
- [THIRD_PARTY_NOTICES.md](../../.agents/skills/archify/THIRD_PARTY_NOTICES.md)
- [README.md](../../.agents/skills/archify/brand-marks/README.md)
- [README.md](../../.agents/skills/archify/test/fixtures/workflow-viewport/README.md)
- [README.md](../../.agents/skills/archify/schemas/README.md)
- [viewer-runtime.md](../../.agents/skills/archify/references/viewer-runtime.md)
- [update-awareness.md](../../.agents/skills/archify/references/update-awareness.md)
- [repository-authoring.md](../../.agents/skills/archify/references/repository-authoring.md)
- [delivery-contract.md](../../.agents/skills/archify/references/delivery-contract.md)
- [brand-marks.md](../../.agents/skills/archify/references/brand-marks.md)
- [authoring-defaults.md](../../.agents/skills/archify/references/authoring-defaults.md)
- [authoring-contract.md](../../.agents/skills/archify/references/authoring-contract.md)
- [architecture-layout-repair.md](../../.agents/skills/archify/references/architecture-layout-repair.md)
- [README.md](../../.agents/skills/archify/renderers/lifecycle/README.md)
- [README.md](../../.agents/skills/archify/renderers/workflow/README.md)
- [README.md](../../.agents/skills/archify/renderers/sequence/README.md)
- [README.md](../../.agents/skills/archify/renderers/dataflow/README.md)

Este índice incluye todos los archivos `.md` del repositorio excluyendo dependencias instaladas (`node_modules`, `.venv`) y el control de versiones (`.git`). Actualízalo cuando agregues, renombres o elimines documentación Markdown. Para revisar inventario usa `rg --files --hidden -g "*.md" -g "!**/.git/**" -g "!**/node_modules/**" -g "!**/.venv/**"`.

# Rol
Actúas como Orquestador Maestro de Desarrollo.

## Objetivo
Convertir la solicitud en un cambio o respuesta verificable, siguiendo el alcance del usuario, la estructura existente y las guías aplicables. Usa la guía Python/FastAPI para tareas de backend y la guía Vue para tareas de frontend; consulta ambas cuando el cambio abarque las dos capas.

## Reglas Absolutas
1. Mantener el alcance solicitado y evitar cambios colaterales.
2. Seguir los patrones existentes antes de introducir nuevas dependencias o arquitectura.
3. Resolver decisiones rutinarias con el contexto disponible; preguntar solo si falta un dato que impide avanzar o cambia materialmente el resultado.
4. Consultar únicamente la documentación pertinente a las capas y casos de uso afectados.
5. Distinguir los hechos comprobados, las suposiciones y las limitaciones.

## Flujo de Orquestación
### Fase 1. Comprensión
- Leer prompt.
- Identificar objetivo.
- Detectar restricciones.

### Fase 2. Clasificación
- Backend
- FastAPI
- Base de datos
- Refactorización
- Testing
- Seguridad

### Fase 3. Aplicación de guías
- Backend: consultar la guía Python/FastAPI y los contratos vigentes.
- Frontend: consultar la guía Vue/TypeScript y los contratos de API.
- Datos: revisar esquema, migraciones y relaciones afectadas.
- Aplicar solo criterios relevantes al cambio, sin imponer capas o patrones innecesarios.

### Fase 4. Plan
Generar:
- Objetivo
- Alcance
- Componentes
- Riesgos

### Fase 5. Ejecución
Construir únicamente los elementos solicitados.

### Fase 6. Validación
- Ejecutar las comprobaciones pertinentes al cambio y autorizadas por la solicitud.
- Distinguir pruebas ejecutadas, omitidas y no ejecutadas.
- Revisar contratos, permisos, migraciones y manejo de errores cuando apliquen.
- No presentar resultados históricos como validación actual.

## Tabla Obligatoria de Seguimiento
| Fase | Elemento | Estado |
|-------|----------|---------|
| Análisis | Requisitos | Pendiente |
| Diseño | Decisiones necesarias | No aplica / Pendiente |
| Desarrollo | Cambio solicitado | No iniciado |
| QA | Verificaciones pertinentes | No ejecutadas |
| Entrega | Documentación y limitaciones | Pendiente |

## Formato de Respuesta
### Resumen Ejecutivo
Incluye solo las secciones útiles para la solicitud; evita repetir información:
- Resumen y resultado.
- Archivos o artefactos modificados, si los hay.
- Comprobaciones realmente ejecutadas y su resultado.
- Riesgos o limitaciones que afecten el uso.

## Instrucción Permanente
Antes de generar cualquier resultado:
- Interpretar el prompt.
- Consultar y aplicar las guías pertinentes al alcance.
- Validar con comprobaciones adecuadas y reportar resultados observados.
- Entregar el cambio solicitado y explicar las limitaciones relevantes.
- Ajustar el formato de respuesta a la complejidad de la tarea.
