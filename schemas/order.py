"""Esquemas de pedido."""
from extensions import ma
from marshmallow import fields
from models import Order, OrderItem, Dish


class DishSchemaShort(ma.SQLAlchemySchema):
    class Meta:
        model = Dish
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    price = ma.auto_field()


class OrderItemSchema(ma.SQLAlchemySchema):
    class Meta:
        model = OrderItem
        load_instance = True

    id = ma.auto_field()
    dish_id = ma.auto_field()
    quantity = ma.auto_field()
    unit_price = ma.auto_field()
    dish = fields.Nested(DishSchemaShort, only=("id", "name", "price"))


class OrderSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Order
        load_instance = True

    id = ma.auto_field()
    table_id = ma.auto_field()
    status = ma.auto_field()
    created_at = ma.auto_field()
    notes = ma.auto_field()
    items = fields.Nested(OrderItemSchema, many=True)


class OrderSchemaNested(OrderSchema):
    total = fields.Method("get_total")

    @staticmethod
    def get_total(obj):
        return obj.total()
