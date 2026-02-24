"""API de inventario e importación desde Excel."""
import csv
import io
import os
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from sqlalchemy import or_
from extensions import db
from models import InventoryItem, InventoryAlert, Supplier, Unit
from models.inventory import item_suppliers
from schemas import InventoryItemSchema, InventoryAlertSchema, SupplierSchema, UnitSchema
from utils.franchisee import get_or_default_franchisee_id

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

item_schema = InventoryItemSchema()
items_schema = InventoryItemSchema(many=True)
alert_schema = InventoryAlertSchema()
alerts_schema = InventoryAlertSchema(many=True)
supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)
unit_schema = UnitSchema()
units_schema = UnitSchema(many=True)

# Umbral por defecto: 10% del stock (inventario bajo cuando existencia < 10% de stock)
DEFAULT_LOW_STOCK_THRESHOLD = 0.10

# Ruta por defecto del Excel (relativa al directorio del proyecto)
DEFAULT_EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "excel_docs",
    "DATOS INVENTARIO.xlsx",
)


def _get_low_stock_items(threshold=None, franchisee_id=None):
    """Ítems con existencia < threshold * stock, o stock=0, o existencia=0. Filtra por franchisee_id si se indica."""
    if threshold is None:
        threshold = DEFAULT_LOW_STOCK_THRESHOLD
    query = InventoryItem.query
    if franchisee_id is not None:
        query = query.filter_by(franchisee_id=franchisee_id)
    items = query.all()
    result = []
    for it in items:
        stock_val = float(it.stock or 0)
        existence_val = float(it.existence or 0)
        pct = (existence_val / stock_val) * 100.0 if stock_val else 0
        # Alerta: stock=0, existencia=0, o existencia < 10% del stock
        is_low = stock_val == 0 or existence_val == 0 or existence_val < threshold * stock_val
        if is_low:
            suggested = it.order_quantity if it.order_quantity is not None else max(0.0, stock_val - existence_val)
            supplier_names = [s.name for s in it.suppliers] if it.suppliers else []
            if it.supplier and it.supplier.strip():
                supplier_names = supplier_names + [it.supplier.strip()]
            supplier_str = ", ".join(supplier_names) if supplier_names else it.supplier
            # Datos de contacto del proveedor (del primer Supplier relacionado o búsqueda por nombre)
            sup_phone = sup_contact = sup_visit_day = None
            if it.suppliers:
                s0 = it.suppliers[0]
                sup_phone, sup_contact, sup_visit_day = s0.phone, s0.contact, s0.visit_day
            elif supplier_str and franchisee_id:
                first_name = supplier_names[0] if supplier_names else (supplier_str.split(",")[0].strip() if supplier_str else None)
                s = Supplier.query.filter_by(franchisee_id=franchisee_id, name=first_name).first() if first_name else None
                if s:
                    sup_phone, sup_contact, sup_visit_day = s.phone, s.contact, s.visit_day
            result.append({
                "id": it.id,
                "code": getattr(it, "code", None),
                "area": it.area,
                "product_name": it.product_name,
                "unit": getattr(it, "unit", None) or "UND",
                "existence": it.existence,
                "stock": it.stock,
                "percentage": round(pct, 2),
                "order_quantity": it.order_quantity,
                "purchase_price": getattr(it, "purchase_price", None),
                "supplier": supplier_str,
                "supplier_phone": sup_phone,
                "supplier_contact": sup_contact,
                "supplier_visit_day": sup_visit_day,
                "suggested_order": suggested,
            })
    return result


def _get_unit_symbols():
    """Devuelve el set de símbolos de unidades definidos en la base de datos."""
    symbols = {u.symbol for u in Unit.query.all()}
    return symbols if symbols else {"UND"}


