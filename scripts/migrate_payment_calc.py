"""
Añade horas_por_dia a employees y days_worked, include_sundays a payment_records.
Uso: python scripts/migrate_payment_calc.py
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

        insp = inspect(db.engine)

        # horas_por_dia en employees
        if "employees" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("employees")]
            if "horas_por_dia" not in existing:
                try:
                    db.session.execute(text(
                        "ALTER TABLE employees ADD COLUMN horas_por_dia FLOAT DEFAULT 8"
                    ))
                    db.session.commit()
                    print("  employees.horas_por_dia añadida.")
                except Exception as e:
                    db.session.rollback()
                    print("  Error horas_por_dia:", e)
            else:
                print("  employees.horas_por_dia ya existe.")

        # days_worked y include_sundays en payment_records
        if "payment_records" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("payment_records")]
            for col, col_def in [
                ("days_worked", "FLOAT NULL"),
                ("include_sundays", "BOOLEAN DEFAULT FALSE"),
            ]:
                if col not in existing:
                    try:
                        db.session.execute(text(
                            f"ALTER TABLE payment_records ADD COLUMN {col} {col_def}"
                        ))
                        db.session.commit()
                        print(f"  payment_records.{col} añadida.")
                    except Exception as e:
                        db.session.rollback()
                        print(f"  Error {col}:", e)
                else:
                    print(f"  payment_records.{col} ya existe.")

        print("Migración completada.")


if __name__ == "__main__":
    main()
