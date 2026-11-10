---
name: vue-frontend-reference
description: Referencia de arquitectura y operación de la interfaz Taller Mecánico.
version: 1.1.0
language: es
---
# Referencia del frontend

## Propósito

Describe la SPA actual. Para reglas generales consulta la [guía Vue/TypeScript](../../frontend/skill-vue.md); los contratos funcionales están en los casos de uso de [analisis](../../../analisis/README.md).

## Stack y ejecución

La interfaz usa Vue 3, TypeScript, Vite y Vuetify 3. Dependencias y comandos se definen en `frontend/package.json`.

```powershell
cd frontend
npm install
npm run dev
```

`npm run build` ejecuta la comprobación de tipos con `vue-tsc -b` y genera el bundle. `npm run preview` sirve el bundle localmente. No hay script de test o lint frontend declarado actualmente.

## Organización

| Archivo | Responsabilidad |
| --- | --- |
| `src/main.ts`, `src/App.vue` | Arranque de Vue y estructura principal. |
| `src/router.ts` | Rutas, metadatos de acceso y guardas de navegación. |
| `src/api.ts` | Cliente HTTP y contratos del backend. |
| `src/session.ts` | Estado de autenticación en el navegador. |
| `src/validation.ts` | Reglas de validación de formularios para experiencia de usuario. |
| `src/views/` | Autenticación, recuperación, panel, clientes, roles, talleres y vehículos. |
| `src/style.css` | Estilos compartidos y ajustes de interfaz. |

## Reglas de integración

- El backend decide permisos y valida la entrada; las guardas del router y la visibilidad de controles no son controles de seguridad.
- Centraliza peticiones y contratos en `api.ts`; muestra carga y errores en los flujos que dependen de la red.
- Mantén el token en la estrategia de sesión vigente y no lo dupliques en almacenamiento persistente sin un diseño de seguridad explícito.
- Configura la URL de API mediante `VITE_API_URL`; no coloques secretos en variables `VITE_*`, ya que se incluyen en el cliente.
- Si cambia un endpoint o contrato, actualiza los tipos del cliente y el caso de uso relacionado.

## Accesibilidad y diseño adaptable

Usa etiquetas asociadas, interacción por teclado y mensajes claros de validación. Revisa tablas y formularios en anchos pequeños y no dependas solo del color para expresar estado.

## Verificación

Después de cambios de interfaz ejecuta `npm run build` cuando la tarea requiera validar. Registra el comando y resultado observado; compilar no sustituye una verificación manual del flujo en navegador.
