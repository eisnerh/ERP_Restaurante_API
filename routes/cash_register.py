"""API de caja: apertura, cierre e historial. Arqueo Z."""
import json
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, jsonify
from sqlalchemy import func

from extensions import db
from models import CashRegisterSession, Order, OrderItem, OperationalExpense, Table, Category, Dish
from utils.franchisee import get_or_default_franchisee_id

cash_register_bp = Blueprint("cash_register", __name__, url_prefix="/api/cash-register")

# Denominaciones Colón para desglose
COLON_DENOMINATIONS = [20000, 10000, 5000, 2000, 1000, 500, 100, 50, 25]


def _session_to_json(session):
    """Convierte sesión a dict para JSON."""
    return {
        "id": session.id,
        "franchisee_id": session.franchisee_id,
        "opened_at": session.opened_at.isoformat() if session.opened_at else None,
        "closed_at": session.closed_at.isoformat() if session.closed_at else None,
        "opening_balance": float(session.opening_balance or 0),
        "closing_balance": float(session.closing_balance) if session.closing_balance else None,
        "expected_balance": float(session.expected_balance) if session.expected_balance else None,
        "difference": float(session.difference) if session.difference else None,
        "notes": session.notes,
        "arqueo_number": getattr(session, "arqueo_number", None),
    }


@cash_register_bp.route("/current", methods=["GET"])
def get_current_session():
    """Obtiene la caja abierta del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"open": False, "session": None})

    session = (
        CashRegisterSession.query.filter_by(franchisee_id=fid, closed_at=None)
        .order_by(CashRegisterSession.opened_at.desc())
        .first()
    )
    if not session:
        return jsonify({"open": False, "session": None})

    # Ventas cobradas de esta caja (orders paid con cash_register_id)
    sales = (
        db.session.query(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0))
        .join(Order, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Order.cash_register_id == session.id,
            Order.status == "paid",
        )
        .scalar() or 0
    )
    expenses_sum = (
        db.session.query(func.coalesce(func.sum(OperationalExpense.amount), 0))
        .filter(OperationalExpense.cash_register_id == session.id)
        .scalar() or 0
    )
    expected = float(session.opening_balance) + float(sales) - float(expenses_sum)
    return jsonify({
        "open": True,
        "session": {
            "id": session.id,
            "opened_at": session.opened_at.isoformat() if session.opened_at else None,
            "opening_balance": float(session.opening_balance),
            "sales": float(sales),
            "expenses": float(expenses_sum),
            "expected_balance": expected,
        },
    })


@cash_register_bp.route("/suggested-opening", methods=["GET"])
def get_suggested_opening():
    """Devuelve el monto sugerido para abrir caja (cierre anterior del franquiciado)."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"suggested_balance": 0})

    last = (
        CashRegisterSession.query.filter_by(franchisee_id=fid)
        .filter(CashRegisterSession.closed_at.isnot(None))
        .order_by(CashRegisterSession.closed_at.desc())
        .first()
    )
    if not last or last.closing_balance is None:
        return jsonify({"suggested_balance": 0})
    return jsonify({"suggested_balance": float(last.closing_balance)})


