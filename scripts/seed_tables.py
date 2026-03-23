"""
Crea 5 mesas para el franquiciado indicado.
Uso: python scripts/seed_tables.py
     python scripts/seed_tables.py --franchisee-id 1
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from extensions import db
from models import Franchisee, Table


def main():
    parser = argparse.ArgumentParser(description="Crea 5 mesas por defecto")
    parser.add_argument("--franchisee-id", type=int, default=None, help="ID del franquiciado. Si no se indica, usa el primero disponible.")
    args = parser.parse_args()

    with app.app_context():
        if args.franchisee_id is not None:
            f = db.session.get(Franchisee, args.franchisee_id)
            if not f:
                print(f"Error: No existe el franquiciado con ID {args.franchisee_id}")
                sys.exit(1)
        else:
            f = Franchisee.query.filter_by(active=True).order_by(Franchisee.id).first()
            if not f:
                print("Error: No hay franquiciados en la base de datos. Ejecuta: python scripts/init_db.py")
                sys.exit(1)
            args.franchisee_id = f.id

        existing = Table.query.filter_by(franchisee_id=args.franchisee_id).count()
        if existing >= 5:
            print(f"Ya hay {existing} mesas para {f.name}. No se crean más.")
            sys.exit(0)

        # Crear mesas 1-5 (o las que falten) con posiciones para que se vean en la grilla
        created = 0
        for n in range(1, 6):
            if Table.query.filter_by(franchisee_id=args.franchisee_id, number=n).first():
                continue
            col = (n - 1) % 3
            row = (n - 1) // 3
            db.session.add(Table(
                franchisee_id=args.franchisee_id,
                number=n,
                capacity=4,
                position_x=col,
                position_y=row,
            ))
            created += 1

        db.session.commit()
        print(f"Creadas {created} mesas para {f.name}. Total: {existing + created}.")


if __name__ == "__main__":
    main()
