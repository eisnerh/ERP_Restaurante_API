"""
Quita el prefijo «Cleo Café — » de los nombres de categoría (menú cargado con seed_cleo_menu).

Uso: python scripts/strip_cleo_category_prefix.py
"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

PATTERN = re.compile(r"^Cleo\s+Café\s*[—\-]\s*", re.IGNORECASE)


def main():
    from app import app
    from extensions import db
    from models import Category

    with app.app_context():
        updated = 0
        for c in Category.query.all():
            if not c.name:
                continue
            new_name = PATTERN.sub("", c.name).strip()
            if new_name and new_name != c.name:
                c.name = new_name[:80]
                updated += 1
        if updated:
            db.session.commit()
        print(f"Listo: {updated} categorías actualizadas.")


if __name__ == "__main__":
    main()
