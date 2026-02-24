"""
Migración: añade franchisee_id a tablas existentes (PostgreSQL).
Para bases de datos creadas antes de la funcionalidad de franquiciados.

Uso: python scripts/migrate_add_franchisee.py
"""
import os
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

        engine = db.engine
        insp = inspect(engine)

        # Tablas que necesitan franchisee_id
        tables_columns = {
            "suppliers": "franchisee_id",
            "inventory_items": "franchisee_id",
            "clients": "franchisee_id",
            "categories": "franchisee_id",
            "tables": "franchisee_id",
            "purchase_orders": "franchisee_id",
            "payroll_locations": "franchisee_id",
            "payslips": "franchisee_id",
            "inventory_alerts": "franchisee_id",
            "app_settings": "franchisee_id",
        }

        # Crear tabla franchisees si no existe
        if "franchisees" not in insp.get_table_names():
            print("Creando tabla franchisees...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE franchisees (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR(20),
                        name VARCHAR(120) NOT NULL,
                        address VARCHAR(255),
                        phone VARCHAR(50),
                        email VARCHAR(120),
                        active BOOLEAN DEFAULT TRUE
                    )
                """))
                conn.commit()
            print("   Tabla franchisees creada.")

        # Crear franquiciado por defecto si no hay ninguno
        with engine.connect() as conn:
            r = conn.execute(text("SELECT COUNT(*) FROM franchisees")).scalar()
            if r == 0:
                conn.execute(text("""
                    INSERT INTO franchisees (code, name, active) VALUES ('001', 'Franquiciado Principal', TRUE)
                """))
                conn.commit()
                print("   Franquiciado por defecto creado.")

        default_fid = 1

        for table, col in tables_columns.items():
            if table not in insp.get_table_names():
                continue
            cols = [c["name"] for c in insp.get_columns(table)]
            if col in cols:
                print(f"   {table}: ya tiene {col}")
                continue
            print(f"Añadiendo {col} a {table}...")
            try:
                if table == "app_settings":
                    add_sql = f"ALTER TABLE {table} ADD COLUMN {col} INTEGER NULL"
                else:
                    add_sql = f"ALTER TABLE {table} ADD COLUMN {col} INTEGER NOT NULL DEFAULT 1"
                with engine.connect() as conn:
                    conn.execute(text(add_sql))
                    conn.commit()
                if table != "app_settings":
                    with engine.connect() as conn:
                        conn.execute(text(f"UPDATE {table} SET {col} = {default_fid} WHERE {col} IS NULL"))
                        conn.commit()
                print(f"   {table}: {col} añadido.")
            except Exception as e:
                print(f"   Error en {table}: {e}")

        print("\nMigración completada. Ejecuta: python scripts/import_inventory_excel.py --franchisee-id 1")


if __name__ == "__main__":
    main()
