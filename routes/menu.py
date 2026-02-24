"""API del menú: categorías y platos."""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Category, Dish
from schemas import CategorySchema, CategorySchemaNested, DishSchema
from utils.franchisee import get_or_default_franchisee_id

menu_bp = Blueprint("menu", __name__, url_prefix="/api/menu")

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
category_nested_schema = CategorySchemaNested()
categories_nested_schema = CategorySchemaNested(many=True)
dish_schema = DishSchema()
dishes_schema = DishSchema(many=True)


# ---------- Categorías ----------
def _franchisee_query(model):
    fid = get_or_default_franchisee_id()
    if not fid:
        return model.query.filter(False)
    return model.query.filter_by(franchisee_id=fid)


@menu_bp.route("/categories", methods=["GET"])
def list_categories():
    """Lista categorías del franquiciado actual."""
    categories = _franchisee_query(Category).all()
    return jsonify(categories_schema.dump(categories))


@menu_bp.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    """Obtiene una categoría con sus platos."""
    fid = get_or_default_franchisee_id()
    category = Category.query.filter_by(id=category_id, franchisee_id=fid).first_or_404()
    return jsonify(category_nested_schema.dump(category))


@menu_bp.route("/categories", methods=["POST"])
def create_category():
    """Crea una categoría."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    data["franchisee_id"] = fid
    category = category_schema.load(data, session=db.session)
    db.session.add(category)
    db.session.commit()
    return jsonify(category_schema.dump(category)), 201


@menu_bp.route("/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    """Actualiza una categoría."""
    fid = get_or_default_franchisee_id()
    category = Category.query.filter_by(id=category_id, franchisee_id=fid).first_or_404()
    data = request.get_json() or {}
    category_schema.load(data, instance=category, session=db.session, partial=True)
    db.session.commit()
    return jsonify(category_schema.dump(category))


@menu_bp.route("/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    """Elimina una categoría (y sus platos)."""
    fid = get_or_default_franchisee_id()
    category = Category.query.filter_by(id=category_id, franchisee_id=fid).first_or_404()
    db.session.delete(category)
    db.session.commit()
    return "", 204


# ---------- Platos ----------
@menu_bp.route("/dishes", methods=["GET"])
def list_dishes():
    """Lista platos del franquiciado. Query: ?category_id=1."""
    fid = get_or_default_franchisee_id()
    category_id = request.args.get("category_id", type=int)
    query = Dish.query.join(Category).filter(Category.franchisee_id == fid)
    if category_id is not None:
        query = query.filter(Dish.category_id == category_id)
    dishes = query.all()
    return jsonify(dishes_schema.dump(dishes))


@menu_bp.route("/dishes/<int:dish_id>", methods=["GET"])
def get_dish(dish_id):
    """Obtiene un plato por ID."""
    fid = get_or_default_franchisee_id()
    dish = Dish.query.join(Category).filter(Dish.id == dish_id, Category.franchisee_id == fid).first_or_404()
    return jsonify(dish_schema.dump(dish))


@menu_bp.route("/dishes", methods=["POST"])
def create_dish():
    """Añade un plato al menú."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    cat_id = data.get("category_id")
    if cat_id:
        cat = Category.query.filter_by(id=cat_id, franchisee_id=fid).first()
        if not cat:
            return jsonify({"error": "Categoría no válida"}), 400
    dish = dish_schema.load(data, session=db.session)
    db.session.add(dish)
    db.session.commit()
    return jsonify(dish_schema.dump(dish)), 201


@menu_bp.route("/dishes/<int:dish_id>", methods=["PUT"])
def update_dish(dish_id):
    """Actualiza un plato."""
    fid = get_or_default_franchisee_id()
    dish = Dish.query.join(Category).filter(Dish.id == dish_id, Category.franchisee_id == fid).first_or_404()
    data = request.get_json() or {}
    dish_schema.load(data, instance=dish, session=db.session, partial=True)
    db.session.commit()
    return jsonify(dish_schema.dump(dish))


@menu_bp.route("/dishes/<int:dish_id>", methods=["DELETE"])
def delete_dish(dish_id):
    """Elimina un plato."""
    fid = get_or_default_franchisee_id()
    dish = Dish.query.join(Category).filter(Dish.id == dish_id, Category.franchisee_id == fid).first_or_404()
    db.session.delete(dish)
    db.session.commit()
    return "", 204


# ---------- Menú completo ----------
@menu_bp.route("/", methods=["GET"])
@menu_bp.route("", methods=["GET"])
def full_menu():
    """Menú completo del franquiciado actual."""
    categories = _franchisee_query(Category).all()
    return jsonify(categories_nested_schema.dump(categories))
