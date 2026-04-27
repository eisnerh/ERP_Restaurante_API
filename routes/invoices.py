"""API de facturación electrónica."""
from decimal import Decimal
from flask import Blueprint, request, jsonify
from sqlalchemy import text

from extensions import db
from models import Invoice, InvoiceItem, Order, OrderItem, Client, Table
from utils.franchisee import get_or_default_franchisee_id
from utils.hacienda import HaciendaService

invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/invoices")


def _allocate_next_invoice_hacienda_seq(franchisee_id: int) -> int:
    """
    Reserva atómicamente el siguiente consecutivo numérico para la franquicia.
    Requiere restricción UNIQUE(franchisee_id) en app_settings (ver scripts/migrate_invoice_hacienda_seq.py).
    """
    row = db.session.execute(
        text(
            """
            INSERT INTO app_settings (franchisee_id, app_name, invoice_hacienda_last_seq)
            VALUES (:fid, 'ERP Raul Castaño', 1)
            ON CONFLICT (franchisee_id) DO UPDATE
            SET invoice_hacienda_last_seq = app_settings.invoice_hacienda_last_seq + 1
            RETURNING invoice_hacienda_last_seq
            """
        ),
        {"fid": franchisee_id},
    ).fetchone()
    if row is None:
        raise RuntimeError("No se pudo asignar consecutivo de factura")
    return int(row[0])


@invoices_bp.route("", methods=["GET"])
def list_invoices():
    """Lista facturas emitidas del franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    tipo = request.args.get("tipo")
    search = request.args.get("search")
    limit = min(request.args.get("limit", 50, type=int), 200)

    q = Invoice.query.filter_by(franchisee_id=fid)
    if tipo:
        q = q.filter(Invoice.tipo_documento == tipo)
    if search:
        s = f"%{search.strip()}%"
        q = q.filter(
            (Invoice.consecutivo.ilike(s)) | (Invoice.clave.ilike(s))
        )
    invoices = q.order_by(Invoice.created_at.desc()).limit(limit).all()

    def inv_to_dict(inv):
        return {
            "id": inv.id,
            "cliente_id": inv.cliente_id,
            "order_id": inv.order_id,
            "tipo_documento": inv.tipo_documento,
            "clave": inv.clave,
            "consecutivo": inv.consecutivo,
            "estado_hacienda": inv.estado_hacienda,
            "is_simulated": inv.is_simulated,
            "total": float(inv.total or 0),
            "subtotal": float(inv.subtotal or 0),
            "impuesto": float(inv.impuesto or 0),
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
    return jsonify([inv_to_dict(i) for i in invoices])


@invoices_bp.route("", methods=["POST"])
def create_invoice():
    """
    Crea una factura desde un pedido.
    Body: { "order_id": 1, "cliente_id": null, "tipo_documento": "FE" }
    En modo simulación genera clave y consecutivo local sin enviar a Hacienda.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400

    data = request.get_json() or {}
    order_id = data.get("order_id")
    cliente_id = data.get("cliente_id")
    tipo_documento = data.get("tipo_documento", "FE")

    if not order_id:
        return jsonify({"error": "order_id es obligatorio"}), 400
    if tipo_documento not in ("FE", "TE", "NC", "ND"):
        return jsonify({"error": "tipo_documento debe ser FE, TE, NC o ND"}), 400

    order = Order.query.join(Table).filter(Order.id == order_id, Table.franchisee_id == fid).first()
    if not order:
        return jsonify({"error": "Pedido no encontrado"}), 404

    existente = Invoice.query.filter_by(order_id=order_id, franchisee_id=fid).first()
    if existente:
        return jsonify({
            "error": "Este pedido ya tiene una factura emitida. Use Imprimir para reimprimirla.",
            "invoice_id": existente.id,
            "consecutivo": existente.consecutivo,
        }), 400

    client = None
    if cliente_id:
        client = Client.query.filter_by(id=cliente_id, franchisee_id=fid).first()

    total = Decimal("0")
    subtotal = Decimal("0")
    items_data = []
    for oi in order.items:
        st = Decimal(str(oi.quantity or 1)) * Decimal(str(oi.unit_price or 0))
        tax = st * Decimal("0.13")  # IVA 13% CR
        total += st + tax
        subtotal += st
        dish_name = oi.dish.name if oi.dish else "Producto"
        items_data.append({
            "dish_id": oi.dish_id,
            "description": dish_name,
            "quantity": oi.quantity,
            "unit_price": oi.unit_price,
            "subtotal": float(st),
            "tax": float(tax),
        })

    next_seq = _allocate_next_invoice_hacienda_seq(fid)
    hacienda = HaciendaService()
    result = hacienda.emitir_documento(
        tipo=tipo_documento,
        cliente=client,
        items=items_data,
        total=float(total),
        subtotal=float(subtotal),
        consecutivo_num=next_seq,
    )

    inv = Invoice(
        franchisee_id=fid,
        cliente_id=cliente_id or None,
        order_id=order.id,
        tipo_documento=tipo_documento,
        clave=result.get("clave"),
        consecutivo=result.get("consecutivo"),
        estado_hacienda=result.get("estado"),
        is_simulated=result.get("simulado", True),
        total=total,
        subtotal=subtotal,
        impuesto=total - subtotal,
    )
    db.session.add(inv)
    db.session.flush()

    for it in items_data:
        item = InvoiceItem(
            invoice_id=inv.id,
            dish_id=it.get("dish_id"),
            description=it["description"],
            quantity=it["quantity"],
            unit_price=it["unit_price"],
            subtotal=Decimal(str(it["subtotal"])),
            tax=Decimal(str(it["tax"])),
        )
        db.session.add(item)
    db.session.commit()
    db.session.refresh(inv)

    return jsonify({
        "id": inv.id,
        "cliente_id": inv.cliente_id,
        "order_id": inv.order_id,
        "tipo_documento": inv.tipo_documento,
        "clave": inv.clave,
        "consecutivo": inv.consecutivo,
        "estado_hacienda": inv.estado_hacienda,
        "is_simulated": inv.is_simulated,
        "total": float(inv.total or 0),
        "subtotal": float(inv.subtotal or 0),
        "impuesto": float(inv.impuesto or 0),
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "items": [
            {"description": it.description, "quantity": float(it.quantity), "unit_price": float(it.unit_price), "subtotal": float(it.subtotal or 0)}
            for it in inv.items
        ],
    }), 201


@invoices_bp.route("/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    """Obtiene detalle de una factura."""
    fid = get_or_default_franchisee_id()
    inv = Invoice.query.filter_by(id=invoice_id, franchisee_id=fid).first_or_404()
    return jsonify({
        "id": inv.id,
        "cliente_id": inv.cliente_id,
        "order_id": inv.order_id,
        "tipo_documento": inv.tipo_documento,
        "clave": inv.clave,
        "consecutivo": inv.consecutivo,
        "estado_hacienda": inv.estado_hacienda,
        "is_simulated": inv.is_simulated,
        "total": float(inv.total or 0),
        "subtotal": float(inv.subtotal or 0),
        "impuesto": float(inv.impuesto or 0),
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "items": [
            {"id": it.id, "description": it.description, "quantity": float(it.quantity), "unit_price": float(it.unit_price), "subtotal": float(it.subtotal or 0)}
            for it in inv.items
        ],
    })
