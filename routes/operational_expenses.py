"""API de gastos operacionales diarios (salidas de caja)."""
from flask import Blueprint, request, jsonify

from extensions import db
from models import OperationalExpense, PurchaseOrder
from utils.franchisee import get_or_default_franchisee_id

operational_expenses_bp = Blueprint("operational_expenses", __name__, url_prefix="/api/operational-expenses")


@operational_expenses_bp.route("", methods=["GET"])
def list_expenses():
    """Lista gastos operacionales del franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])

    cash_register_id = request.args.get("cash_register_id", type=int)
    limit = min(request.args.get("limit", 100, type=int), 500)

    q = OperationalExpense.query.filter_by(franchisee_id=fid)
    if cash_register_id is not None:
        q = q.filter_by(cash_register_id=cash_register_id)
    expenses = q.order_by(OperationalExpense.created_at.desc()).limit(limit).all()

    return jsonify([
        {
            "id": e.id,
            "amount": float(e.amount),
            "description": e.description,
            "payment_type": e.payment_type,
            "cash_register_id": e.cash_register_id,
            "purchase_order_id": e.purchase_order_id,
            "purchase_order": {
                "id": e.purchase_order.id,
                "order_number": e.purchase_order.order_number,
                "supplier_name": e.purchase_order.supplier.name if e.purchase_order.supplier else None,
                "total": float(e.purchase_order.total or 0),
            } if e.purchase_order else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in expenses
    ])


@operational_expenses_bp.route("", methods=["POST"])
def create_expense():
    """
    Registra un gasto operacional.
    Body: { "amount": 10000, "description": "...", "payment_type": "efectivo", "cash_register_id": 1 }
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400

    data = request.get_json() or {}
    amount = data.get("amount")
    if amount is None:
        return jsonify({"error": "amount es obligatorio"}), 400
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount debe ser numérico"}), 400
    if amount < 0:
        return jsonify({"error": "amount debe ser positivo"}), 400

    desc = (data.get("description") or "").strip()
    payment_type = (data.get("payment_type") or "efectivo").strip() or "efectivo"
    cash_register_id = data.get("cash_register_id")
    purchase_order_id = data.get("purchase_order_id")
    if purchase_order_id:
        po = PurchaseOrder.query.filter_by(id=purchase_order_id, franchisee_id=fid).first()
        if not po:
            return jsonify({"error": "Orden de compra no encontrada o no pertenece al franquiciado"}), 400

    expense = OperationalExpense(
        franchisee_id=fid,
        amount=amount,
        description=desc or None,
        payment_type=payment_type,
        cash_register_id=cash_register_id,
        purchase_order_id=purchase_order_id if purchase_order_id else None,
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify({
        "id": expense.id,
        "amount": float(expense.amount),
        "description": expense.description,
        "payment_type": expense.payment_type,
        "cash_register_id": expense.cash_register_id,
        "purchase_order_id": expense.purchase_order_id,
        "purchase_order": {
            "id": expense.purchase_order.id,
            "order_number": expense.purchase_order.order_number,
            "supplier_name": expense.purchase_order.supplier.name if expense.purchase_order.supplier else None,
            "total": float(expense.purchase_order.total or 0),
        } if expense.purchase_order else None,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
    }), 201


@operational_expenses_bp.route("/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    """Elimina un gasto operacional."""
    fid = get_or_default_franchisee_id()
    expense = OperationalExpense.query.filter_by(id=expense_id, franchisee_id=fid).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return "", 204
