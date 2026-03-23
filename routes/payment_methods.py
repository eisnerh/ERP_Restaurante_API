"""API de medios de pago."""
from flask import Blueprint, request, jsonify

from extensions import db
from models import PaymentMethod
from utils.franchisee import get_or_default_franchisee_id

payment_methods_bp = Blueprint("payment_methods", __name__, url_prefix="/api/payment-methods")


def _to_json(pm):
    return {
        "id": pm.id,
        "franchisee_id": pm.franchisee_id,
        "name": pm.name,
        "code": pm.code,
        "display_order": pm.display_order,
        "active": pm.active,
    }


@payment_methods_bp.route("", methods=["GET"])
def list_payment_methods():
    """Lista medios de pago del franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    items = PaymentMethod.query.filter_by(franchisee_id=fid, active=True).order_by(
        PaymentMethod.display_order.asc(), PaymentMethod.name.asc()
    ).all()
    include_inactive = request.args.get("all", "").lower() in ("1", "true", "si")
    if include_inactive:
        items = PaymentMethod.query.filter_by(franchisee_id=fid).order_by(
            PaymentMethod.display_order.asc(), PaymentMethod.name.asc()
        ).all()
    return jsonify([_to_json(p) for p in items])


@payment_methods_bp.route("", methods=["POST"])
def create_payment_method():
    """Crea un medio de pago."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Nombre es obligatorio"}), 400
    code = (data.get("code") or "").strip() or None
    pm = PaymentMethod(
        franchisee_id=fid,
        name=name,
        code=code,
        display_order=data.get("display_order", 0),
    )
    db.session.add(pm)
    db.session.commit()
    return jsonify(_to_json(pm)), 201


@payment_methods_bp.route("/<int:pm_id>", methods=["PATCH"])
def update_payment_method(pm_id):
    """Actualiza un medio de pago."""
    fid = get_or_default_franchisee_id()
    pm = PaymentMethod.query.filter_by(id=pm_id, franchisee_id=fid).first_or_404()
    data = request.get_json() or {}
    if "name" in data:
        pm.name = (data.get("name") or "").strip() or pm.name
    if "code" in data:
        pm.code = (data.get("code") or "").strip() or None
    if "display_order" in data:
        pm.display_order = data.get("display_order", pm.display_order)
    if "active" in data:
        pm.active = bool(data.get("active"))
    db.session.commit()
    return jsonify(_to_json(pm))


@payment_methods_bp.route("/<int:pm_id>", methods=["DELETE"])
def delete_payment_method(pm_id):
    """Desactiva o elimina un medio de pago."""
    fid = get_or_default_franchisee_id()
    pm = PaymentMethod.query.filter_by(id=pm_id, franchisee_id=fid).first_or_404()
    pm.active = False
    db.session.commit()
    return jsonify(_to_json(pm))
