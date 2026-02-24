"""API de franquiciados."""
from sqlalchemy import or_
from flask import Blueprint, request, jsonify
from extensions import db
from models import Franchisee, PayrollLocation
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
    result = []
    for f in franchisees:
        loc_count = PayrollLocation.query.filter_by(franchisee_id=f.id).count()
        result.append({
            "id": f.id,
            "code": f.code or "",
            "name": f.name,
            "address": f.address or "",
            "phone": f.phone or "",
            "email": f.email or "",
            "active": f.active,
            "locations_count": loc_count,
        })
    return jsonify(result)


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
    """Obtiene un franquiciado con sus lugares de trabajo."""
    f = db.get_or_404(Franchisee, fid)
    locations = PayrollLocation.query.filter_by(franchisee_id=f.id).order_by(
        PayrollLocation.display_order, PayrollLocation.name
    ).all()
    return jsonify({
        "id": f.id, "code": f.code or "", "name": f.name,
        "address": f.address or "", "phone": f.phone or "", "email": f.email or "",
        "active": f.active,
        "locations": [{"id": l.id, "name": l.name, "display_order": l.display_order} for l in locations],
    })


@franchisees_bp.route("/<int:fid>/locations", methods=["GET"])
def list_franchisee_locations(fid):
    """Lista los lugares de trabajo de un franquiciado."""
    f = db.get_or_404(Franchisee, fid)
    locations = PayrollLocation.query.filter_by(franchisee_id=f.id).order_by(
        PayrollLocation.display_order, PayrollLocation.name
    ).all()
    return jsonify([{"id": l.id, "name": l.name, "display_order": l.display_order} for l in locations])


@franchisees_bp.route("/<int:fid>/locations", methods=["POST"])
def create_franchisee_location(fid):
    """Crea un lugar de trabajo para el franquiciado."""
    f = db.get_or_404(Franchisee, fid)
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    existing = PayrollLocation.query.filter_by(franchisee_id=f.id, name=name).first()
    if existing:
        return jsonify({"error": "Ya existe un lugar con ese nombre"}), 400
    loc = PayrollLocation(franchisee_id=f.id, name=name, display_order=data.get("display_order", 0))
    db.session.add(loc)
    db.session.commit()
    return jsonify({"id": loc.id, "name": loc.name, "display_order": loc.display_order}), 201


@franchisees_bp.route("/<int:fid>/locations/<int:loc_id>", methods=["PUT", "DELETE"])
def franchisee_location_detail(fid, loc_id):
    """Actualiza o elimina un lugar de trabajo del franquiciado."""
    f = db.get_or_404(Franchisee, fid)
    loc = PayrollLocation.query.filter_by(id=loc_id, franchisee_id=f.id).first()
    if not loc:
        return jsonify({"error": "Lugar de trabajo no encontrado"}), 404
    if request.method == "PUT":
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if name:
            other = PayrollLocation.query.filter(
                PayrollLocation.franchisee_id == f.id,
                PayrollLocation.name == name,
                PayrollLocation.id != loc_id,
            ).first()
            if other:
                return jsonify({"error": "Ya existe un lugar con ese nombre"}), 400
            loc.name = name
        if "display_order" in data:
            loc.display_order = data.get("display_order", 0)
        db.session.commit()
        return jsonify({"id": loc.id, "name": loc.name, "display_order": loc.display_order})
    db.session.delete(loc)
    db.session.commit()
    return "", 204


@franchisees_bp.route("/<int:fid>", methods=["PUT"])
def update_franchisee(fid):
    """Actualiza un franquiciado."""
    f = db.get_or_404(Franchisee, fid)
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
    f = db.get_or_404(Franchisee, fid)
    f.active = False
    db.session.commit()
    return "", 204


@franchisees_bp.route("/current", methods=["GET"])
def get_current():
    """Obtiene el franquiciado actualmente seleccionado."""
    fid = get_current_franchisee_id()
    if not fid:
        return jsonify({"franchisee_id": None, "franchisee": None})
    f = db.session.get(Franchisee, fid)
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
    f = db.session.get(Franchisee, fid)
    if not f or not f.active:
        return jsonify({"error": "Franquiciado no encontrado o inactivo"}), 404
    set_current_franchisee_id(f.id)
    return jsonify({"franchisee_id": f.id, "franchisee": {"id": f.id, "code": f.code or "", "name": f.name}})
