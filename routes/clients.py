"""API de clientes (ERP)."""
from sqlalchemy import or_
from flask import Blueprint, request, jsonify
from extensions import db
from models import Client
from schemas import ClientSchema
from utils.franchisee import get_or_default_franchisee_id
from utils.client_payload import normalize_client_payload, parse_active

clients_bp = Blueprint("clients", __name__, url_prefix="/api/clients")

client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)


@clients_bp.route("", methods=["GET"])
def list_clients():
    """Lista clientes del franquiciado. Query: ?q=buscar, ?active=1|0."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    q = (request.args.get("q") or "").strip()
    active = request.args.get("active")
    query = Client.query.filter_by(franchisee_id=fid).order_by(Client.name)
    if q:
        query = query.filter(
            or_(
                Client.name.ilike(f"%{q}%"),
                Client.tax_id.ilike(f"%{q}%"),
                Client.email.ilike(f"%{q}%"),
            )
        )
    if active is not None:
        try:
            query = query.filter(Client.active == parse_active(active))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
    clients = query.all()
    return jsonify(clients_schema.dump(clients))


@clients_bp.route("", methods=["POST"])
def create_client():
    """Crea un cliente del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    try:
        values = normalize_client_payload(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    client = Client(franchisee_id=fid, **values)
    db.session.add(client)
    db.session.commit()
    return jsonify(client_schema.dump(client)), 201


@clients_bp.route("/<int:client_id>", methods=["GET"])
def get_client(client_id):
    """Obtiene un cliente por ID."""
    fid = get_or_default_franchisee_id()
    client = Client.query.filter_by(id=client_id, franchisee_id=fid).first() if fid else None
    if not client:
        return jsonify({"error": "Cliente no encontrado"}), 404
    return jsonify(client_schema.dump(client))


@clients_bp.route("/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    """Actualiza un cliente."""
    fid = get_or_default_franchisee_id()
    client = Client.query.filter_by(id=client_id, franchisee_id=fid).first() if fid else None
    if not client:
        return jsonify({"error": "Cliente no encontrado"}), 404
    try:
        values = normalize_client_payload(request.get_json(silent=True), partial=True)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    for field, value in values.items():
        setattr(client, field, value)
    db.session.commit()
    return jsonify(client_schema.dump(client))


@clients_bp.route("/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    """Elimina un cliente (soft delete: marca como inactivo)."""
    fid = get_or_default_franchisee_id()
    client = Client.query.filter_by(id=client_id, franchisee_id=fid).first() if fid else None
    if not client:
        return jsonify({"error": "Cliente no encontrado"}), 404
    client.active = False
    db.session.commit()
    return jsonify(client_schema.dump(client))
