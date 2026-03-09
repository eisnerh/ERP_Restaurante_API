"""API de órdenes de compra (ERP)."""
from datetime import datetime, timedelta
import csv
import io
from flask import Blueprint, request, jsonify, Response
from extensions import db
from models import PurchaseOrder, PurchaseOrderItem, Supplier, InventoryItem
from schemas import PurchaseOrderSchema, PurchaseOrderItemSchema, SupplierSchema
from utils.franchisee import get_or_default_franchisee_id

purchases_bp = Blueprint("purchases", __name__, url_prefix="/api/purchases")

order_schema = PurchaseOrderSchema()
orders_schema = PurchaseOrderSchema(many=True)
item_schema = PurchaseOrderItemSchema()
supplier_schema = SupplierSchema()


def _next_order_number(franchisee_id):
    """Genera el siguiente número de orden por franquiciado (PO-YYYYMM-001)."""
    prefix = f"PO-{datetime.utcnow().strftime('%Y%m')}-"
    query = PurchaseOrder.query.filter(
        PurchaseOrder.franchisee_id == franchisee_id,
        PurchaseOrder.order_number.like(f"{prefix}%"),
    ).order_by(PurchaseOrder.order_number.desc())
    last = query.first()
    if not last or not last.order_number:
        return f"{prefix}001"
    try:
        num = int(last.order_number.split("-")[-1])
        return f"{prefix}{num + 1:03d}"
    except (ValueError, IndexError):
        return f"{prefix}001"


