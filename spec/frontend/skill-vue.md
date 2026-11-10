---
name: vue-frontend-best-practices
description: Guía para analizar, implementar y revisar la SPA Vue 3 de este repositorio.
version: 1.1.0
language: es
---
# Buenas prácticas de Vue y TypeScript

## Alcance

Esta guía aplica a `frontend/`. Sigue la estructura y dependencias instaladas en el repositorio. No agregues librerías, stores o capas nuevas sin una necesidad concreta y explícita.

## Vue y TypeScript

- Usa Vue 3 Composition API y prefiere `<script setup lang="ts">` en componentes nuevos, siguiendo el patrón cercano.
- Define tipos para props, eventos, respuestas de API y estado; evita `any` salvo una frontera externa justificada y encapsulada.
- Usa `ref`/`reactive` para estado, `computed` para valores derivados y `watch` solo para efectos secundarios que no puedan expresarse mejor de otra forma.
- Mantén una única fuente de verdad para el estado. Evita copiar valores derivados a refs separados.
- Divide componentes cuando mejore la reutilización o claridad; no conviertas cada bloque visual en una abstracción innecesaria.

## API, sesión y validación

- Usa el cliente de `src/api.ts` y los tipos compartidos existentes para llamadas remotas.
- `src/session.ts` y `src/router.ts` son los puntos centrales para sesión y navegación. No dupliques tokens ni reglas de autorización en componentes.
- La interfaz puede mejorar la experiencia con validación previa, pero el backend es la autoridad para los datos y permisos.
- Maneja estados de carga, vacío, éxito y error en los flujos que consultan o guardan datos.
- No inventes endpoints, campos o estados; confirma el contrato con la API.

## Accesibilidad y experiencia

- Asocia etiquetas con controles, permite uso por teclado y comunica errores junto al campo correspondiente.
- Usa Vuetify de manera consistente con el tema y componentes existentes.
- Asegura que formularios y tablas sigan siendo utilizables en pantallas pequeñas; evita comunicar estados solo con color.

## Rendimiento y errores

- Prioriza una implementación sencilla. Usa `v-memo`, `markRaw`, `Suspense` o carga diferida solo ante una necesidad medida o un patrón existente.
- Usa `onErrorCaptured` para errores de subárbol cuando la interfaz pueda recuperarse; conserva un manejador global para fallos no controlados si el proyecto lo incorpora.
- Evita efectos secundarios en renderizado y observadores amplios sobre objetos grandes.

## Verificación

El script `npm run build` ejecuta `vue-tsc -b` y Vite. No hay actualmente un script de test frontend declarado; no afirmes que una prueba de interfaz se ejecutó si no fue añadida y ejecutada.
