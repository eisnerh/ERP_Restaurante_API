"""
Actualiza las posiciones de mesas que se solapan (varias en 0,0) para que se vean en la grilla.
Solo modifica franquiciados donde hay más de una mesa con la misma posición.
Uso: python scripts/fix_table_positions.py
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from extensions import db
from models import Table


def main():
    with app.app_context():
        updated = 0
        for franchisee_id, in db.session.query(Table.franchisee_id).distinct():
            tables = Table.query.filter_by(franchisee_id=franchisee_id).order_by(Table.number).all()
            if len(tables) <= 1:
                continue
            pos_count = defaultdict(int)
            for t in tables:
                px = getattr(t, "position_x", None) or 0
                py = getattr(t, "position_y", None) or 0
                pos_count[(px, py)] += 1
            if not any(c > 1 for c in pos_count.values()):
                continue
            for idx, t in enumerate(tables):
                col = idx % 4
                row = idx // 4
                t.position_x = col
                t.position_y = row
                updated += 1
        db.session.commit()
        print(f"Posiciones actualizadas: {updated} mesas.")
        if updated == 0:
            print("No había mesas con posiciones solapadas.")
