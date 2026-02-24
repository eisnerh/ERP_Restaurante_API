"""
Crea la tabla employees y añade employee_id a payroll_entries y payslips.
Uso: python scripts/migrate_add_employees.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def main():
    from app import app
    from extensions import db

    with app.app_context():
        from sqlalchemy import text, inspect
        dialect = db.engine.dialect.name
        print(f"Conectado a: {dialect}")

        # Crear tabla employees si no existe
        db.create_all()

        for table, col in [("payroll_entries", "employee_id"), ("payslips", "employee_id")]:
            try:
                insp = inspect(db.engine)
                if table not in insp.get_table_names():
                    continue
                cols = [c["name"] for c in insp.get_columns(table)]
                if col in cols:
                    print(f"  {table}.{col} ya existe.")
                else:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} INTEGER"))
                    db.session.commit()
                    print(f"  {table}.{col} añadida.")
            except Exception as e:
                db.session.rollback()
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  {table}.{col} ya existe.")
                else:
                    print(f"  Error en {table}:", e)

        print("Migración completada.")


if __name__ == "__main__":
    main()
