"""
Migración: añade columnas para Arqueo Z en cash_register_sessions.
Ejecutar: python scripts/migrate_arqueo_z.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from sqlalchemy import text


def migrate():
    with app.app_context():
        conn = db.engine.connect()
        cols = [
            ("arqueo_number", "INTEGER"),
            ("declared_json", "TEXT"),
            ("cash_breakdown_json", "TEXT"),
            ("cash_in", "NUMERIC(12,2)"),
            ("cash_out", "NUMERIC(12,2)"),
            ("retirada", "NUMERIC(12,2)"),
            ("new_fianza", "NUMERIC(12,2)"),
        ]
        for col_name, col_type in cols:
            try:
                r = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'cash_register_sessions' AND column_name = :name
                """), {"name": col_name})
                if r.fetchone() is None:
                    conn.execute(text(f"ALTER TABLE cash_register_sessions ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Columna {col_name} añadida.")
            except Exception as e:
                print(f"Error en {col_name}:", e)
                conn.rollback()
        conn.close()
    print("Migración Arqueo Z completada.")


if __name__ == "__main__":
    migrate()
