"""
Añade salario_hora a employees y hours_worked, hourly_rate a payment_records.
Uso: python scripts/migrate_hourly_payment.py
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

        # salario_hora en employees
        if "employees" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("employees")]
            if "salario_hora" not in existing:
                try:
                    db.session.execute(text(
                        "ALTER TABLE employees ADD COLUMN salario_hora FLOAT NULL"
                    ))
                    db.session.commit()
                    print("  employees.salario_hora añadida.")
                except Exception as e:
                    db.session.rollback()
                    print("  Error salario_hora:", e)
            else:
                print("  employees.salario_hora ya existe.")

        # hours_worked y hourly_rate en payment_records
        if "payment_records" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("payment_records")]
            for col, col_type in [("hours_worked", "FLOAT"), ("hourly_rate", "FLOAT")]:
                if col not in existing:
                    try:
                        db.session.execute(text(
                            f"ALTER TABLE payment_records ADD COLUMN {col} {col_type} NULL"
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
