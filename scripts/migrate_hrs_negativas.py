"""
Añade columna hrs_negativas a payroll_entries.
Uso: python scripts/migrate_hrs_negativas.py
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

        float_type = "DOUBLE PRECISION" if dialect == "postgresql" else "REAL"
        insp = inspect(db.engine)
        if "payroll_entries" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("payroll_entries")]
            if "hrs_negativas" in existing:
                print("  payroll_entries.hrs_negativas ya existe.")
            else:
                try:
                    db.session.execute(text(f"ALTER TABLE payroll_entries ADD COLUMN hrs_negativas {float_type}"))
                    db.session.commit()
                    print("  payroll_entries.hrs_negativas añadida.")
                except Exception as e:
                    db.session.rollback()
                    print("  Error hrs_negativas:", e)
        else:
            print("  Tabla payroll_entries no existe. Ejecuta init_db.py primero.")
        print("Migración completada.")


if __name__ == "__main__":
    main()
