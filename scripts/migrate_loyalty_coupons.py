"""
Crea la tabla loyalty_coupons si no existe.
Uso: python scripts/migrate_loyalty_coupons.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    p = PROJECT_ROOT / ".env"
    if p.exists():
        try:
            load_dotenv(p, encoding="utf-8")
        except (UnicodeDecodeError, UnicodeError):
            load_dotenv(p, encoding="latin-1")
except ImportError:
    pass


def main():
    from sqlalchemy import text
    from app import app
    from extensions import db

    ddl = """
    CREATE TABLE IF NOT EXISTS loyalty_coupons (
        id SERIAL PRIMARY KEY,
        franchisee_id INTEGER NOT NULL REFERENCES franchisees(id),
        location_id INTEGER REFERENCES payroll_locations(id),
        invoice_number VARCHAR(64) NOT NULL,
        kind VARCHAR(20) NOT NULL,
        discount_percent NUMERIC(5, 2),
        discount_amount NUMERIC(12, 2),
        reward_description VARCHAR(500),
        public_token VARCHAR(64) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        redeemed_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT uq_loyalty_public_token UNIQUE (public_token)
    );
    CREATE INDEX IF NOT EXISTS ix_loyalty_franchisee_invoice
        ON loyalty_coupons (franchisee_id, invoice_number);
    CREATE INDEX IF NOT EXISTS ix_loyalty_public_token ON loyalty_coupons (public_token);
    """

    with app.app_context():
        url = str(db.engine.url)
        if "postgresql" not in url:
            print("Esta migración está pensada para PostgreSQL. Use db.create_all() con el modelo.")
            from models import LoyaltyCoupon  # noqa: F401
            db.create_all()
            print("db.create_all() ejecutado.")
            return
        with db.engine.connect() as conn:
            for stmt in ddl.strip().split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(text(s))
            conn.commit()
        print("Tabla loyalty_coupons lista.")


if __name__ == "__main__":
    main()
