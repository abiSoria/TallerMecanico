"""Importa a la base local el TXT pipe-delimited de Correos de México/SEPOMEX."""
import argparse
import csv
import io
import unicodedata
from pathlib import Path

from sqlalchemy import delete, insert

from app.database import SessionLocal
from app.models import PostalCode


def _field(row: dict[str, str], *names: str) -> str:
    normalized = {key.strip().lstrip("\ufeff").casefold(): value for key, value in row.items() if key}
    for name in names:
        value = normalized.get(name.casefold())
        if value is not None:
            return value.strip()
    return ""


def _identity_part(value: str) -> str:
    """Match the case- and accent-insensitive MySQL catalog collation."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def load_rows(path: Path, counts: dict[str, int]):
    raw = path.read_bytes()
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = raw.decode("cp1252")
    lines = decoded.splitlines()
    header_at = next((index for index, line in enumerate(lines)
                      if "d_codigo" in {field.strip().lstrip("\ufeff").casefold() for field in line.split("|")}
                      and "d_asenta" in {field.strip().lstrip("\ufeff").casefold() for field in line.split("|")}), None)
    if header_at is None:
        raise ValueError("No se reconocieron encabezados SEPOMEX en el TXT.")
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_at:])), delimiter="|")
    seen = set()
    for row in reader:
        code = _field(row, "d_codigo", "codigo postal", "código postal")
        neighborhood = _field(row, "d_asenta", "asentamiento", "colonia")
        municipality = _field(row, "d_mnpio", "municipio", "alcaldia", "alcaldía")
        state = _field(row, "d_estado", "estado")
        if len(code) == 4 and code.isdigit():
            code = "0" + code
        key = tuple(_identity_part(value) for value in (code, neighborhood, municipality, state))
        if len(code) == 5 and code.isdigit() and neighborhood and municipality and state and key not in seen:
            seen.add(key)
            yield {"postal_code": code, "neighborhood": neighborhood[:120], "municipality": municipality[:120], "state": state[:100]}
        else:
            counts["skipped"] += 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa catálogo SEPOMEX desde TXT delimitado por |.")
    parser.add_argument("file", type=Path, help="Ruta al archivo TXT descargado de Correos de México")
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error("No se encontró el archivo especificado.")
    db = SessionLocal()
    imported = 0
    counts = {"skipped": 0}
    try:
        with db.begin():
            db.execute(delete(PostalCode))
            batch = []
            for row in load_rows(args.file, counts):
                batch.append(row)
                if len(batch) >= 2000:
                    result = db.execute(insert(PostalCode), batch)
                    imported += len(batch)
                    batch.clear()
            if batch:
                db.execute(insert(PostalCode), batch)
                imported += len(batch)
            if imported == 0:
                raise ValueError("El archivo no contenía filas postales válidas; se revirtió la importación.")
        print(f"Catálogo postal actualizado: {imported} filas. Filas inválidas o repetidas omitidas: {counts['skipped']}.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
