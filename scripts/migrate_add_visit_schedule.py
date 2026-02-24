"""
Añade la columna visit_schedule a suppliers si no existe.
Uso: python scripts/migrate_add_visit_schedule.py
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
        from sqlalchemy import text
        dialect = db.engine.dialect.name
        print(f"Conectado a: {dialect}")
        col_type = "VARCHAR(40)" if dialect == "postgresql" else "VARCHAR(40)"
        try:
            db.session.execute(text(f"ALTER TABLE suppliers ADD COLUMN visit_schedule {col_type}"))
            db.session.commit()
            print("Columna visit_schedule añadida correctamente.")
        except Exception as e:
            db.session.rollback()
            err = str(e).lower()
            if "already exists" in err or "duplicate column" in err or "exists" in err:
                print("La columna visit_schedule ya existe.")
            else:
                print("Error:", e)


if __name__ == "__main__":
    main()
