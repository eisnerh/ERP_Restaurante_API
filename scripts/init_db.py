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
        # Tipos de registro de planilla (empleado, mermas, por contrato, etc.)
        from models import PayrollEntryType
        if PayrollEntryType.query.count() == 0:
            for d in [
                {"code": "empleado", "name": "Empleado", "description": "Empleado en planilla", "display_order": 0, "hide_puesto": False},
                {"code": "mermas", "name": "Mermas", "description": "Gasto por mermas que se deduce del empleado", "display_order": 1, "hide_puesto": True},
                {"code": "por_contrato", "name": "Por contrato", "description": "Servicios por contrato", "display_order": 2, "hide_puesto": False},
                {"code": "servicios_profesionales", "name": "Servicios profesionales", "description": "Honorarios profesionales", "display_order": 3, "hide_puesto": False},
                {"code": "administrador", "name": "Administrador", "description": "Personal administrativo", "display_order": 4, "hide_puesto": False},
                {"code": "administrativo", "name": "Administrativo", "description": "Personal administrativo", "display_order": 5, "hide_puesto": False},
                {"code": "inventario", "name": "Inventario", "description": "Personal de inventario", "display_order": 6, "hide_puesto": False},
                {"code": "custom", "name": "Personalizado", "description": "Tipo personalizado", "display_order": 99, "hide_puesto": False},
            ]:
                db.session.add(PayrollEntryType(**d))
            db.session.commit()
            print("   Tipos de registro creados: Empleado, Mermas, Por contrato, Servicios profesionales, etc.")
        # Puesto Gerente Socio (salario 500 000)
        from models import Position
        if not Position.query.filter_by(name="Gerente Socio").first():
            db.session.add(Position(
                name="Gerente Socio",
                position_type="administrador",
                salario_base=500000,
                display_order=0,
                horas_por_dia=8,
                dias_por_semana=6,
            ))
            db.session.commit()
            print("   Puesto 'Gerente Socio' creado (₡ 500 000).")
        if Franchisee.query.count() == 0:
            casas = [
                ("001", "Casa Plaza San Carlos"),
                ("002", "Casa del Mirador"),
                ("003", "Casa del Brunch"),
                ("004", "Casa del Pan artesanal"),
                ("005", "Casa del Coronado"),
            ]
            for code, name in casas:
                db.session.add(Franchisee(code=code, name=name, active=True))
            db.session.commit()
            print("   Casas de Don Raul creadas: Plaza San Carlos, Mirador, Brunch, Pan artesanal, Coronado")
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
