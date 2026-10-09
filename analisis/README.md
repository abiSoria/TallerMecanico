# Documentación de análisis

## Casos de uso

- [UC-SEG-01 — Crear roles](FASE_CREAR_ROLES.md)
- [UC-SEG-02 — Administrar roles](FASE_ADMINISTRAR_ROLES.md)
- [UC-TM-01 — Dar de alta un taller mecánico](ALTA_DEL_TALLER.md)

## Diagramas

Cada proceso tiene diagramas Mermaid de actividad y secuencia en `diagramas/`; el modelo relacional común está en `diagramas/modelo-datos.mmd`. También se conservan las especificaciones de workflow Archify (`*.workflow.json`).

# Puesta en marcha de esta fase

## 1. Aplicar la migración

En una instalación existente, ejecutar una sola vez desde PowerShell con credenciales de MySQL que puedan alterar tablas:

```powershell
cd C:\TallerMecanico
Get-Content -Raw .\database\migrations\002_roles_workshops_postal.sql | mysql -u root -p
```

No ejecutar `database/init.sql` sobre una base existente: ese archivo es para una base nueva. La cuenta `taller_app` conserva las operaciones de lectura/escritura; no requiere permisos de DDL durante el uso diario.

## 2. Instalar y arrancar backend

```powershell
cd C:\TallerMecanico\backend
..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py" -v
uvicorn app.main:app --reload
```

Configurar primero `backend/.env` con `DATABASE_URL` y `JWT_SECRET_KEY` según `backend/.env.example`. `python-multipart` atiende el formulario y Pillow decodifica la imagen para verificar el formato real.

## 3. Cargar y actualizar el catálogo postal

Descargar el TXT nacional de [Correos de México/SEPOMEX](https://www.correosdemexico.gob.mx/sslservicios/consultacp/CodigoPostal_Exportar.aspx), delimitado por `|`, y ejecutar:

```powershell
cd C:\TallerMecanico\backend
python -m app.import_postal_codes "C:\ruta\al\CodigoPostal_Exportar.txt"
```

La carga sustituye el catálogo dentro de una transacción; si no encuentra filas válidas, revierte sin vaciar la tabla.

## 4. Arrancar frontend

En otra terminal:

```powershell
cd C:\TallerMecanico\frontend
npm install
npm run dev
```

Entrar al panel como Administrador para **Administrar roles** y **Dar de alta taller**; Administrador y Recepcionista pueden registrar talleres.

## Estado de verificación de esta entrega

- El build de producción de Vue/Vite se ejecutó correctamente.
- La compilación de bytecode Python se ejecutó correctamente.
- En la suite SQLite, 8 pruebas pasaron y 1 se omitió: faltó Pillow para verificar una imagen válida justo en el límite de 10 MiB. El `.venv` también carece de `python-multipart`; para ejecutar esta suite en la sesión se usó el paquete global disponible. El backend normal requiere `pip install -r requirements.txt`. PyPI no resolvió al intentar instalar Pillow en esta sesión.
- La migración de roles y talleres se aplicó manualmente en la base usada por la aplicación. En otras instalaciones, verificar el esquema antes de ejecutarla; requiere permisos DBA. El catálogo postal local se cargó desde el TXT SEPOMEX.
- Las configuraciones Archify (`*.workflow.json`) y los diagramas Mermaid quedan en `analisis/diagramas`. La exportación Archify a HTML quedó pendiente por `EPERM` al resolver con seguridad la ruta de salida en este entorno.
