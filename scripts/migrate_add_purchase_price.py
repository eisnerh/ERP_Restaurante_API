"""
Añade la columna purchase_price a inventory_items si no existe.
Uso: python scripts/migrate_add_purchase_price.py
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
        col_type = "DOUBLE PRECISION" if dialect == "postgresql" else "REAL"
        try:
            db.session.execute(text(f"ALTER TABLE inventory_items ADD COLUMN purchase_price {col_type}"))
            db.session.commit()
            print("Columna purchase_price añadida correctamente.")
        except Exception as e:
            db.session.rollback()
            err = str(e).lower()
            if "already exists" in err or "duplicate column" in err or "exists" in err:
                print("La columna purchase_price ya existe.")
            else:
                print("Error:", e)
                print("\nSi usas PostgreSQL, ejecuta manualmente:")
                print("  psql -U postgres -d restaurant_erp -f scripts/add_purchase_price.sql")


if __name__ == "__main__":
    main()
