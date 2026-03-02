"""
Importación desde Excel vía upload. Usado por Configuración.
Cada función recibe file_bytes (bytes del archivo) y opciones, retorna (created_count, error).
"""
import io
import re
import tempfile
import os
from datetime import datetime


def _to_float(val, default=None):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", ".")
    if not s:
        return default
    m = re.match(r"^([-+]?\d*\.?\d+)", s)
    return float(m.group(1)) if m else default


def _to_date(val):
    if val is None:
        return None
    if hasattr(val, "date"):
        return val.date()
    s = str(val).strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _parse_si_no(val):
    if val is None:
        return True
    s = str(val).strip().upper()
    return s in ("SI", "S", "1", "TRUE", "YES", "X")


# --- Inventario ---
def import_inventario(file_bytes, franchisee_id, replace=False):
    from utils.excel_inventory import parse_excel_inventory
    from models import InventoryItem
    from models.inventory import item_suppliers
    from routes.inventory import _get_or_create_supplier_id, _set_item_suppliers
    from extensions import db

    items_list, error = parse_excel_inventory(io.BytesIO(file_bytes))
    if error:
        return 0, error
    if not franchisee_id:
        return 0, "Selecciona un franquiciado"

    if replace:
        from sqlalchemy import delete
        db.session.execute(delete(item_suppliers))
        InventoryItem.query.filter_by(franchisee_id=franchisee_id).delete()

    created = 0
    for d in items_list:
        supplier_ids = []
        for sup_name in (d.get("supplier"), d.get("supplier2")):
            sid = _get_or_create_supplier_id(sup_name, franchisee_id)
            if sid and sid not in supplier_ids:
                supplier_ids.append(sid)
        main_supplier = (d.get("supplier") or "").strip() or None
        if not main_supplier and supplier_ids:
            from models import Supplier
            s0 = db.session.get(Supplier, supplier_ids[0])
            if s0:
                main_supplier = s0.name
        item = InventoryItem(
            franchisee_id=franchisee_id,
            code=d.get("code"),
            area=d.get("area", "cocina"),
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
        _set_item_suppliers(item, supplier_ids, franchisee_id)
        created += 1
    db.session.commit()
    return created, None


# --- Planilla ubicaciones y registros ---
def import_planilla_ubicaciones(file_bytes, franchisee_id, replace_all=False, period_date=None):
    from routes.payroll import _parse_payroll_excel
    from models import PayrollLocation, PayrollEntry
    from extensions import db
    from datetime import date

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        locations_list, entries_list, err = _parse_payroll_excel(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if err:
        return 0, 0, err
    if not franchisee_id:
        return 0, 0, "Selecciona un franquiciado"

    period_date = period_date or date.today()

    if replace_all:
        loc_ids = [l.id for l in PayrollLocation.query.filter_by(franchisee_id=franchisee_id).all()]
        PayrollEntry.query.filter(PayrollEntry.location_id.in_(loc_ids)).delete(synchronize_session=False)
        PayrollLocation.query.filter_by(franchisee_id=franchisee_id).delete()
        db.session.commit()

    name_to_id = {}
    for loc_dict in locations_list:
        name = loc_dict["name"]
        loc = PayrollLocation.query.filter_by(franchisee_id=franchisee_id, name=name).first()
        if not loc:
            loc = PayrollLocation(franchisee_id=franchisee_id, name=name, display_order=loc_dict.get("display_order", 0))
            db.session.add(loc)
            db.session.flush()
        name_to_id[name] = loc.id

    created = 0
    for e in entries_list:
        loc_id = name_to_id.get(e["location_name"])
        if not loc_id:
            continue
        entry = PayrollEntry(
            location_id=loc_id,
            period_date=period_date,
            employee_name=e["employee_name"],
            entry_type=e.get("entry_type", "empleado"),
            code=e.get("code"),
            hrs_extra=e.get("hrs_extra"),
            creditos_comida=e.get("creditos_comida") or 0,
            vale_efectivo=e.get("vale_efectivo"),
            ccss_rebajos=e.get("ccss_rebajos"),
            dia_psg=e.get("dia_psg"),
            incapacidades=e.get("incapacidades"),
            numero_cuenta=e.get("numero_cuenta"),
            fecha_ingreso=e.get("fecha_ingreso"),
            notes=e.get("notes"),
        )
        db.session.add(entry)
        created += 1
    db.session.commit()
    return len(locations_list), created, None


# --- Casas (Franquiciados) ---
def import_casas(file_bytes):
    import openpyxl
    from models import Franchisee
    from extensions import db

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    if not ws:
        return 0, "No hay hojas en el archivo"
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[1] if len(row) > 1 else None) or ""
        if not str(nombre).strip():
            continue
        codigo = str(row[0]).strip() if len(row) > 0 and row[0] else None
        direccion = str(row[2]).strip() if len(row) > 2 and row[2] else None
        telefono = str(row[3]).strip() if len(row) > 3 and row[3] else None
        email = str(row[4]).strip() if len(row) > 4 and row[4] else None
        activo = _parse_si_no(row[5]) if len(row) > 5 else True
        if Franchisee.query.filter_by(name=nombre.strip()).first():
            continue
        f = Franchisee(
            code=codigo or None,
            name=nombre.strip(),
            address=direccion or None,
            phone=telefono or None,
            email=email or None,
            active=activo,
        )
        db.session.add(f)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Menú (Categorías + Platos) ---
def import_menu(file_bytes, franchisee_id):
    import openpyxl
    from models import Category, Dish
    from extensions import db

    if not franchisee_id:
        return 0, "Selecciona un franquiciado"

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    cat_by_name = {}
    cats_created = 0
    dishes_created = 0
    for ws_name in wb.sheetnames:
        ws = wb[ws_name]
        if not ws:
            continue
        if "categoria" in ws_name.lower():
            for row in ws.iter_rows(min_row=2, values_only=True):
                row = list(row) if row else []
                nombre = (row[0] if len(row) > 0 else None) or ""
                if not str(nombre).strip():
                    continue
                desc = str(row[1]).strip() if len(row) > 1 and row[1] else None
                cat = Category.query.filter_by(franchisee_id=franchisee_id, name=nombre.strip()).first()
                if not cat:
                    cat = Category(franchisee_id=franchisee_id, name=nombre.strip(), description=desc)
                    db.session.add(cat)
                    db.session.flush()
                    cats_created += 1
                cat_by_name[nombre.strip()] = cat
        elif "plato" in ws_name.lower():
            for row in ws.iter_rows(min_row=2, values_only=True):
                row = list(row) if row else []
                nombre = (row[0] if len(row) > 0 else None) or ""
                if not str(nombre).strip():
                    continue
                desc = str(row[1]).strip() if len(row) > 1 and row[1] else None
                precio = _to_float(row[2]) if len(row) > 2 else 0
                cat_nombre = str(row[3]).strip() if len(row) > 3 and row[3] else None
                disponible = _parse_si_no(row[4]) if len(row) > 4 else True
                cat = cat_by_name.get(cat_nombre) if cat_nombre else None
                if not cat:
                    cat = list(cat_by_name.values())[0] if cat_by_name else None
                if not cat:
                    continue
                if Dish.query.join(Category).filter(Category.franchisee_id == franchisee_id, Dish.name == nombre.strip()).first():
                    continue
                dish = Dish(
                    name=nombre.strip(),
                    description=desc or None,
                    price=precio,
                    available=disponible,
                    category_id=cat.id,
                )
                db.session.add(dish)
                dishes_created += 1
    wb.close()
    db.session.commit()
    return cats_created + dishes_created, None


# --- Mesas ---
def import_mesas(file_bytes, franchisee_id):
    import openpyxl
    from models import Table
    from extensions import db

    if not franchisee_id:
        return 0, "Selecciona un franquiciado"

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        numero = _to_float(row[0]) if len(row) > 0 else None
        if numero is None or numero < 1:
            continue
        capacidad = int(_to_float(row[1], 1) or 1)
        pos_x = int(_to_float(row[2], 0) or 0)
        pos_y = int(_to_float(row[3], 0) or 0)
        ocupada = _parse_si_no(row[4]) if len(row) > 4 else False
        if Table.query.filter_by(franchisee_id=franchisee_id, number=int(numero)).first():
            continue
        t = Table(
            franchisee_id=franchisee_id,
            number=int(numero),
            capacity=capacidad,
            position_x=pos_x,
            position_y=pos_y,
            occupied=ocupada,
        )
        db.session.add(t)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Clientes ---
def import_clientes(file_bytes, franchisee_id):
    import openpyxl
    from models import Client
    from extensions import db

    if not franchisee_id:
        return 0, "Selecciona un franquiciado"

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[0] if len(row) > 0 else None) or ""
        if not str(nombre).strip():
            continue
        cedula = str(row[1]).strip() if len(row) > 1 and row[1] else None
        email = str(row[2]).strip() if len(row) > 2 and row[2] else None
        telefono = str(row[3]).strip() if len(row) > 3 and row[3] else None
        direccion = str(row[4]).strip() if len(row) > 4 and row[4] else None
        notas = str(row[5]).strip() if len(row) > 5 and row[5] else None
        activo = _parse_si_no(row[6]) if len(row) > 6 else True
        if Client.query.filter_by(franchisee_id=franchisee_id, name=nombre.strip()).first():
            continue
        c = Client(
            franchisee_id=franchisee_id,
            name=nombre.strip(),
            tax_id=cedula or None,
            email=email or None,
            phone=telefono or None,
            address=direccion or None,
            notes=notas or None,
            active=activo,
        )
        db.session.add(c)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Proveedores ---
