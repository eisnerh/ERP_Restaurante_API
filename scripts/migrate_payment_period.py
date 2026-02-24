"""
Añade periodo_pago a employees y crea tabla payment_records.
Uso: python scripts/migrate_payment_period.py
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

        # periodo_pago en employees
        if "employees" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("employees")]
            if "periodo_pago" not in existing:
                try:
                    db.session.execute(text(
                        "ALTER TABLE employees ADD COLUMN periodo_pago VARCHAR(20) DEFAULT 'mensual'"
                    ))
                    db.session.commit()
                    print("  employees.periodo_pago añadida.")
                except Exception as e:
                    db.session.rollback()
                    print("  Error periodo_pago:", e)
            else:
                print("  employees.periodo_pago ya existe.")

        # Tabla payment_records
        from models import PaymentRecord
        db.create_all()
        if "payment_records" in insp.get_table_names():
            print("  Tabla payment_records lista.")

        print("Migración completada.")


if __name__ == "__main__":
    main()
