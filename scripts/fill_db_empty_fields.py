"""
Rellena campos vacios en la base de datos con datos de prueba.
Uso: python scripts/fill_db_empty_fields.py
"""
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

TELEFONOS = ["2222-3333", "8888-9999", "7777-1234", "5555-6789", "3333-4444", "6666-1111"]
DIAS_VISITA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]
RESPONSABLES = ["Arlen Nuñez", "Maria Lopez", "Carlos Perez", "Ana Garcia", "Luis Martinez"]
EMAILS = ["contacto@proveedor.com", "ventas@empresa.com", "info@distribuidor.com"]


def _empty(val):
    if val is None:
        return True
    s = str(val).strip()
    return s == "" or s.lower() in ("none", "null")


def main():
    from app import app
    from extensions import db
    from models import InventoryItem, Supplier, Client, Category, Franchisee, Unit

    with app.app_context():
        updated = {}

        # InventoryItem: order_quantity, responsible
        items = InventoryItem.query.all()
        count_order = count_resp = 0
        for it in items:
            if _empty(it.order_quantity) and it.stock and float(it.stock) > 0:
                it.order_quantity = max(1, int(float(it.stock) * 0.5))
                count_order += 1
            if _empty(it.responsible):
                it.responsible = random.choice(RESPONSABLES)
                count_resp += 1
        updated["inventory_order_quantity"] = count_order
        updated["inventory_responsible"] = count_resp

        # Supplier: phone, contact, visit_day
        suppliers = Supplier.query.all()
        count_sphone = count_contact = count_visit = 0
        for s in suppliers:
            if _empty(s.phone):
                s.phone = random.choice(TELEFONOS)
                count_sphone += 1
            if _empty(s.contact):
                s.contact = "Contacto ventas"
                count_contact += 1
            if _empty(s.visit_day):
                s.visit_day = random.choice(DIAS_VISITA)
                count_visit += 1
        updated["supplier_phone"] = count_sphone
        updated["supplier_contact"] = count_contact
        updated["supplier_visit_day"] = count_visit

        # Client: tax_id, email, phone, address, notes
        clients = Client.query.all()
        count_tax = count_email = count_cphone = count_addr = count_notes = 0
        for c in clients:
            if _empty(c.tax_id):
                c.tax_id = f"3-{random.randint(100, 999)}-{random.randint(100, 999)}"
                count_tax += 1
            if _empty(c.email):
                c.email = f"cliente{c.id}@ejemplo.com"
                count_email += 1
            if _empty(c.phone):
                c.phone = random.choice(TELEFONOS)
                count_cphone += 1
            if _empty(c.address):
                c.address = f"Calle {random.randint(1, 100)} # {random.randint(1, 50)}"
                count_addr += 1
            if _empty(c.notes):
                c.notes = "Cliente preferencial"
                count_notes += 1
        updated["client_tax_id"] = count_tax
        updated["client_email"] = count_email
        updated["client_phone"] = count_cphone
        updated["client_address"] = count_addr
        updated["client_notes"] = count_notes

        # Category: description
        categories = Category.query.all()
        count_desc = 0
        for cat in categories:
            if _empty(cat.description):
                cat.description = f"Categoria {cat.name}"
                count_desc += 1
        updated["category_description"] = count_desc

        # Franchisee: address, phone, email
        franchisees = Franchisee.query.all()
        count_faddr = count_fphone = count_femail = 0
        for f in franchisees:
            if _empty(f.address):
                f.address = "Sucursal principal"
                count_faddr += 1
            if _empty(f.phone):
                f.phone = "2222-0000"
                count_fphone += 1
            if _empty(f.email):
                f.email = f"franquicia{f.id}@ejemplo.com"
                count_femail += 1
        updated["franchisee_address"] = count_faddr
        updated["franchisee_phone"] = count_fphone
        updated["franchisee_email"] = count_femail

        # Unit: name
        units = Unit.query.all()
        unit_names = {"UND": "Unidad", "KG": "Kilogramo", "GR": "Gramo", "CJ": "Caja", "BOT": "Botella", "L": "Litro"}
        count_uname = 0
        for u in units:
            if _empty(u.name):
                u.name = unit_names.get(u.symbol, u.symbol)
                count_uname += 1
        updated["unit_name"] = count_uname

        db.session.commit()

        print("Campos vacios rellenados:")
        print("  Inventario - Pedido sugerido:", count_order)
        print("  Inventario - Responsable:", count_resp)
        print("  Proveedores - Telefono:", count_sphone)
        print("  Proveedores - Contacto:", count_contact)
        print("  Proveedores - Dia visita:", count_visit)
        print("  Clientes - Cedula/RUC:", count_tax)
        print("  Clientes - Email:", count_email)
        print("  Clientes - Telefono:", count_cphone)
        print("  Clientes - Direccion:", count_addr)
        print("  Clientes - Notas:", count_notes)
        print("  Categorias - Descripcion:", count_desc)
        print("  Franquiciados - Direccion:", count_faddr)
        print("  Franquiciados - Telefono:", count_fphone)
        print("  Franquiciados - Email:", count_femail)
        print("  Unidades - Nombre:", count_uname)
        print("\nListo.")


if __name__ == "__main__":
    main()
