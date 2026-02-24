"""
Crea todas las tablas del ERP en la base de datos.
Requiere que la base de datos ya exista (para PostgreSQL, ejecuta create_database.py antes).
Uso: python scripts/create_tables.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def main():
    from app import app
    from extensions import db

    with app.app_context():
        db.create_all()
        print("Tablas creadas correctamente.")
        # Listar tablas
        from sqlalchemy import inspect
        insp = inspect(db.engine)
        tables = insp.get_table_names()
        for t in sorted(tables):
            print(f"  - {t}")


if __name__ == "__main__":
    main()