def import_proveedores(file_bytes, franchisee_id):
    import openpyxl
    from models import Supplier
    from extensions import db

    if not franchisee_id:
        return 0, "Selecciona un franquiciado"

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[0] if len(row) > 0 else None) or ""
        if not str(nombre).strip():
            continue
        if Supplier.query.filter_by(franchisee_id=franchisee_id, name=nombre.strip()).first():
            continue
        telefono = str(row[1]).strip() if len(row) > 1 and row[1] else None
        contacto = str(row[2]).strip() if len(row) > 2 and row[2] else None
        dia_visita = str(row[3]).strip() if len(row) > 3 and row[3] else None
        visita_prog = str(row[4]).strip() if len(row) > 4 and row[4] else None
        s = Supplier(
            franchisee_id=franchisee_id,
            name=nombre.strip(),
            phone=telefono or None,
            contact=contacto or None,
            visit_day=dia_visita or None,
            visit_schedule=visita_prog or None,
        )
        db.session.add(s)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Unidades (globales) ---
def import_unidades(file_bytes):
    import openpyxl
    from models import Unit
    from extensions import db

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        simbolo = (row[0] if len(row) > 0 else None) or ""
        if not str(simbolo).strip():
            continue
        if Unit.query.filter_by(symbol=simbolo.strip().upper()).first():
            continue
        nombre = str(row[1]).strip() if len(row) > 1 and row[1] else None
        u = Unit(symbol=simbolo.strip().upper(), name=nombre or None)
        db.session.add(u)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Puestos (globales) ---
