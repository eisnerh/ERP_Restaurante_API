"""
Script principal: crea la base de datos (PostgreSQL) y todas las tablas.
No borra datos existentes. Si tienes esquema antiguo (sin franchisee_id), ejecuta antes:
  python scripts/migrate_add_franchisee.py

Uso: python scripts/init_db.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        try:
            load_dotenv(env_path, encoding="utf-8")
        except (UnicodeDecodeError, UnicodeError):
            load_dotenv(env_path, encoding="latin-1")
except ImportError:
    pass


def create_database():
    """Crea la BD PostgreSQL si no existe."""
    url = os.environ.get("DATABASE_URL") or ""
    if "postgresql" in url or os.environ.get("PGHOST"):
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from create_database import create_postgres_db
        return create_postgres_db()
    return True


def create_tables():
    """Crea todas las tablas y un franquiciado por defecto si no existe."""
    from app import app
    from extensions import db
    from models import Franchisee

    with app.app_context():
        db.create_all()
        if Franchisee.query.count() == 0:
            default = Franchisee(
                code="001",
                name="Franquiciado Principal",
                active=True,
            )
            db.session.add(default)
            db.session.commit()
            print("   Franquiciado por defecto creado: Franquiciado Principal")
        from sqlalchemy import inspect
        insp = inspect(db.engine)
        return sorted(insp.get_table_names())


def main():
    print("1. Creando base de datos (si aplica)...")
    if not create_database():
        sys.exit(1)
    print("2. Creando tablas...")
    tables = create_tables()
    print(f"   Tablas creadas: {', '.join(tables)}")
    print("Listo. Puedes ejecutar: python app.py")
    print("Para importar inventario: python scripts/import_inventory_excel.py --franchisee-id 1")


if __name__ == "__main__":
    main()
