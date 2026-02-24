"""API de franquiciados."""
from sqlalchemy import or_
from flask import Blueprint, request, jsonify
from extensions import db
from models import Franchisee
from utils.franchisee import set_current_franchisee_id, get_current_franchisee_id

franchisees_bp = Blueprint("franchisees", __name__, url_prefix="/api/franchisees")


@franchisees_bp.route("", methods=["GET"])
def list_franchisees():
    """Lista franquiciados. Query: ?active=1|0, ?q=buscar."""
    q = (request.args.get("q") or "").strip()
    active = request.args.get("active")
    query = Franchisee.query.order_by(Franchisee.name)
    if q:
        query = query.filter(
            or_(
                Franchisee.name.ilike(f"%{q}%"),
                Franchisee.code.ilike(f"%{q}%"),
            )
        )
    if active is not None:
        query = query.filter(Franchisee.active == (active in ("1", "true", "yes")))
    franchisees = query.all()
    return jsonify([{
        "id": f.id,
        "code": f.code or "",
        "name": f.name,
        "address": f.address or "",
        "phone": f.phone or "",
        "email": f.email or "",
        "active": f.active,
    } for f in franchisees])


@franchisees_bp.route("", methods=["POST"])
def create_franchisee():
    """Crea un franquiciado. Body: code, name, address, phone, email, active."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    code = (data.get("code") or "").strip() or None
    if code and Franchisee.query.filter_by(code=code).first():
        return jsonify({"error": "Ya existe un franquiciado con ese código"}), 400
    f = Franchisee(
        code=code,
        name=name,
        address=(data.get("address") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
        active=data.get("active", True),
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({"id": f.id, "code": f.code, "name": f.name}), 201


@franchisees_bp.route("/<int:fid>", methods=["GET"])
def get_franchisee(fid):
    """Obtiene un franquiciado."""
    f = Franchisee.query.get_or_404(fid)
    return jsonify({
        "id": f.id, "code": f.code or "", "name": f.name,
        "address": f.address or "", "phone": f.phone or "", "email": f.email or "",
        "active": f.active,
    })


@franchisees_bp.route("/<int:fid>", methods=["PUT"])
def update_franchisee(fid):
    """Actualiza un franquiciado."""
    f = Franchisee.query.get_or_404(fid)
    data = request.get_json() or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "El nombre no puede estar vacío"}), 400
        f.name = name
    if "code" in data:
        code = (data.get("code") or "").strip() or None
        if code:
            other = Franchisee.query.filter(Franchisee.code == code, Franchisee.id != fid).first()
            if other:
                return jsonify({"error": "Ya existe otro franquiciado con ese código"}), 400
        f.code = code
    if "address" in data:
        f.address = (data.get("address") or "").strip() or None
    if "phone" in data:
        f.phone = (data.get("phone") or "").strip() or None
    if "email" in data:
        f.email = (data.get("email") or "").strip() or None
    if "active" in data:
        f.active = bool(data.get("active"))
    db.session.commit()
    return jsonify({"id": f.id, "code": f.code, "name": f.name})


@franchisees_bp.route("/<int:fid>", methods=["DELETE"])
def delete_franchisee(fid):
    """Desactiva un franquiciado (soft delete)."""
    f = Franchisee.query.get_or_404(fid)
    f.active = False
    db.session.commit()
    return "", 204


@franchisees_bp.route("/current", methods=["GET"])
def get_current():
    """Obtiene el franquiciado actualmente seleccionado."""
    fid = get_current_franchisee_id()
    if not fid:
        return jsonify({"franchisee_id": None, "franchisee": None})
    f = Franchisee.query.get(fid)
    if not f:
        return jsonify({"franchisee_id": None, "franchisee": None})
    return jsonify({
        "franchisee_id": f.id,
        "franchisee": {"id": f.id, "code": f.code or "", "name": f.name},
    })


@franchisees_bp.route("/current", methods=["POST"])
def set_current():
    """Establece el franquiciado actual. Body: { franchisee_id: 1 }."""
    data = request.get_json() or {}
    fid = data.get("franchisee_id")
    if fid is None:
        from utils.franchisee import clear_current_franchisee
        clear_current_franchisee()
        return jsonify({"franchisee_id": None})
    f = Franchisee.query.get(fid)
    if not f or not f.active:
        return jsonify({"error": "Franquiciado no encontrado o inactivo"}), 404
    set_current_franchisee_id(f.id)
    return jsonify({"franchisee_id": f.id, "franchisee": {"id": f.id, "code": f.code or "", "name": f.name}})