def import_puestos(file_bytes):
    import openpyxl
    from models import Position
    from extensions import db

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[0] if len(row) > 0 else None) or ""
        if not str(nombre).strip():
            continue
        if Position.query.filter_by(name=nombre.strip()).first():
            continue
        tipo = str(row[1]).strip() if len(row) > 1 and row[1] else "empleado"
        salario = _to_float(row[2]) if len(row) > 2 else None
        horas = _to_float(row[3]) if len(row) > 3 else 8
        aplicar_ccss = _parse_si_no(row[4]) if len(row) > 4 else True
        p = Position(
            name=nombre.strip(),
            position_type=tipo or "empleado",
            salario_base=salario,
            horas_por_dia=horas,
            aplicar_ccss=aplicar_ccss,
        )
        db.session.add(p)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Tipos de registro (globales) ---
def import_tipos_registro(file_bytes):
    import openpyxl
    from models import PayrollEntryType
    from extensions import db

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[0] if len(row) > 0 else None) or ""
        if not str(nombre).strip():
            continue
        code = str(row[1]).strip().lower().replace(" ", "_") if len(row) > 1 and row[1] else None
        if not code:
            code = str(nombre).strip().lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        if PayrollEntryType.query.filter_by(code=code).first():
            continue
        desc = str(row[2]).strip() if len(row) > 2 and row[2] else None
        hide = _parse_si_no(row[3]) if len(row) > 3 else False
        t = PayrollEntryType(name=nombre.strip(), code=code, description=desc or None, hide_puesto=hide)
        db.session.add(t)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Tipos deducción (globales) ---