@cash_register_bp.route("", methods=["POST"])
def open_session():
    """Abre una nueva sesión de caja. Solo si no hay otra abierta para el franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400

    existing = (
        CashRegisterSession.query.filter_by(franchisee_id=fid)
        .filter(CashRegisterSession.closed_at.is_(None))
        .first()
    )
    if existing:
        return jsonify({"error": "Ya tienes una caja abierta. Ciérrala primero."}), 400

    data = request.get_json() or {}
    opening = float(data.get("opening_balance", 0))
    session = CashRegisterSession(franchisee_id=fid, opening_balance=opening)
    db.session.add(session)
    db.session.commit()
    return jsonify(_session_to_json(session)), 201


def _compute_arqueo_data(session, fid):
    """Calcula datos para Arqueo Z: ventas por tipo de pago, por familia, etc."""
    orders = (
        Order.query.join(Table)
        .filter(Table.franchisee_id == fid, Order.cash_register_id == session.id, Order.status == "paid")
        .all()
    )
    expenses = OperationalExpense.query.filter_by(cash_register_id=session.id).all()

    # Ventas por tipo de pago
    sales_by_type = {}
    for o in orders:
        total = sum(float(i.quantity or 0) * float(i.unit_price or 0) for i in o.items)
        pt = o.payment_type or "efectivo"
        sales_by_type[pt] = sales_by_type.get(pt, 0) + total

    # Gastos en efectivo (salidas)
    cash_out_efectivo = sum(float(e.amount or 0) for e in expenses if (e.payment_type or "efectivo") == "efectivo")
    cash_out_total = sum(float(e.amount or 0) for e in expenses)

    ventas_efectivo = sales_by_type.get("efectivo", 0)
    fianza = float(session.opening_balance or 0)
    cash_in = float(session.cash_in or 0)
    cash_out_val = float(session.cash_out) if session.cash_out is not None else cash_out_total

    total_calc_efectivo = fianza + ventas_efectivo + cash_in - cash_out_val

    payment_labels = {
        "efectivo": "Efectivo",
        "sinpe": "SINPE Movil",
        "tarjeta_credito": "Tarjeta",
        "tarjeta_debito": "Tarjeta",
        "pendiente": "Pendiente",
    }

    resumen_moneda = []
    total_calc = 0
    for pt, label in payment_labels.items():
        calc = total_calc_efectivo if pt == "efectivo" else sales_by_type.get(pt, 0)
        total_calc += calc
        resumen_moneda.append({
            "tipo": pt,
            "label": label,
            "calculado": round(calc, 2),
            "declarado": None,
        })
    # Ajustar: total calculado general incluye todas las ventas
    total_calc_all = fianza + sum(sales_by_type.values()) + cash_in - cash_out_val

    # Ventas por familia (categoría)
    family_sales = {}
    for o in orders:
        for oi in o.items:
            cat_name = "Sin categoría"
            if oi.dish_id and oi.dish:
                cat = oi.dish.category if hasattr(oi.dish, "category") else None
                if cat:
                    cat_name = cat.name or "Sin categoría"
            subtotal = float(oi.quantity or 0) * float(oi.unit_price or 0)
            if cat_name not in family_sales:
                family_sales[cat_name] = {"unidades": 0, "monto": 0}
            family_sales[cat_name]["unidades"] += int(oi.quantity or 0)
            family_sales[cat_name]["monto"] += subtotal

    ventas_por_familia = [
        {"familia": k, "unidades": v["unidades"], "monto": round(v["monto"], 2)}
        for k, v in sorted(family_sales.items(), key=lambda x: -x[1]["monto"])
    ]

    # Número de arqueo Z (siguiente si no cerrada)
    next_arqueo = db.session.query(func.coalesce(func.max(CashRegisterSession.arqueo_number), 0)).filter_by(
        franchisee_id=fid
    ).scalar() or 0
    if session.closed_at and session.arqueo_number:
        next_arqueo = session.arqueo_number
    else:
        next_arqueo = int(next_arqueo) + 1

    return {
        "session_id": session.id,
        "arqueo_number": session.arqueo_number or next_arqueo,
        "opened_at": session.opened_at.isoformat() if session.opened_at else None,
        "closed_at": session.closed_at.isoformat() if session.closed_at else None,
        "fianza": fianza,
        "ventas_efectivo": round(ventas_efectivo, 2),
        "ventas_total": round(sum(sales_by_type.values()), 2),
        "cash_in": round(cash_in, 2),
        "cash_out": round(cash_out_val, 2),
        "total_calculado_efectivo": round(total_calc_efectivo, 2),
        "total_calculado_general": round(total_calc_all, 2),
        "resumen_moneda": resumen_moneda,
        "ventas_por_familia": ventas_por_familia,
        "total_pedidos": len(orders),
        "denominations": COLON_DENOMINATIONS,
    }


@cash_register_bp.route("/<int:session_id>/arqueo-data", methods=["GET"])
def get_arqueo_data(session_id):
    """Datos completos para el wizard Arqueo Z: calculados, resumen por moneda, ventas por familia."""
    fid = get_or_default_franchisee_id()
    session = CashRegisterSession.query.filter_by(id=session_id, franchisee_id=fid).first_or_404()
    data = _compute_arqueo_data(session, fid)
    # Si ya se cerró, incluir declarados y descuadres
    if session.declared_json:
        try:
            declared = json.loads(session.declared_json)
            for r in data["resumen_moneda"]:
                decl = declared.get(r["tipo"])
                if decl is not None:
                    r["declarado"] = decl
                    calc = r["calculado"]
                    r["descuadre"] = round(decl - calc, 2)
        except (json.JSONDecodeError, TypeError):
            pass
    return jsonify(data)


@cash_register_bp.route("/<int:session_id>/detail", methods=["GET"])
def get_session_detail(session_id):
    """Detalle de una sesión: ventas (pedidos) y gastos operacionales."""
    fid = get_or_default_franchisee_id()
    session = CashRegisterSession.query.filter_by(id=session_id, franchisee_id=fid).first_or_404()

    orders = (
        Order.query.join(Table)
        .filter(Table.franchisee_id == fid, Order.cash_register_id == session_id, Order.status == "paid")
        .order_by(Order.updated_at.asc())
        .all()
    )
    expenses = OperationalExpense.query.filter_by(cash_register_id=session_id).order_by(OperationalExpense.created_at.asc()).all()

    sales_total = sum(float(oi.quantity or 0) * float(oi.unit_price or 0) for o in orders for oi in o.items)
    expenses_total = sum(float(e.amount or 0) for e in expenses)

    return jsonify({
        "session": {
            "id": session.id,
            "opened_at": session.opened_at.isoformat() if session.opened_at else None,
            "closed_at": session.closed_at.isoformat() if session.closed_at else None,
            "opening_balance": float(session.opening_balance or 0),
            "closing_balance": float(session.closing_balance) if session.closing_balance else None,
            "expected_balance": float(session.expected_balance) if session.expected_balance else None,
            "difference": float(session.difference) if session.difference is not None else None,
            "arqueo_number": getattr(session, "arqueo_number", None),
            "sales_total": sales_total,
            "expenses_total": expenses_total,
        },
        "orders": [
            {
                "id": o.id,
                "total": sum(float(i.quantity or 0) * float(i.unit_price or 0) for i in o.items),
                "payment_type": o.payment_type or "efectivo",
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in orders
        ],
        "expenses": [
            {
                "id": e.id,
                "amount": float(e.amount),
                "description": e.description,
                "payment_type": e.payment_type,
                "purchase_order_id": e.purchase_order_id,
                "purchase_order": {
                    "id": e.purchase_order.id,
                    "order_number": e.purchase_order.order_number,
                    "supplier_name": e.purchase_order.supplier.name if e.purchase_order.supplier else None,
                } if e.purchase_order else None,
            }
            for e in expenses
        ],
    })


@cash_register_bp.route("/<int:session_id>/report-pdf", methods=["GET"])
def get_session_report_pdf(session_id):
    """Genera PDF del reporte de cierre de caja."""
    from flask import Response
    from utils.cash_register_pdf import build_cash_register_report_pdf

    fid = get_or_default_franchisee_id()
    session = CashRegisterSession.query.filter_by(id=session_id, franchisee_id=fid).first_or_404()

    # Obtener detalle (reutilizando lógica)
    orders = (
        Order.query.join(Table)
        .filter(Table.franchisee_id == fid, Order.cash_register_id == session_id, Order.status == "paid")
        .order_by(Order.updated_at.asc())
        .all()
    )
    expenses = OperationalExpense.query.filter_by(cash_register_id=session_id).order_by(OperationalExpense.created_at.asc()).all()
    sales_total = sum(float(oi.quantity or 0) * float(oi.unit_price or 0) for o in orders for oi in o.items)
    expenses_total = sum(float(e.amount or 0) for e in expenses)

    detail_data = {
        "session": {
            "id": session.id,
            "opened_at": session.opened_at.isoformat() if session.opened_at else None,
            "closed_at": session.closed_at.isoformat() if session.closed_at else None,
            "opening_balance": float(session.opening_balance or 0),
            "closing_balance": float(session.closing_balance) if session.closing_balance else None,
            "expected_balance": float(session.expected_balance) if session.expected_balance else None,
            "difference": float(session.difference) if session.difference is not None else None,
            "arqueo_number": getattr(session, "arqueo_number", None),
            "sales_total": sales_total,
            "expenses_total": expenses_total,
        },
        "orders": [
            {
                "id": o.id,
                "total": sum(float(i.quantity or 0) * float(i.unit_price or 0) for i in o.items),
                "payment_type": o.payment_type or "efectivo",
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in orders
        ],
        "expenses": [
            {
                "id": e.id,
                "amount": float(e.amount),
                "description": e.description,
                "payment_type": e.payment_type,
                "purchase_order_id": e.purchase_order_id,
                "purchase_order": {
                    "id": e.purchase_order.id,
                    "order_number": e.purchase_order.order_number,
                    "supplier_name": e.purchase_order.supplier.name if e.purchase_order.supplier else None,
                } if e.purchase_order else None,
            }
            for e in expenses
        ],
    }

    arqueo_data = None
    if session.closed_at:
        arqueo_data = _compute_arqueo_data(session, fid)
        if session.declared_json:
            try:
                declared = json.loads(session.declared_json)
                for r in arqueo_data.get("resumen_moneda", []):
                    decl = declared.get(r["tipo"])
                    if decl is not None:
                        r["declarado"] = decl
            except (json.JSONDecodeError, TypeError):
                pass

    try:
        pdf_bytes = build_cash_register_report_pdf(detail_data, arqueo_data)
    except Exception as e:
        return jsonify({"error": f"Error al generar PDF: {e}"}), 500

    fecha = session.closed_at or session.opened_at
    fecha_str = fecha.strftime("%Y%m%d_%H%M") if fecha else "reporte"
    filename = f"cierre_caja_{session_id}_{fecha_str}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@cash_register_bp.route("/<int:session_id>/close", methods=["POST"])
def close_session(session_id):
    """
    Cierra la sesión de caja. Acepta:
    - closing_balance: monto total contado (simple)
    - O arqueo completo: declared (dict por tipo pago), cash_breakdown, retirada, new_fianza
    """
    fid = get_or_default_franchisee_id()
    session = CashRegisterSession.query.filter_by(id=session_id, franchisee_id=fid).first_or_404()

    if session.closed_at:
        return jsonify({"error": "Esta caja ya está cerrada"}), 400

    data = request.get_json() or {}

    # Calcular ventas y gastos
    sales = (
        db.session.query(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0))
        .join(Order, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Order.cash_register_id == session.id,
            Order.status == "paid",
        )
        .scalar() or 0
    )
    expenses_sum = (
        db.session.query(func.coalesce(func.sum(OperationalExpense.amount), 0))
        .filter(OperationalExpense.cash_register_id == session.id)
        .scalar() or 0
    )
    expected = float(session.opening_balance) + float(sales) - float(expenses_sum)

    # Arqueo Z completo o cierre simple
    declared = data.get("declared")  # {efectivo: 123110, tarjeta: 566223, ...}
    if declared:
        total_declared = sum(float(v or 0) for v in declared.values())
        closing = total_declared
        session.declared_json = json.dumps(declared)
        session.cash_breakdown_json = json.dumps(data.get("cash_breakdown", [])) if data.get("cash_breakdown") else None
        session.retirada = Decimal(str(data.get("retirada", 0))) if data.get("retirada") is not None else None
        session.new_fianza = Decimal(str(data.get("new_fianza", 0))) if data.get("new_fianza") is not None else None
        next_z = db.session.query(func.coalesce(func.max(CashRegisterSession.arqueo_number), 0)).filter_by(
            franchisee_id=fid
        ).scalar() or 0
        session.arqueo_number = int(next_z) + 1
    else:
        closing = float(data.get("closing_balance", 0))

    diff = Decimal(str(closing - expected))

    session.closed_at = datetime.utcnow()
    session.closing_balance = Decimal(str(closing))
    session.expected_balance = Decimal(str(expected))
    session.difference = diff
    session.notes = data.get("notes")
    db.session.commit()
    return jsonify(_session_to_json(session))


@cash_register_bp.route("", methods=["GET"])
def list_sessions():
    """Lista el historial de sesiones de caja del franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    limit = request.args.get("limit", 50, type=int)
    sessions = (
        CashRegisterSession.query.filter_by(franchisee_id=fid)
        .order_by(CashRegisterSession.opened_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([_session_to_json(s) for s in sessions])
