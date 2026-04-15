"""
Añade hacienda_p12_filename a app_settings si no existe.
Uso: python scripts/migrate_app_settings_hacienda_p12.py
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
    from sqlalchemy import text, inspect

    with app.app_context():
        insp = inspect(db.engine)
        cols = [c["name"] for c in insp.get_columns("app_settings")]
        if "hacienda_p12_filename" in cols:
            print("La columna hacienda_p12_filename ya existe.")
            return

        dialect = db.engine.dialect.name
        col = "VARCHAR(255)" if dialect == "postgresql" else "VARCHAR(255)"
        try:
            db.session.execute(text(f"ALTER TABLE app_settings ADD COLUMN hacienda_p12_filename {col}"))
            db.session.commit()
            print("Columna hacienda_p12_filename añadida correctamente.")
        except Exception as e:
            db.session.rollback()
            err = str(e).lower()
            if "already exists" in err or "duplicate column" in err:
                print("La columna hacienda_p12_filename ya existe.")
            else:
                print("Error:", e)
                raise


if __name__ == "__main__":
    main()
