"""
Importa artículos y proveedores desde excel_docs/DATOS INVENTARIO.xlsx.
Crea proveedores, unidades de medida (si faltan) e ítems de inventario.

Uso:
  python scripts/import_inventory_excel.py --franchisee-id 1
  python scripts/import_inventory_excel.py --franchisee-id 1 --path "ruta/al/archivo.xlsx"
  python scripts/import_inventory_excel.py --franchisee-id 1 --replace   # Borra inventario del franquiciado antes de importar
"""
import argparse
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


DEFAULT_UNITS = [
    ("UND", "Unidad"),
    ("KG", "Kilogramo"),
    ("GR", "Gramo"),
    ("CJ", "Caja"),
]


def seed_units(db, Unit):
    """Crea unidades de medida si la tabla está vacía."""
    if Unit.query.count() > 0:
        return
    for symbol, name in DEFAULT_UNITS:
        db.session.add(Unit(symbol=symbol, name=name))
    db.session.flush()
    print("  Unidades de medida creadas: UND, KG, GR, CJ")


def get_or_create_supplier(db, Supplier, name, franchisee_id, phone=None, visit_day=None):
    """Devuelve el proveedor del franquiciado (crea si no existe)."""
    if not name or not str(name).strip() or not franchisee_id:
        return None
    name = str(name).strip()
    s = Supplier.query.filter_by(franchisee_id=franchisee_id, name=name).first()
    if s:
        if phone and not s.phone:
            s.phone = phone
        if visit_day and not s.visit_day:
            s.visit_day = visit_day
        return s
    s = Supplier(franchisee_id=franchisee_id, name=name, phone=phone or None, visit_day=visit_day or None)
    db.session.add(s)
    db.session.flush()
    return s


def main():
    parser = argparse.ArgumentParser(description="Importa inventario desde Excel")
    parser.add_argument("--franchisee-id", type=int, required=True, help="ID del franquiciado (obligatorio)")
    parser.add_argument("--path", default=None, help="Ruta al archivo Excel")
    parser.add_argument("--replace", action="store_true", help="Borrar inventario del franquiciado antes de importar")
    args = parser.parse_args()

    from utils.excel_inventory import parse_excel_inventory, get_default_excel_path
    path = args.path or get_default_excel_path()

    print(f"Leyendo: {path}")
    items_list, error = parse_excel_inventory(path)
    if error:
        print(f"Error: {error}")
        sys.exit(1)
    if not items_list:
        print("No se encontraron datos en la hoja INVENTARIO.")
        sys.exit(0)

    print(f"  {len(items_list)} filas encontradas.")

    from app import app
    from extensions import db
    from models import InventoryItem, Supplier, Unit
    from models.inventory import item_suppliers
    from sqlalchemy import delete

    with app.app_context():
        from models import Franchisee
        fid = args.franchisee_id
        if not db.session.get(Franchisee, fid):
            print(f"Error: No existe el franquiciado con ID {fid}.")
            sys.exit(1)
        print(f"Franquiciado ID {fid}")
        print("1. Creando unidades de medida (si faltan)...")
        seed_units(db, Unit)

        if args.replace:
            print("2. Borrando inventario del franquiciado...")
            item_ids = [i.id for i in InventoryItem.query.filter_by(franchisee_id=fid).all()]
            if item_ids:
                db.session.execute(delete(item_suppliers).where(item_suppliers.c.inventory_item_id.in_(item_ids)))
            InventoryItem.query.filter_by(franchisee_id=fid).delete()
            db.session.flush()

        print("3. Creando proveedores e ítems...")
        items_created = 0

        for d in items_list:
            supplier_ids = []
            for sup_name, phone, visit_day in [
                (d.get("supplier"), d.get("supplier_phone"), d.get("supplier_visit_day")),
                (d.get("supplier2"), None, None),
            ]:
                s = get_or_create_supplier(db, Supplier, sup_name, fid, phone, visit_day)
                if s and s.id not in supplier_ids:
                    supplier_ids.append(s.id)

            main_supplier = (d.get("supplier") or "").strip() or None
            if not main_supplier and supplier_ids:
                s0 = db.session.get(Supplier, supplier_ids[0])
                if s0:
                    main_supplier = s0.name

            item = InventoryItem(
                franchisee_id=fid,
                code=d.get("code"),
                area=d["area"],
                product_name=d["product_name"],
                unit=d.get("unit") or "UND",
                existence=d.get("existence", 0),
                stock=d.get("stock", 0),
                order_quantity=d.get("order_quantity"),
                supplier=main_supplier,
                responsible=d.get("responsible"),
            )
            db.session.add(item)
            db.session.flush()
            for sid in supplier_ids:
                db.session.execute(
                    item_suppliers.insert().values(
                        inventory_item_id=item.id,
                        supplier_id=sid,
                    )
                )
            items_created += 1

        db.session.commit()
        n_suppliers = Supplier.query.filter_by(franchisee_id=fid).count()
        print(f"\nListo. Proveedores: {n_suppliers}, Ítems: {items_created}")


if __name__ == "__main__":
    main()