@purchases_bp.route("", methods=["GET"])
def list_orders():
    """Lista órdenes de compra del franquiciado. Query: ?supplier_id=, ?status=, ?q=."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    supplier_id = request.args.get("supplier_id", type=int)
    status = request.args.get("status")
    q = (request.args.get("q") or "").strip()
    query = PurchaseOrder.query.filter_by(franchisee_id=fid).order_by(PurchaseOrder.order_date.desc())
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    if status:
        query = query.filter_by(status=status)
    if q:
        query = query.join(Supplier).filter(Supplier.name.ilike(f"%{q}%"))
    orders = query.all()
    return jsonify(orders_schema.dump(orders))


@purchases_bp.route("", methods=["POST"])
def create_order():
    """Crea una orden de compra del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    supplier_id = data.get("supplier_id")
    if not supplier_id:
        return jsonify({"error": "supplier_id es obligatorio"}), 400
    supplier = Supplier.query.filter_by(id=supplier_id, franchisee_id=fid).first()
    if not supplier:
        return jsonify({"error": "Proveedor no encontrado"}), 404

    order_date = data.get("order_date")
    if order_date:
        try:
            dt = datetime.strptime(order_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            dt = datetime.utcnow()
    else:
        dt = datetime.utcnow()
    order = PurchaseOrder(
        franchisee_id=fid,
        supplier_id=supplier_id,
        order_number=_next_order_number(fid),
        order_date=dt,
        notes=(data.get("notes") or "").strip() or None,
        status="draft",
    )
    db.session.add(order)
    db.session.flush()

    items_data = data.get("items") or []
    for it in items_data:
        inv_id = it.get("inventory_item_id")
        product = (it.get("product_name") or "").strip()
        if not product and inv_id:
            inv = InventoryItem.query.filter_by(id=inv_id, franchisee_id=fid).first()
            product = inv.product_name if inv else "Producto"
        if not product:
            continue
        item = PurchaseOrderItem(
            purchase_order_id=order.id,
            inventory_item_id=inv_id or None,
            product_name=product,
            quantity=float(it.get("quantity", 1)),
            unit=(it.get("unit") or "UND").strip(),
            unit_price=float(it.get("unit_price", 0)),
            notes=(it.get("notes") or "").strip() or None,
        )
        db.session.add(item)
    order.recalc_total()
    db.session.commit()
    return jsonify(order_schema.dump(order)), 201


@purchases_bp.route("/direct", methods=["POST"])
def create_direct_purchase():
    """
    Registra una compra directa: fecha, proveedor, monto.
    Se crea como orden recibida (cuenta en total de compras) sin ítems de inventario.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    supplier_id = data.get("supplier_id")
    if not supplier_id:
        return jsonify({"error": "supplier_id es obligatorio"}), 400
    supplier = Supplier.query.filter_by(id=supplier_id, franchisee_id=fid).first()
    if not supplier:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    total = float(data.get("total") or 0)
    if total <= 0:
        return jsonify({"error": "El monto debe ser mayor que 0"}), 400
    order_date = data.get("order_date")
    if order_date:
        try:
            dt = datetime.strptime(order_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            dt = datetime.utcnow()
    else:
        dt = datetime.utcnow()
    order = PurchaseOrder(
        franchisee_id=fid,
        supplier_id=supplier_id,
        order_number=_next_order_number(fid),
        order_date=dt,
        notes="Compra directa",
        status="received",
        total=total,
    )
    db.session.add(order)
    db.session.flush()
    item = PurchaseOrderItem(
        purchase_order_id=order.id,
        product_name="Compra directa",
        quantity=1,
        unit="Pago",
        unit_price=total,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(order_schema.dump(order)), 201


@purchases_bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Obtiene una orden con sus ítems."""
    fid = get_or_default_franchisee_id()
    order = PurchaseOrder.query.filter_by(id=order_id, franchisee_id=fid).first() if fid else None
    if not order:
        return jsonify({"error": "Orden no encontrada"}), 404
    return jsonify(order_schema.dump(order))


@purchases_bp.route("/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    """Actualiza una orden (solo draft). Body: status, items[], notes."""
    fid = get_or_default_franchisee_id()
    order = PurchaseOrder.query.filter_by(id=order_id, franchisee_id=fid).first() if fid else None
    if not order:
        return jsonify({"error": "Orden no encontrada"}), 404
    data = request.get_json() or {}
    new_status = data.get("status", order.status)
    can_edit_full = order.status == "draft"
    can_mark_received = order.status in ("draft", "sent") and "status" in data and new_status == "received"

    if not can_edit_full and not can_mark_received:
        return jsonify({"error": "Solo se pueden editar órdenes en borrador"}), 400

    if "status" in data:
        order.status = new_status
        if new_status == "received":
            for item in order.items:
                inv = None
                if item.inventory_item_id:
                    inv = InventoryItem.query.filter_by(id=item.inventory_item_id, franchisee_id=fid).first()
                if not inv and (item.product_name or "").strip():
                    inv = InventoryItem.query.filter_by(
                        franchisee_id=fid,
                        product_name=(item.product_name or "").strip(),
                    ).first()
                if not inv and (item.product_name or "").strip():
                    inv = InventoryItem(
                        franchisee_id=fid,
                        product_name=(item.product_name or "").strip(),
                        area="cocina",
                        unit=(item.unit or "UND").strip(),
                        existence=0,
                        stock=0,
                        purchase_price=item.unit_price if item.unit_price and item.unit_price > 0 else None,
                    )
                    db.session.add(inv)
                    db.session.flush()
                if inv:
                    qty = float(item.quantity or 0)
                    inv.existence = float(inv.existence or 0) + qty
                    if item.unit_price and item.unit_price > 0:
                        inv.purchase_price = item.unit_price
    if can_edit_full and "order_date" in data:
        od = data.get("order_date")
        if od:
            try:
                order.order_date = datetime.strptime(od, "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
    if can_edit_full and "notes" in data:
        order.notes = (data.get("notes") or "").strip() or None
    if can_edit_full and "items" in data:
        for existing in order.items:
            db.session.delete(existing)
        for it in data.get("items", []):
            inv_id = it.get("inventory_item_id")
            product = (it.get("product_name") or "").strip()
            if not product and inv_id:
                inv = InventoryItem.query.filter_by(id=inv_id, franchisee_id=fid).first()
                product = inv.product_name if inv else "Producto"
            if not product:
                continue
            item = PurchaseOrderItem(
                purchase_order_id=order.id,
                inventory_item_id=inv_id or None,
                product_name=product,
                quantity=float(it.get("quantity", 1)),
                unit=(it.get("unit") or "UND").strip(),
                unit_price=float(it.get("unit_price", 0)),
                notes=(it.get("notes") or "").strip() or None,
            )
            db.session.add(item)
    order.recalc_total()
    db.session.commit()
    return jsonify(order_schema.dump(order))


@purchases_bp.route("/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    """Elimina una orden (solo draft)."""
    fid = get_or_default_franchisee_id()
    order = PurchaseOrder.query.filter_by(id=order_id, franchisee_id=fid).first() if fid else None
    if not order:
        return jsonify({"error": "Orden no encontrada"}), 404
    if order.status != "draft":
        return jsonify({"error": "Solo se pueden eliminar órdenes en borrador"}), 400
    db.session.delete(order)
    db.session.commit()
    return "", 204


@purchases_bp.route("/suppliers", methods=["GET"])
def list_suppliers():
    """Lista proveedores del franquiciado para órdenes de compra."""
    fid = get_or_default_franchisee_id()
    suppliers = Supplier.query.filter_by(franchisee_id=fid).order_by(Supplier.name).all() if fid else []
    return jsonify(SupplierSchema(many=True).dump(suppliers))


@purchases_bp.route("/spending", methods=["GET"])
def spending_report():
    """
    Reporte de gastos en compras. Histórico por órdenes recibidas.
    Query: ?from=YYYY-MM-DD&to=YYYY-MM-DD&supplier_id=&format=json|csv
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"total": 0, "orders": [], "count": 0})
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    supplier_id = request.args.get("supplier_id", type=int)
    fmt = (request.args.get("format") or "json").lower()

    query = PurchaseOrder.query.filter_by(franchisee_id=fid).filter(
        PurchaseOrder.status.in_(["received", "sent"])
    )
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    if date_from:
        try:
            d = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.order_date >= d)
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(PurchaseOrder.order_date < d)
        except ValueError:
            pass
    orders = query.order_by(PurchaseOrder.order_date.desc()).all()
    total = sum(o.total or 0 for o in orders)
    payload = {
        "total": round(total, 2),
        "count": len(orders),
        "orders": [{
            "id": o.id,
            "order_number": o.order_number,
            "order_date": o.order_date.isoformat() if o.order_date else None,
            "supplier": o.supplier.name if o.supplier else None,
            "total": o.total,
            "status": o.status,
        } for o in orders],
    }
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Nº Orden", "Fecha", "Proveedor", "Total", "Estado"])
        for o in orders:
            w.writerow([
                o.order_number or o.id,
                o.order_date.strftime("%Y-%m-%d") if o.order_date else "",
                o.supplier.name if o.supplier else "",
                o.total or 0,
                o.status or "",
            ])
        w.writerow([])
        w.writerow(["TOTAL GASTOS", "", "", total, ""])
        buf.seek(0)
        body = "\ufeff" + buf.getvalue()
        return Response(
            body,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=reporte_gastos_compras.csv"},
        )
    return jsonify(payload)


