"""
Añade hours_extra y hours_extra_festivo a payment_records (CR Código de Trabajo).
Uso: python scripts/migrate_hours_extra.py
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

        insp = inspect(db.engine)
        if "payment_records" not in insp.get_table_names():
            print("Tabla payment_records no existe.")
            return
        existing = [c["name"] for c in insp.get_columns("payment_records")]
        for col, col_def in [
            ("hours_extra", "FLOAT NULL"),
            ("hours_extra_festivo", "BOOLEAN DEFAULT FALSE"),
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
