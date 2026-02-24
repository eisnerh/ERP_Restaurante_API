"""API de pedidos."""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Order, OrderItem, Dish, Table, Category
from schemas import OrderSchema, OrderSchemaNested
from utils.franchisee import get_or_default_franchisee_id

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
order_nested_schema = OrderSchemaNested()


@orders_bp.route("", methods=["GET"])
def list_orders():
    """Lista pedidos del franquiciado. Query: ?table_id=1 o ?status=pending."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    table_id = request.args.get("table_id", type=int)
    status = request.args.get("status")
    query = Order.query.join(Table).filter(Table.franchisee_id == fid)
    if table_id is not None:
        query = query.filter(Order.table_id == table_id)
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.id.desc()).all()
    return jsonify(orders_schema.dump(orders))


@orders_bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Obtiene un pedido con ítems y total."""
    fid = get_or_default_franchisee_id()
    order = Order.query.join(Table).filter(Order.id == order_id, Table.franchisee_id == fid).first_or_404()
    return jsonify(order_nested_schema.dump(order))


@orders_bp.route("", methods=["POST"])
def create_order():
    """
    Crea un pedido.
    Body: { "table_id": 1, "notes": "...", "items": [ { "dish_id": 1, "quantity": 2 }, ... ] }
    """
    data = request.get_json() or {}
    table_id = data.get("table_id")
    if not table_id:
        return jsonify({"error": "table_id es obligatorio"}), 400
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    table = Table.query.filter_by(id=table_id, franchisee_id=fid).first_or_404()

    order = Order(table_id=table_id, notes=data.get("notes"))
    db.session.add(order)
    db.session.flush()  # para tener order.id

    items_data = data.get("items") or []
    for item_data in items_data:
        dish_id = item_data.get("dish_id")
        quantity = item_data.get("quantity", 1)
        if not dish_id or quantity < 1:
            continue
        dish = Dish.query.join(Category).filter(Dish.id == dish_id, Category.franchisee_id == fid).first()
        if not dish or not dish.available:
            continue
        order_item = OrderItem(
            order_id=order.id,
            dish_id=dish_id,
            quantity=quantity,
            unit_price=dish.price,
        )
        db.session.add(order_item)

    table.occupied = True
    db.session.commit()
    return jsonify(order_nested_schema.dump(order)), 201


@orders_bp.route("/<int:order_id>/status", methods=["PATCH"])
def update_order_status(order_id):
    """Actualiza el estado: pending, preparing, served, paid."""
    fid = get_or_default_franchisee_id()
    order = Order.query.join(Table).filter(Order.id == order_id, Table.franchisee_id == fid).first_or_404()
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ("pending", "preparing", "served", "paid"):
        return jsonify({"error": "status debe ser pending, preparing, served o paid"}), 400
    order.status = status
    if status == "paid":
        order.table.occupied = False
    db.session.commit()
    return jsonify(order_schema.dump(order))


@orders_bp.route("/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    """Elimina un pedido (y libera la mesa)."""
    fid = get_or_default_franchisee_id()
    order = Order.query.join(Table).filter(Order.id == order_id, Table.franchisee_id == fid).first_or_404()
    order.table.occupied = False
    db.session.delete(order)
    db.session.commit()
    return "", 204
