"""
Crea la tabla payroll_entry_types y carga tipos por defecto.
Ejecutar: python scripts/migrate_entry_types.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", encoding="utf-8")
except Exception:
    pass


DEFAULT_TYPES = [
    {"code": "empleado", "name": "Empleado", "description": "Empleado en planilla", "display_order": 0, "hide_puesto": False},
    {"code": "mermas", "name": "Mermas", "description": "Gasto por mermas que se deduce del empleado", "display_order": 1, "hide_puesto": True},
    {"code": "por_contrato", "name": "Por contrato", "description": "Servicios por contrato", "display_order": 2, "hide_puesto": False},
    {"code": "servicios_profesionales", "name": "Servicios profesionales", "description": "Honorarios profesionales", "display_order": 3, "hide_puesto": False},
    {"code": "administrador", "name": "Administrador", "description": "Cargo administrativo", "display_order": 4, "hide_puesto": False},
    {"code": "administrativo", "name": "Administrativo", "description": "Personal administrativo", "display_order": 5, "hide_puesto": False},
    {"code": "inventario", "name": "Inventario", "description": "Personal de inventario", "display_order": 6, "hide_puesto": False},
    {"code": "custom", "name": "Personalizado", "description": "Otro tipo personalizado", "display_order": 99, "hide_puesto": False},
]


def main():
    from app import app
    from extensions import db
    from models import PayrollEntryType

    with app.app_context():
        db.create_all()
        for d in DEFAULT_TYPES:
            existing = PayrollEntryType.query.filter_by(code=d["code"]).first()
            if not existing:
                t = PayrollEntryType(**d)
                db.session.add(t)
                print(f"  Creado tipo: {d['name']} ({d['code']})")
        db.session.commit()
    print("Migración completada. Tipos de registro listos.")


if __name__ == "__main__":
    main()