def _normalize_unit(val):
    """Normaliza un valor a una unidad válida (según tabla units)."""
    symbols = _get_unit_symbols()
    default = "UND" if "UND" in symbols else next(iter(symbols), "UND")
    if not val:
        return default
    s = str(val).strip().upper()
    if s in symbols:
        return s
    # Variantes comunes en Excel
    if s in ("KGS", "KILO", "KILOS", "KILOGRAMO", "KILOGRAMOS") and "KG" in symbols:
        return "KG"
    if s in ("GRS", "GRAMO", "GRAMOS") and "GR" in symbols:
        return "GR"
    if s in ("CAJA", "CAJAS", "CJAS") and "CJ" in symbols:
        return "CJ"
    if s in ("UN", "UNID", "UNIDAD", "UNIDADES", "U") and "UND" in symbols:
        return "UND"
    return default


def _to_float(val, default=None):
    """Convierte a float si es posible; si no, devuelve default."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return default
    # Quitar caracteres no numéricos al final (ej. "2KG" -> 2, "0.5 L" -> 0.5)
    m = re.match(r"^([-+]?\d*\.?\d+)", s.replace(",", "."))
    return float(m.group(1)) if m else default


def _parse_excel(path):
    """
    Lee la hoja "INVENTARIO" de DATOS INVENTARIO.xlsx.
    Usa utils.excel_inventory; normaliza unidades según tabla units de la BD.
    """
    from utils.excel_inventory import parse_excel_inventory as _parse
    items, err = _parse(path)
    if err:
        return None, err
    # Normalizar unidades según BD (el utils usa UND por defecto)
    for d in items:
        d["unit"] = _normalize_unit(d.get("unit"))
    return items, None


@inventory_bp.route("", methods=["GET"])
def list_inventory():
    """Lista ítems del franquiciado. Query: ?area=salon|cocina, ?q=buscar."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    area = request.args.get("area")
    supplier_id = request.args.get("supplier_id", type=int)
    q = (request.args.get("q") or "").strip()
    query = InventoryItem.query.filter_by(franchisee_id=fid)
    if area in ("salon", "cocina"):
        query = query.filter_by(area=area)
    if supplier_id:
        query = query.join(item_suppliers).filter(item_suppliers.c.supplier_id == supplier_id).distinct()
    if q:
        query = query.outerjoin(InventoryItem.suppliers).filter(
            or_(
                InventoryItem.product_name.ilike(f"%{q}%"),
                Supplier.name.ilike(f"%{q}%"),
            )
        ).distinct()
    items = query.order_by(InventoryItem.area, InventoryItem.product_name).all()
    return jsonify(items_schema.dump(items))


# ---------- Unidades de medida ----------

@inventory_bp.route("/units", methods=["GET"])
def list_units():
    """Lista unidades de medida (símbolo y nombre)."""
    units = Unit.query.order_by(Unit.symbol).all()
    return jsonify(units_schema.dump(units))


@inventory_bp.route("/units", methods=["POST"])
def create_unit():
    """Crea una unidad de medida. Body: symbol (obligatorio), name (opcional)."""
    data = request.get_json() or {}
    symbol = (data.get("symbol") or "").strip().upper()
    if not symbol:
        return jsonify({"error": "El símbolo es obligatorio"}), 400
    if Unit.query.filter_by(symbol=symbol).first():
        return jsonify({"error": "Ya existe una unidad con ese símbolo"}), 400
    unit = Unit(
        symbol=symbol,
        name=(data.get("name") or "").strip() or None,
    )
    db.session.add(unit)
    db.session.commit()
    return jsonify(unit_schema.dump(unit)), 201


@inventory_bp.route("/units/<int:unit_id>", methods=["PUT"])
def update_unit(unit_id):
    """Actualiza una unidad de medida. Body: symbol, name (opcionales)."""
    unit = db.get_or_404(Unit, unit_id)
    data = request.get_json() or {}
    if "symbol" in data:
        symbol = str(data["symbol"]).strip().upper()
        if not symbol:
            return jsonify({"error": "El símbolo no puede estar vacío"}), 400
        other = Unit.query.filter(Unit.symbol == symbol, Unit.id != unit_id).first()
        if other:
            return jsonify({"error": "Ya existe otra unidad con ese símbolo"}), 400
        unit.symbol = symbol
    if "name" in data:
        unit.name = (data.get("name") or "").strip() or None
    db.session.commit()
    return jsonify(unit_schema.dump(unit))


