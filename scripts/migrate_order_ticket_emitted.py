"""
Añade la columna ticket_emitted_at a orders para rastrear si el tiquete fue emitido.
Uso: python scripts/migrate_order_ticket_emitted.py
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
        cols = [c["name"] for c in insp.get_columns("orders")]
        if "ticket_emitted_at" in cols:
            print("La columna ticket_emitted_at ya existe.")
            return

        dialect = db.engine.dialect.name
        sql = (
            "ALTER TABLE orders ADD COLUMN ticket_emitted_at TIMESTAMP"
            if dialect == "postgresql"
            else "ALTER TABLE orders ADD COLUMN ticket_emitted_at DATETIME"
        )
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("Columna ticket_emitted_at añadida correctamente.")
        except Exception as e:
            db.session.rollback()
            err = str(e).lower()
            if "already exists" in err or "duplicate column" in err:
                print("La columna ticket_emitted_at ya existe.")
            else:
                print("Error:", e)
                raise


if __name__ == "__main__":
    main()
