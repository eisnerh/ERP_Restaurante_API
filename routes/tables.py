"""API de mesas."""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Table
from schemas import TableSchema
from utils.franchisee import get_or_default_franchisee_id

tables_bp = Blueprint("tables", __name__, url_prefix="/api/tables")

table_schema = TableSchema()
tables_schema = TableSchema(many=True)


@tables_bp.route("", methods=["GET"])
def list_tables():
    """Lista mesas del franquiciado actual. Query: ?occupied=true|false."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    occupied = request.args.get("occupied")
    query = Table.query.filter_by(franchisee_id=fid)
    if occupied is not None:
        if occupied.lower() in ("true", "1", "yes"):
            query = query.filter_by(occupied=True)
        else:
            query = query.filter_by(occupied=False)
    tables = query.order_by(Table.position_y, Table.position_x, Table.number).all()
    return jsonify(tables_schema.dump(tables))


@tables_bp.route("/<int:table_id>", methods=["GET"])
def get_table(table_id):
    """Obtiene una mesa por ID."""
    fid = get_or_default_franchisee_id()
    table = Table.query.filter_by(id=table_id, franchisee_id=fid).first_or_404()
    return jsonify(table_schema.dump(table))


@tables_bp.route("", methods=["POST"])
def create_table():
    """Crea una mesa."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    data["franchisee_id"] = fid
    table = table_schema.load(data, session=db.session)
    db.session.add(table)
    db.session.commit()
    return jsonify(table_schema.dump(table)), 201


@tables_bp.route("/<int:table_id>", methods=["PUT"])
def update_table(table_id):
    """Actualiza una mesa."""
    fid = get_or_default_franchisee_id()
    table = Table.query.filter_by(id=table_id, franchisee_id=fid).first_or_404()
    data = request.get_json() or {}
    table_schema.load(data, instance=table, session=db.session, partial=True)
    db.session.commit()
    return jsonify(table_schema.dump(table))


@tables_bp.route("/<int:table_id>", methods=["DELETE"])
def delete_table(table_id):
    """Elimina una mesa."""
    fid = get_or_default_franchisee_id()
    table = Table.query.filter_by(id=table_id, franchisee_id=fid).first_or_404()
    db.session.delete(table)
    db.session.commit()
    return "", 204
