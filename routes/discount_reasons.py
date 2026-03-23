"""API de motivos de descuento."""
from flask import Blueprint, request, jsonify

from extensions import db
from models import DiscountReason
from utils.franchisee import get_or_default_franchisee_id

discount_reasons_bp = Blueprint("discount_reasons", __name__, url_prefix="/api/discount-reasons")


def _to_json(dr):
    return {
        "id": dr.id,
        "franchisee_id": dr.franchisee_id,
        "name": dr.name,
        "percentage": dr.percentage,
        "description": dr.description,
        "active": dr.active,
    }


@discount_reasons_bp.route("", methods=["GET"])
def list_discount_reasons():
    """Lista motivos de descuento del franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    items = DiscountReason.query.filter_by(franchisee_id=fid, active=True).order_by(DiscountReason.name.asc()).all()
    include_inactive = request.args.get("all", "").lower() in ("1", "true", "si")
    if include_inactive:
        items = DiscountReason.query.filter_by(franchisee_id=fid).order_by(DiscountReason.name.asc()).all()
    return jsonify([_to_json(d) for d in items])


@discount_reasons_bp.route("", methods=["POST"])
def create_discount_reason():
    """Crea un motivo de descuento."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Nombre es obligatorio"}), 400
    pct = data.get("percentage")
    if pct is not None:
        try:
            pct = float(pct)
        except (TypeError, ValueError):
            pct = None
    dr = DiscountReason(
        franchisee_id=fid,
        name=name,
        percentage=pct,
        description=(data.get("description") or "").strip() or None,
    )
    db.session.add(dr)
    db.session.commit()
    return jsonify(_to_json(dr)), 201


@discount_reasons_bp.route("/<int:dr_id>", methods=["PATCH"])
def update_discount_reason(dr_id):
    """Actualiza un motivo de descuento."""
    fid = get_or_default_franchisee_id()
    dr = DiscountReason.query.filter_by(id=dr_id, franchisee_id=fid).first_or_404()
    data = request.get_json() or {}
    if "name" in data:
        dr.name = (data.get("name") or "").strip() or dr.name
    if "percentage" in data:
        try:
            dr.percentage = float(data["percentage"]) if data["percentage"] is not None else None
        except (TypeError, ValueError):
            pass
    if "description" in data:
        dr.description = (data.get("description") or "").strip() or None
    if "active" in data:
        dr.active = bool(data.get("active"))
    db.session.commit()
    return jsonify(_to_json(dr))


@discount_reasons_bp.route("/<int:dr_id>", methods=["DELETE"])
def delete_discount_reason(dr_id):
    """Desactiva un motivo de descuento."""
    fid = get_or_default_franchisee_id()
    dr = DiscountReason.query.filter_by(id=dr_id, franchisee_id=fid).first_or_404()
    dr.active = False
    db.session.commit()
    return jsonify(_to_json(dr))
