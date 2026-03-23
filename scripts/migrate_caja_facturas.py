"""
Migración: añade tablas y columnas para Caja, Facturas y Gastos operacionales.
Ejecutar: python scripts/migrate_caja_facturas.py
"""
import os
import sys

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from sqlalchemy import text


def migrate():
    with app.app_context():
        # Crear tablas nuevas si no existen
        db.create_all()
        print("Tablas creadas/actualizadas.")

        # Añadir columnas a orders si no existen (PostgreSQL)
        conn = db.engine.connect()
        try:
            # Verificar si la columna existe
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'payment_type'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_type VARCHAR(30)"))
                conn.commit()
                print("Columna orders.payment_type añadida.")
            else:
                print("Columna orders.payment_type ya existe.")

            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'cash_register_id'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE orders ADD COLUMN cash_register_id INTEGER REFERENCES cash_register_sessions(id)"))
                conn.commit()
                print("Columna orders.cash_register_id añadida.")
            else:
                print("Columna orders.cash_register_id ya existe.")

            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'orders' AND column_name = 'updated_at'
            """))
            if result.fetchone() is None:
                conn.execute(text("ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()
                print("Columna orders.updated_at añadida.")
            else:
                print("Columna orders.updated_at ya existe.")
        except Exception as e:
            print("Error en migración:", e)
            conn.rollback()
        finally:
            conn.close()
    print("Migración completada.")


if __name__ == "__main__":
    migrate()
