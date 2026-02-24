"""Esquemas de plato."""
from extensions import ma
from models import Dish


class DishSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Dish
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    description = ma.auto_field()
    price = ma.auto_field()
    available = ma.auto_field()
    category_id = ma.auto_field()