@inventory_bp.route("/units/<int:unit_id>", methods=["DELETE"])
def delete_unit(unit_id):
    """Elimina una unidad. No se puede eliminar si algún ítem de inventario la usa."""
    unit = db.get_or_404(Unit, unit_id)
    count = InventoryItem.query.filter_by(unit=unit.symbol).count()
    if count > 0:
        return jsonify({"error": f"No se puede eliminar: {count} ítem(s) de inventario usan esta unidad"}), 400
    db.session.delete(unit)
    db.session.commit()
    return "", 204


# ---------- Proveedores ----------

@inventory_bp.route("/suppliers", methods=["GET"])
def list_suppliers():
    """Lista proveedores del franquiciado. Query: ?q=buscar."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    q = (request.args.get("q") or "").strip()
    query = Supplier.query.filter_by(franchisee_id=fid).order_by(Supplier.name)
    if q:
        query = query.filter(Supplier.name.ilike(f"%{q}%"))
    suppliers = query.all()
    return jsonify(suppliers_schema.dump(suppliers))


@inventory_bp.route("/suppliers", methods=["POST"])
def create_supplier():
    """Crea un proveedor nuevo."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    if Supplier.query.filter_by(franchisee_id=fid, name=name).first():
        return jsonify({"error": "Ya existe un proveedor con ese nombre"}), 400
    supplier = Supplier(
        franchisee_id=fid,
        name=name,
        phone=(data.get("phone") or "").strip() or None,
        contact=(data.get("contact") or "").strip() or None,
        visit_day=(data.get("visit_day") or "").strip() or None,
        visit_schedule=(data.get("visit_schedule") or "").strip() or None,
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify(supplier_schema.dump(supplier)), 201


@inventory_bp.route("/suppliers/export", methods=["GET"])
def export_suppliers():
    """Exporta proveedores en CSV. Query: ?format=csv."""
    fmt = (request.args.get("format") or "csv").lower()
    fid = get_or_default_franchisee_id()
    suppliers = Supplier.query.filter_by(franchisee_id=fid).order_by(Supplier.name).all() if fid else []
    if fmt != "csv":
        return jsonify(suppliers_schema.dump(suppliers))
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Nombre", "Teléfono", "Contacto directo", "Día visita", "Rol visita"])
    for s in suppliers:
        writer.writerow([
            s.id,
            s.name or "",
            getattr(s, "phone", None) or "",
            getattr(s, "contact", None) or "",
            getattr(s, "visit_day", None) or "",
            getattr(s, "visit_schedule", None) or "",
        ])
    buf.seek(0)
    body = "\ufeff" + buf.getvalue()
    return Response(
        body,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=proveedores.csv"},
    )


@inventory_bp.route("/suppliers/copy-from-franchisee", methods=["POST"])
def copy_suppliers_from_franchisee():
    """
    Copia proveedores desde otro franquiciado. Body: { franchisee_id: 1 }.
    Los mismos nombres; cada franquiciado edita su teléfono, contacto, día de visita.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    source_fid = data.get("franchisee_id")
    try:
        source_fid = int(source_fid) if source_fid is not None else None
    except (TypeError, ValueError):
        source_fid = None
    if not source_fid:
        return jsonify({"error": "franchisee_id es obligatorio"}), 400
    if source_fid == fid:
        return jsonify({"error": "No puedes copiar desde el mismo franquiciado"}), 400
    source_suppliers = Supplier.query.filter_by(franchisee_id=source_fid).order_by(Supplier.name).all()
    created = 0
    for s in source_suppliers:
        if not Supplier.query.filter_by(franchisee_id=fid, name=s.name).first():
            db.session.add(Supplier(
                franchisee_id=fid, name=s.name,
                phone=s.phone, contact=s.contact, visit_day=s.visit_day, visit_schedule=s.visit_schedule,
            ))
            created += 1
    db.session.commit()
    return jsonify({"message": f"Copiados {created} proveedores. Total: {len(source_suppliers)}.", "created": created})


@inventory_bp.route("/suppliers/reload-from-excel", methods=["POST"])
def reload_suppliers_from_excel():
    """
    Vuelve a cargar los proveedores desde la hoja INVENTARIO del Excel.
    Crea proveedores del franquiciado actual que no existan.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    path = data.get("path") or DEFAULT_EXCEL_PATH
    items_list, error = _parse_excel(path)
    if error:
        return jsonify({"error": error}), 400
    names = set()
    for d in items_list:
        for name in (d.get("supplier"), d.get("supplier2")):
            if name and str(name).strip():
                names.add(str(name).strip())
    created = 0
    for name in sorted(names):
        if Supplier.query.filter_by(franchisee_id=fid, name=name).first():
            continue
        db.session.add(Supplier(franchisee_id=fid, name=name))
        created += 1
    db.session.commit()
    return jsonify({
        "message": "Proveedores cargados desde el Excel.",
        "total_in_excel": len(names),
        "created": created,
    })


def _normalize_supplier_name(name):
    """
    Nombre normalizado para detectar duplicados: minúsculas, sin espacios extra,
    y sin acentos (Isleña=islena, Jean Ledezma=Jean ledezma=jean ledezma, Super=super).
    """
    if not name:
        return ""
    import unicodedata
    s = str(name).strip().lower()
    s = " ".join(s.split())
    # Quitar acentos: ñ->n, á->a, etc.
    nfd = unicodedata.normalize("NFD", s)
    s = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return s


@inventory_bp.route("/suppliers/suggest-duplicates", methods=["GET"])
def suggest_supplier_duplicates():
    """
    Sugiere grupos de proveedores duplicados del franquiciado actual.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"groups": []})
    all_suppliers = Supplier.query.filter_by(franchisee_id=fid).order_by(Supplier.name).all()
    by_normalized = {}
    for s in all_suppliers:
        n = _normalize_supplier_name(s.name)
        if n not in by_normalized:
            by_normalized[n] = []
        by_normalized[n].append(s)

    groups = []
    seen_ids = set()
    for n, supps in by_normalized.items():
        if len(supps) > 1 and n:
            ids = [s.id for s in supps]
            groups.append({"names": [s.name for s in supps], "ids": ids, "reason": "Mismo nombre (mayúsculas/minúsculas)"})
            seen_ids.update(ids)
    for s in all_suppliers:
        if s.id in seen_ids:
            continue
        n = _normalize_supplier_name(s.name)
        if len(n) < 2:
            continue
        for other in all_suppliers:
            if other.id == s.id or other.id in seen_ids:
                continue
            other_n = _normalize_supplier_name(other.name)
            if n in other_n or other_n in n:
                ids = [s.id, other.id]
                groups.append({
                    "names": [s.name, other.name],
                    "ids": ids,
                    "reason": "Nombre similar o contenido en otro",
                })
                seen_ids.add(s.id)
                seen_ids.add(other.id)
                break
    return jsonify({"groups": groups})


@inventory_bp.route("/suppliers/merge", methods=["POST"])
def merge_suppliers():
    """
    Unifica dos proveedores: todos los ítems que usan from_id pasan a usar into_id.
    Body: { "from_id": 123, "into_id": 456 }. Se elimina el proveedor from_id.
    """
    data = request.get_json(silent=True) or {}
    from_id = data.get("from_id")
    into_id = data.get("into_id")
    if from_id is None or into_id is None:
        return jsonify({"error": "Se requieren from_id e into_id"}), 400
    try:
        from_id = int(from_id)
        into_id = int(into_id)
    except (TypeError, ValueError):
        return jsonify({"error": "from_id e into_id deben ser números"}), 400
    if from_id == into_id:
        return jsonify({"error": "from_id e into_id deben ser distintos"}), 400
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    from_supplier = Supplier.query.filter_by(id=from_id, franchisee_id=fid).first()
    into_supplier = Supplier.query.filter_by(id=into_id, franchisee_id=fid).first()
    if not from_supplier or not into_supplier:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    from sqlalchemy import delete, and_, select
    sel = select(item_suppliers.c.inventory_item_id).where(item_suppliers.c.supplier_id == from_id)
    rows = db.session.execute(sel).fetchall()
    item_ids_with_from = [row[0] for row in rows]
    for iid in item_ids_with_from:
        existing = db.session.execute(
            select(item_suppliers).where(
                and_(
                    item_suppliers.c.inventory_item_id == iid,
                    item_suppliers.c.supplier_id == into_id,
                )
            )
        ).fetchone()
        if not existing:
            db.session.execute(item_suppliers.insert().values(inventory_item_id=iid, supplier_id=into_id))
        db.session.execute(
            delete(item_suppliers).where(
                and_(
                    item_suppliers.c.inventory_item_id == iid,
                    item_suppliers.c.supplier_id == from_id,
                )
            )
        )
    InventoryItem.query.filter_by(franchisee_id=fid, supplier=from_supplier.name).update({"supplier": into_supplier.name})
    db.session.delete(from_supplier)
    db.session.commit()
    return jsonify({"message": "Proveedores unificados.", "into_id": into_id})


@inventory_bp.route("/suppliers/<int:supplier_id>", methods=["GET"])
def get_supplier(supplier_id):
    """Obtiene un proveedor por ID."""
    fid = get_or_default_franchisee_id()
    supplier = Supplier.query.filter_by(id=supplier_id, franchisee_id=fid).first() if fid else None
    if not supplier:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    return jsonify(supplier_schema.dump(supplier))


@inventory_bp.route("/suppliers/<int:supplier_id>", methods=["PUT"])
def update_supplier(supplier_id):
    """Actualiza el nombre del proveedor y corrige en todos los ítems que lo usan."""
    fid = get_or_default_franchisee_id()
    supplier = Supplier.query.filter_by(id=supplier_id, franchisee_id=fid).first() if fid else None
    if not supplier:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}
    raw_name = data.get("name") if data.get("name") is not None else request.form.get("name")
    new_name = (raw_name or "").strip()
    if not new_name:
        return jsonify({"error": "El nombre es obligatorio. Envía JSON: {\"name\": \"Nuevo nombre\"}"}), 400
    old_name = supplier.name
    if old_name == new_name:
        return jsonify(supplier_schema.dump(supplier))
    existing = Supplier.query.filter(
        Supplier.franchisee_id == fid, Supplier.name == new_name, Supplier.id != supplier_id
    ).first()
    if existing:
        return jsonify({"error": "Ya existe otro proveedor con ese nombre"}), 400
    supplier.name = new_name
    if "phone" in data:
        supplier.phone = (data.get("phone") or "").strip() or None
    if "contact" in data:
        supplier.contact = (data.get("contact") or "").strip() or None
    if "visit_day" in data:
        supplier.visit_day = (data.get("visit_day") or "").strip() or None
    if "visit_schedule" in data:
        supplier.visit_schedule = (data.get("visit_schedule") or "").strip() or None
    InventoryItem.query.filter_by(franchisee_id=fid, supplier=old_name).update({"supplier": new_name})
    db.session.commit()
    return jsonify(supplier_schema.dump(supplier))


@inventory_bp.route("/suppliers/<int:supplier_id>", methods=["DELETE"])
def delete_supplier(supplier_id):
    """Elimina un proveedor (los ítems conservan el nombre como texto)."""
    fid = get_or_default_franchisee_id()
    supplier = Supplier.query.filter_by(id=supplier_id, franchisee_id=fid).first() if fid else None
    if not supplier:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    db.session.delete(supplier)
    db.session.commit()
    return "", 204


@inventory_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Obtiene un ítem por ID."""
    fid = get_or_default_franchisee_id()
    item = InventoryItem.query.filter_by(id=item_id, franchisee_id=fid).first() if fid else None
    if not item:
        return jsonify({"error": "Ítem no encontrado"}), 404
    return jsonify(item_schema.dump(item))


def _set_item_suppliers(item, supplier_ids, franchisee_id=None):
    """Asigna la lista de proveedores a un ítem (solo del mismo franquiciado)."""
    if not franchisee_id:
        item.suppliers = []
        return
    item.suppliers = [
        s for sid in (supplier_ids or [])
        if isinstance(sid, int) and (s := Supplier.query.filter_by(id=sid, franchisee_id=franchisee_id).first())
    ]


def _get_next_code(area, franchisee_id=None):
    """
    Devuelve el siguiente código consecutivo por área y franquiciado.
    """
    prefix = "83" if area == "salon" else "67" if area == "cocina" else None
    if not prefix:
        return None
    query = InventoryItem.query.filter(InventoryItem.code.like(f"{prefix}-%"))
    if franchisee_id:
        query = query.filter_by(franchisee_id=franchisee_id)
    items = query.all()
    max_num = 0
    for it in items:
        if not it.code:
            continue
        part = (it.code or "").split("-", 1)
        if len(part) < 2:
            continue
        try:
            n = int(part[1].strip())
            if n > max_num:
                max_num = n
        except ValueError:
            continue
    return f"{prefix}-{max_num + 1:02d}"


@inventory_bp.route("/next-code", methods=["GET"])
def next_code():
    """Devuelve el siguiente código disponible para el área. Query: ?area=salon|cocina."""
    area = request.args.get("area", "salon")
    fid = get_or_default_franchisee_id()
    code = _get_next_code(area, fid)
    return jsonify({"code": code or ""})


@inventory_bp.route("", methods=["POST"])
def create_item():
    """Crea un ítem de inventario del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    supplier_ids = data.pop("supplier_ids", None)
    data["franchisee_id"] = fid
    if not data.get("code") or not str(data.get("code")).strip():
        area = data.get("area") or "salon"
        data["code"] = _get_next_code(area, fid) or ""
    item = item_schema.load(data, session=db.session)
    db.session.add(item)
    db.session.flush()  # para tener item.id antes de asociar proveedores
    _set_item_suppliers(item, supplier_ids, fid)
    db.session.commit()
    return jsonify(item_schema.dump(item)), 201


@inventory_bp.route("/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Actualiza un ítem. Body puede incluir supplier_ids: [1, 2, ...]."""
    fid = get_or_default_franchisee_id()
    item = InventoryItem.query.filter_by(id=item_id, franchisee_id=fid).first() if fid else None
    if not item:
        return jsonify({"error": "Ítem no encontrado"}), 404
    data = request.get_json() or {}
    supplier_ids = data.pop("supplier_ids", None)
    item_schema.load(data, instance=item, session=db.session, partial=True)
    if supplier_ids is not None:
        _set_item_suppliers(item, supplier_ids, fid)
    db.session.commit()
    return jsonify(item_schema.dump(item))


@inventory_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Elimina un ítem."""
    fid = get_or_default_franchisee_id()
    item = InventoryItem.query.filter_by(id=item_id, franchisee_id=fid).first() if fid else None
    if not item:
        return jsonify({"error": "Ítem no encontrado"}), 404
    db.session.delete(item)
    db.session.commit()
    return "", 204


def _get_or_create_supplier_id(name, franchisee_id):
    """Devuelve el id del proveedor con ese nombre del franquiciado; si no existe, lo crea."""
    if not name or not str(name).strip() or not franchisee_id:
        return None
    name = str(name).strip()
    s = Supplier.query.filter_by(franchisee_id=franchisee_id, name=name).first()
    if s:
        return s.id
    s = Supplier(franchisee_id=franchisee_id, name=name)
    db.session.add(s)
    db.session.flush()
    return s.id


@inventory_bp.route("/copy-from-franchisee", methods=["POST"])
def copy_inventory_from_franchisee():
    """
    Copia el catálogo de inventario desde otro franquiciado. Body: { franchisee_id: 1 }.
    Mismos productos; stock en 0 para que cada ubicación registre el suyo.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    source_fid = data.get("franchisee_id")
    try:
        source_fid = int(source_fid) if source_fid is not None else None
    except (TypeError, ValueError):
        source_fid = None
    if not source_fid:
        return jsonify({"error": "franchisee_id es obligatorio"}), 400
    if source_fid == fid:
        return jsonify({"error": "No puedes copiar desde el mismo franquiciado"}), 400
    source_items = InventoryItem.query.filter_by(franchisee_id=source_fid).all()
    created = 0
    for it in source_items:
        if InventoryItem.query.filter_by(franchisee_id=fid, product_name=it.product_name, area=it.area).first():
            continue
        supplier_ids = []
        for s in it.suppliers:
            target_s = Supplier.query.filter_by(franchisee_id=fid, name=s.name).first()
            if target_s and target_s.id not in supplier_ids:
                supplier_ids.append(target_s.id)
            elif not target_s:
                new_s = Supplier(franchisee_id=fid, name=s.name, phone=s.phone, contact=s.contact, visit_day=s.visit_day, visit_schedule=s.visit_schedule)
                db.session.add(new_s)
                db.session.flush()
                supplier_ids.append(new_s.id)
        new_item = InventoryItem(
            franchisee_id=fid,
            code=it.code, area=it.area, product_name=it.product_name,
            unit=it.unit or "UND",
            existence=0, stock=0,
            order_quantity=it.order_quantity, supplier=it.supplier, responsible=it.responsible,
        )
        db.session.add(new_item)
        db.session.flush()
        _set_item_suppliers(new_item, supplier_ids, fid)
        created += 1
    db.session.commit()
    return jsonify({"message": f"Copiados {created} ítems. Total en origen: {len(source_items)}.", "created": created})


@inventory_bp.route("/import-excel", methods=["POST"])
def import_from_excel():
    """
    Importa inventario desde el Excel para el franquiciado actual.
    Body opcional: { "path": "...", "replace": true }.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    path = data.get("path") or DEFAULT_EXCEL_PATH
    replace = data.get("replace", False)

    items_list, error = _parse_excel(path)
    if error:
        return jsonify({"error": error}), 400

    if replace:
        from sqlalchemy import delete
        db.session.execute(delete(item_suppliers))
        InventoryItem.query.filter_by(franchisee_id=fid).delete()

    created = 0
    for d in items_list:
        supplier_ids = []
        for sup_name in (d.get("supplier"), d.get("supplier2")):
            sid = _get_or_create_supplier_id(sup_name, fid)
            if sid is not None and sid not in supplier_ids:
                supplier_ids.append(sid)
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
        _set_item_suppliers(item, supplier_ids, fid)
        created += 1

    db.session.commit()
    return jsonify({"message": "Importación correcta", "imported": created}), 200


# ---------- Reporte y notificaciones de inventario bajo (< 10% del stock) ----------

@inventory_bp.route("/report", methods=["GET"])
def report_low_stock():
    """
    Reporte de ítems con inventario bajo (existencia < threshold * stock).
    Query: ?threshold=0.1 (default 10%), ?format=json|csv, ?supplier=Nombre (filtrar por proveedor)
    """
    threshold = request.args.get("threshold", type=float)
    if threshold is None or threshold <= 0 or threshold > 1:
        threshold = DEFAULT_LOW_STOCK_THRESHOLD
    supplier_filter = request.args.get("supplier", "").strip()
    fmt = (request.args.get("format") or "json").lower()
    fid = get_or_default_franchisee_id()
    items = _get_low_stock_items(threshold, fid)
    if supplier_filter:
        if supplier_filter.lower() == "sin proveedor":
            items = [it for it in items if not (it.get("supplier") or "").strip()]
        else:
            items = [it for it in items if it.get("supplier") and supplier_filter.lower() in (it.get("supplier") or "").lower()]
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "threshold_percent": round(threshold * 100, 1),
        "count": len(items),
        "items": items,
    }
    if fmt == "csv":
        safe_name = re.sub(r"[^\w\-]", "_", supplier_filter)[:50] if supplier_filter else ""
        payload["filename"] = f"pedidos_{safe_name}.csv" if safe_name else "reporte_pedidos_completo.csv"
        payload["items"] = sorted(payload["items"], key=lambda x: ((x.get("supplier") or "").lower(), x.get("product_name") or ""))
        return _report_as_csv(payload)
    return jsonify(payload)


def _report_as_csv(payload, include_supplier_contact=True):
    """Genera respuesta CSV del reporte de faltantes (UTF-8 con BOM para Excel).
    Incluye Teléfono, Contacto y Día visita del proveedor cuando estén disponibles."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    headers = ["Proveedor", "Teléfono", "Contacto", "Día visita", "Área", "Producto", "Unidad", "Existencia", "Stock", "% actual", "Pedido sugerido"]
    if not include_supplier_contact:
        headers = ["Área", "Producto", "Unidad", "Existencia", "Stock", "% actual", "Pedido sugerido", "Proveedor"]
    writer.writerow(headers)
    for row in payload.get("items", []):
        if include_supplier_contact:
            writer.writerow([
                row.get("supplier", ""),
                row.get("supplier_phone") or "",
                row.get("supplier_contact") or "",
                row.get("supplier_visit_day") or "",
                row.get("area", ""),
                row.get("product_name", ""),
                row.get("unit", "UND"),
                row.get("existence", ""),
                row.get("stock", ""),
                str(row.get("percentage", "")) + "%",
                row.get("suggested_order", ""),
            ])
        else:
            writer.writerow([
                row.get("area", ""),
                row.get("product_name", ""),
                row.get("unit", "UND"),
                row.get("existence", ""),
                row.get("stock", ""),
                str(row.get("percentage", "")) + "%",
                row.get("suggested_order", ""),
                row.get("supplier", ""),
            ])
    buf.seek(0)
    body = "\ufeff" + buf.getvalue()  # BOM UTF-8 para que Excel abra bien los acentos
    filename = payload.get("filename") or "reporte_faltantes_inventario.csv"
    return Response(
        body,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@inventory_bp.route("/check-low-stock", methods=["POST"])
def check_and_notify_low_stock():
    """
    Evalúa inventario bajo (existencia < 10% del stock), crea una notificación (alerta)
    y devuelve el reporte. Body opcional: { "threshold": 0.1 }
    """
    data = request.get_json() or {}
    threshold = data.get("threshold")
    if threshold is None:
        threshold = DEFAULT_LOW_STOCK_THRESHOLD
    elif not isinstance(threshold, (int, float)) or threshold <= 0 or threshold > 1:
        threshold = DEFAULT_LOW_STOCK_THRESHOLD
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    items = _get_low_stock_items(threshold, fid)
    alert = InventoryAlert(
        franchisee_id=fid,
        threshold=threshold,
        item_count=len(items),
        items_snapshot=items,
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({
        "message": "Revisión realizada; notificación registrada.",
        "alert_id": alert.id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "threshold_percent": round(threshold * 100, 1),
        "count": len(items),
        "items": items,
    }), 200


@inventory_bp.route("/alerts", methods=["GET"])
def list_alerts():
    """Lista las alertas de inventario bajo del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    query = InventoryAlert.query.filter_by(franchisee_id=fid) if fid else InventoryAlert.query.filter(False)
    alerts = query.order_by(InventoryAlert.created_at.desc()).limit(100).all()
    return jsonify(alerts_schema.dump(alerts))


@inventory_bp.route("/alerts/<int:alert_id>", methods=["GET"])
def get_alert(alert_id):
    """Obtiene una alerta por ID."""
    fid = get_or_default_franchisee_id()
    alert = InventoryAlert.query.filter_by(id=alert_id, franchisee_id=fid).first() if fid else None
    if not alert:
        return jsonify({"error": "Alerta no encontrada"}), 404
    return jsonify(alert_schema.dump(alert))


@inventory_bp.route("/alerts/<int:alert_id>/export", methods=["GET"])
def export_alert_csv(alert_id):
    """Exporta el reporte de una alerta como CSV."""
    fid = get_or_default_franchisee_id()
    alert = InventoryAlert.query.filter_by(id=alert_id, franchisee_id=fid).first() if fid else None
    if not alert:
        return jsonify({"error": "Alerta no encontrada"}), 404
    payload = {
        "items": alert.items_snapshot or [],
        "generated_at": alert.created_at.isoformat() if alert.created_at else "",
        "threshold_percent": round(alert.threshold * 100, 1),
    }
    return _report_as_csv(payload)