@purchases_bp.route("/top-items-weekly", methods=["GET"])
def top_items_weekly():
    """
    Ítems más comprados por semana (para gráficos).
    Query: ?weeks=4 (últimas N semanas, default 4)
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"weeks": [], "items": []})
    weeks_count = request.args.get("weeks", 4, type=int)
    weeks_count = max(1, min(12, weeks_count))

    # Semanas: lunes a domingo
    today = datetime.utcnow().date()
    result = []
    for i in range(weeks_count):
        week_start = today - timedelta(days=today.weekday() + 7 * i)  # Lunes
        week_end = week_start + timedelta(days=6)  # Domingo
        week_label = f"{week_start.strftime('%d/%m')}-{week_end.strftime('%d/%m')}"
        week_end_next = week_start + timedelta(days=7)
        orders = PurchaseOrder.query.filter_by(franchisee_id=fid).filter(
            PurchaseOrder.status.in_(["received", "sent"]),
            PurchaseOrder.order_date >= datetime.combine(week_start, datetime.min.time()),
            PurchaseOrder.order_date < datetime.combine(week_end_next, datetime.min.time()),
        ).all()
        items_qty = {}
        for o in orders:
            for it in o.items:
                name = (it.product_name or "").strip() or "Sin nombre"
                items_qty[name] = items_qty.get(name, 0) + float(it.quantity or 0)
        top = sorted(items_qty.items(), key=lambda x: -x[1])[:10]
        result.append({
            "week": week_label,
            "week_start": week_start.isoformat(),
            "items": [{"product": k, "quantity": round(v, 2)} for k, v in top],
        })
    return jsonify({"weeks": result})
