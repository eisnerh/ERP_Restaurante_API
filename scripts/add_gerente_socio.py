"""
Añade el puesto "Gerente Socio" con salario 500 000 si no existe.
Para instalaciones que ya tenían la BD antes de esta actualización.

Uso: python scripts/add_gerente_socio.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    from app import app
    from models import Position

    with app.app_context():
        from extensions import db
        if Position.query.filter_by(name="Gerente Socio").first():
            print("El puesto 'Gerente Socio' ya existe.")
        else:
            db.session.add(Position(
                name="Gerente Socio",
                position_type="administrador",
                salario_base=500000,
                display_order=0,
                horas_por_dia=8,
                dias_por_semana=6,
            ))
            db.session.commit()
            print("Puesto 'Gerente Socio' creado (₡ 500 000).")
