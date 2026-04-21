"""Rellena icon según el nombre de categoría. Uso: python scripts/backfill_category_icons.py"""
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
    from models import Category
    from utils.category_icon import suggest_icon_for_category_name

    with app.app_context():
        n = 0
        for c in Category.query.all():
            if c.icon:
                continue
            c.icon = suggest_icon_for_category_name(c.name)
            n += 1
        if n:
            db.session.commit()
        print(f"Listo: {n} categorías con icono asignado.")


if __name__ == "__main__":
    main()
