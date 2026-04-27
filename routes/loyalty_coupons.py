"""API de cupones de fidelización (factura = cupón, QR con token)."""
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Franchisee, LoyaltyCoupon, PayrollLocation

loyalty_bp = Blueprint("loyalty", __name__, url_prefix="/api/loyalty")


def _coupon_to_owner_dict(c: LoyaltyCoupon):
    f = c.franchisee
    loc = c.location
    return {
        "id": c.id,
        "franchisee_id": c.franchisee_id,
        "franchisee_name": f.name if f else "",
        "location_id": c.location_id,
        "location_name": loc.name if loc else None,
        "invoice_number": c.invoice_number,
        "kind": c.kind,
        "discount_percent": float(c.discount_percent) if c.discount_percent is not None else None,
        "discount_amount": float(c.discount_amount) if c.discount_amount is not None else None,
        "reward_description": c.reward_description,
        "public_token": c.public_token,
        "qr_payload": f"fidelitity://coupon/{c.public_token}",
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "redeemed_at": c.redeemed_at.isoformat() if c.redeemed_at else None,
    }


def _coupon_to_client_dict(c: LoyaltyCoupon):
    f = c.franchisee
    loc = c.location
    return {
        "franchisee_id": c.franchisee_id,
        "franchisee_name": f.name if f else "",
        "franchisee_code": f.code or "" if f else "",
        "location_id": c.location_id,
        "location_name": loc.name if loc else None,
        "invoice_number": c.invoice_number,
        "kind": c.kind,
        "discount_percent": float(c.discount_percent) if c.discount_percent is not None else None,
        "discount_amount": float(c.discount_amount) if c.discount_amount is not None else None,
        "reward_description": c.reward_description,
        "status": c.status,
    }


@loyalty_bp.route("/coupons", methods=["POST"])
def create_coupon():
    """
    Crea un cupón. Body JSON:
      franchisee_id (int, requerido),
      invoice_number (str),
      kind: discount | reward,
      discount_percent, discount_amount (opcionales si kind=discount),
      reward_description (si kind=reward),
      location_id (opcional, payroll_locations del franquiciado).
    """
    data = request.get_json() or {}
    fid = data.get("franchisee_id")
    if fid is None:
        return jsonify({"error": "franchisee_id es obligatorio"}), 400
    f = db.session.get(Franchisee, fid)
    if not f or not f.active:
        return jsonify({"error": "Franquiciado no encontrado o inactivo"}), 404

    invoice_number = (data.get("invoice_number") or "").strip()
    if not invoice_number:
        return jsonify({"error": "invoice_number es obligatorio"}), 400

    kind = (data.get("kind") or "").strip().lower()
    if kind not in ("discount", "reward"):
        return jsonify({"error": "kind debe ser discount o reward"}), 400

    location_id = data.get("location_id")
    if location_id is not None:
        loc = PayrollLocation.query.filter_by(id=location_id, franchisee_id=fid).first()
        if not loc:
            return jsonify({"error": "Ubicación no válida para este franquiciado"}), 400

    active = LoyaltyCoupon.query.filter_by(
        franchisee_id=fid, invoice_number=invoice_number, status="active"
    ).first()
    if active:
        return jsonify({"error": "Ya existe un cupón activo para esta factura en esta franquicia"}), 409

    raw_pct = data.get("discount_percent")
    raw_amt = data.get("discount_amount")
    reward_description = (data.get("reward_description") or "").strip() or None
    dp = da = None

    if kind == "discount":
        has_pct = raw_pct is not None and str(raw_pct).strip() != ""
        has_amt = raw_amt is not None and str(raw_amt).strip() != ""
        if not has_pct and not has_amt:
            return jsonify({"error": "Indique discount_percent o discount_amount"}), 400
        if has_pct:
            dp = Decimal(str(raw_pct))
            if dp < 0 or dp > 100:
                return jsonify({"error": "discount_percent debe estar entre 0 y 100"}), 400
        if has_amt:
            da = Decimal(str(raw_amt))
            if da < 0:
                return jsonify({"error": "discount_amount no puede ser negativo"}), 400
        reward_description = None
    else:
        if not reward_description:
            return jsonify({"error": "reward_description es obligatorio para kind=reward"}), 400

    token = LoyaltyCoupon.generate_token()
    c = LoyaltyCoupon(
        franchisee_id=fid,
        location_id=location_id,
        invoice_number=invoice_number,
        kind=kind,
        discount_percent=dp,
        discount_amount=da,
        reward_description=reward_description,
        public_token=token,
        status="active",
    )
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo crear el cupón (duplicado o conflicto)"}), 409

    return jsonify(_coupon_to_owner_dict(c)), 201


@loyalty_bp.route("/coupons", methods=["GET"])
def list_coupons():
    """Lista cupones del franquiciado. Query: franchisee_id (requerido), status=active|redeemed|all."""
    fid = request.args.get("franchisee_id", type=int)
    if not fid:
        return jsonify({"error": "franchisee_id es obligatorio"}), 400
    status = (request.args.get("status") or "all").lower()
    q = LoyaltyCoupon.query.filter_by(franchisee_id=fid).order_by(LoyaltyCoupon.created_at.desc())
    if status in ("active", "redeemed", "cancelled"):
        q = q.filter(LoyaltyCoupon.status == status)
    coupons = q.limit(200).all()
    return jsonify([_coupon_to_owner_dict(c) for c in coupons])


@loyalty_bp.route("/coupons/resolve", methods=["GET"])
def resolve_coupon():
    """Obtiene datos del cupón para el cliente. Query: token=."""
    token = (request.args.get("token") or "").strip()
    if not token:
        return jsonify({"error": "token es obligatorio"}), 400
    # Permitir token crudo o URL fidelitity://coupon/TOKEN
    if token.startswith("fidelitity://coupon/"):
        token = token.split("fidelitity://coupon/", 1)[-1].strip()
    c = LoyaltyCoupon.query.filter_by(public_token=token).first()
    if not c:
        return jsonify({"error": "Cupón no encontrado"}), 404
    return jsonify(_coupon_to_client_dict(c))


@loyalty_bp.route("/coupons/redeem", methods=["POST"])
def redeem_coupon():
    """Canjea un cupón. Body: { \"token\": \"...\" }."""
    data = request.get_json() or {}
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"error": "token es obligatorio"}), 400
    if token.startswith("fidelitity://coupon/"):
        token = token.split("fidelitity://coupon/", 1)[-1].strip()
    c = LoyaltyCoupon.query.filter_by(public_token=token).first()
    if not c:
        return jsonify({"error": "Cupón no encontrado"}), 404
    if c.status != "active":
        return jsonify({"error": f"Cupón no disponible (estado: {c.status})"}), 409

    from datetime import datetime, timezone

    c.status = "redeemed"
    c.redeemed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"ok": True, "coupon": _coupon_to_client_dict(c)})


@loyalty_bp.route("/locations", methods=["GET"])
def list_locations_for_franchisee():
    """Ubicaciones (planilla) del franquiciado para aplicar el cupón. Query: franchisee_id=."""
    fid = request.args.get("franchisee_id", type=int)
    if not fid:
        return jsonify({"error": "franchisee_id es obligatorio"}), 400
    f = db.session.get(Franchisee, fid)
    if not f:
        return jsonify({"error": "Franquiciado no encontrado"}), 404
    locs = PayrollLocation.query.filter_by(franchisee_id=fid).order_by(
        PayrollLocation.display_order, PayrollLocation.name
    ).all()
    return jsonify([{"id": l.id, "name": l.name} for l in locs])
