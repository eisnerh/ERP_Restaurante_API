"""
Añade la columna purchase_order_id a operational_expenses para vincular gastos con compras.
Uso: python scripts/migrate_expense_purchase_link.py
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
        cols = [c["name"] for c in insp.get_columns("operational_expenses")]
        if "purchase_order_id" in cols:
            print("La columna purchase_order_id ya existe.")
            return

        dialect = db.engine.dialect.name
        print(f"Conectado a: {dialect}")
        sql = (
            "ALTER TABLE operational_expenses ADD COLUMN purchase_order_id INTEGER REFERENCES purchase_orders(id)"
            if dialect == "postgresql"
            else "ALTER TABLE operational_expenses ADD COLUMN purchase_order_id INTEGER"
        )
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print("Columna purchase_order_id añadida correctamente.")
        except Exception as e:
            db.session.rollback()
            err = str(e).lower()
            if "already exists" in err or "duplicate column" in err or "exists" in err:
                print("La columna purchase_order_id ya existe.")
            else:
                print("Error:", e)
                raise


if __name__ == "__main__":
    main()
