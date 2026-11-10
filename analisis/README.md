# Análisis y especificaciones

**Versión de la documentación:** 1.3.0 · **Revisada:** 2026-11-05

Este directorio reúne casos de uso, reglas de negocio, criterios de aceptación y evidencia registrada. El estado de cada documento describe la última verificación escrita allí; no implica que las pruebas se hayan repetido en la revisión actual.

## Casos de uso

| Identificador | Caso | Documento |
| --- | --- | --- |
| UC-CV-01 | Registrar cliente | [README del caso de uso](../README_UC-CV-01_Registrar_Cliente.md) |
| UC-06 | Registrar vehículo | [Especificación](UC06_registrar_vehiculo.md) |
| UC-07 | Consultar vehículo | [Especificación](UC07_consultar_vehiculo.md) |
| UC-08 | Actualizar vehículo | [Especificación](UC08_actualizar_vehiculo.md) |
| UC-SEG-01 | Crear roles | [Especificación](FASE_CREAR_ROLES.md) |
| UC-SEG-02 | Administrar roles | [Especificación](FASE_ADMINISTRAR_ROLES.md) |
| UC-TM-01 | Dar de alta un taller | [Especificación](ALTA_DEL_TALLER.md) |
| UC-TM-02 | Asociar un cliente a un taller activo | [Especificación](FASE_ASOCIAR_CLIENTE_TALLER.md) |

## Diagramas y artefactos

Los diagramas Mermaid, modelos relacionales y especificaciones Archify se encuentran en `analisis/diagramas/`. Abre el caso de uso correspondiente para sus nombres y vínculos. Actualiza los diagramas junto con los cambios de flujo o datos; no los tomes como evidencia de que una ruta está implementada.

## Puesta en marcha de la fase de roles, talleres y catálogo postal

Estos pasos corresponden a esa fase específica; no son un instalador universal de todas las migraciones.

### 1. Aplicar migraciones requeridas

En una base existente, confirma primero el estado de su esquema y aplica cada migración pendiente una sola vez con una cuenta autorizada. Por ejemplo, la migración de roles, talleres y catálogo postal de esta fase:

```powershell
cd C:\TallerMecanico
Get-Content -Raw .\database\migrations\002_roles_workshops_postal.sql | mysql -u root -p
```

`database/init.sql` es para una base nueva; no lo ejecutes sobre una base ya inicializada. La cuenta de aplicación no debe tener permisos DDL para operar normalmente.

### 2. Configurar y arrancar backend

```powershell
cd C:\TallerMecanico\backend
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py" -v
uvicorn app.main:app --reload
```

Configura `backend/.env` a partir de `.env.example`. Las pruebas y sus dependencias disponibles pueden variar por entorno; reporta el resultado real de la ejecución.

### 3. Cargar o actualizar el catálogo postal

Descarga el TXT delimitado por `|` desde [Correos de México/SEPOMEX](https://www.correosdemexico.gob.mx/sslservicios/consultacp/CodigoPostal_Exportar.aspx) y ejecútalo con el importador:

```powershell
cd C:\TallerMecanico\backend
python -m app.import_postal_codes "C:\ruta\al\CodigoPostal_Exportar.txt"
```

El importador reemplaza el catálogo dentro de una transacción y debe revertir si no encuentra registros válidos. La fuente y el volumen importado pueden cambiar; consulta el resultado de la ejecución más reciente.

### 4. Arrancar frontend

```powershell
cd C:\TallerMecanico\frontend
npm install
npm run dev
```

## Evidencia histórica

La versión anterior de esta guía registró un build de frontend correcto, compilación Python correcta y ocho pruebas aprobadas con una omitida por dependencia ausente. También registró una migración y carga postal realizadas en el entorno de aquella ejecución. Estos datos son antecedentes, no una verificación del checkout actual.