def import_tipos_deduccion(file_bytes):
    import openpyxl
    from models import DeductionType
    from extensions import db

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[0] if len(row) > 0 else None) or ""
        if not str(nombre).strip():
            continue
        if DeductionType.query.filter_by(name=nombre.strip()).first():
            continue
        desc = str(row[1]).strip() if len(row) > 1 and row[1] else None
        puede_neg = _parse_si_no(row[2]) if len(row) > 2 else False
        basado_hrs = _parse_si_no(row[3]) if len(row) > 3 else False
        tasa = _to_float(row[4]) if len(row) > 4 else None
        d = DeductionType(
            name=nombre.strip(),
            description=desc or None,
            can_be_negative=puede_neg,
            is_hours_based=basado_hrs,
            rate_pct=tasa,
        )
        db.session.add(d)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


# --- Empleados ---
def import_empleados(file_bytes, franchisee_id):
    import openpyxl
    from models import Employee, PayrollLocation, Position
    from extensions import db

    if not franchisee_id:
        return 0, "Selecciona un franquiciado"

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    loc_by_name = {l.name.upper(): l for l in PayrollLocation.query.filter_by(franchisee_id=franchisee_id).all()}
    pos_by_name = {p.name.upper(): p for p in Position.query.all()}
    created = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) if row else []
        nombre = (row[0] if len(row) > 0 else None) or ""
        if not str(nombre).strip():
            continue
        codigo = str(row[1]).strip() if len(row) > 1 and row[1] else None
        cedula = str(row[2]).strip() if len(row) > 2 and row[2] else None
        num_cuenta = str(row[3]).strip() if len(row) > 3 and row[3] else None
        ub_name = str(row[4]).strip() if len(row) > 4 and row[4] else None
        puesto_name = str(row[5]).strip() if len(row) > 5 and row[5] else None
        fecha_ing = _to_date(row[6]) if len(row) > 6 else None
        salario = _to_float(row[7]) if len(row) > 7 else None
        periodo = str(row[8]).strip() if len(row) > 8 and row[8] else "mensual"
        activo = _parse_si_no(row[9]) if len(row) > 9 else True

        loc = loc_by_name.get((ub_name or "").upper()) if ub_name else None
        pos = pos_by_name.get((puesto_name or "").upper()) if puesto_name else None

        if Employee.query.filter_by(franchisee_id=franchisee_id, name=nombre.strip()).first():
            continue
        emp = Employee(
            franchisee_id=franchisee_id,
            name=nombre.strip(),
            code=codigo or None,
            cedula=cedula or None,
            numero_cuenta=num_cuenta or None,
            location_id=loc.id if loc else None,
            position_id=pos.id if pos else None,
            fecha_ingreso=fecha_ing,
            salario_base=salario,
            periodo_pago=periodo or "mensual",
            active=activo,
        )
        db.session.add(emp)
        created += 1
    wb.close()
    db.session.commit()
    return created, None


IMPORT_HANDLERS = {
    "inventario": (import_inventario, ["replace"]),
    "planilla_ubicaciones": (import_planilla_ubicaciones, ["replace_all", "period_date"]),
    "casas": (import_casas, []),
    "menu": (import_menu, []),
    "mesas": (import_mesas, []),
    "clientes": (import_clientes, []),
    "proveedores": (import_proveedores, []),
    "unidades": (import_unidades, []),
    "puestos": (import_puestos, []),
    "tipos_registro": (import_tipos_registro, []),
    "tipos_deduccion": (import_tipos_deduccion, []),
    "empleados": (import_empleados, []),
}
