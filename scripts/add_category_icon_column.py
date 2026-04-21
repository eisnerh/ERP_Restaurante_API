"""Añade columna categories.icon (PostgreSQL). Uso: python scripts/add_category_icon_column.py"""
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
    from sqlalchemy import inspect, text
    from app import app
    from extensions import db

    with app.app_context():
        insp = inspect(db.engine)
        if "categories" not in insp.get_table_names():
            print("No existe tabla categories.")
            sys.exit(1)
        cols = [c["name"] for c in insp.get_columns("categories")]
        if "icon" in cols:
            print("La columna categories.icon ya existe.")
            return
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE categories ADD COLUMN icon VARCHAR(64)"))
            conn.commit()
        print("Columna icon añadida correctamente.")


if __name__ == "__main__":
    main()
