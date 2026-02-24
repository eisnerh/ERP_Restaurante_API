"""Esquemas de categoría."""
from extensions import ma
from marshmallow import fields
from models import Category


class CategorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Category
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    name = ma.auto_field()
    description = ma.auto_field()


class CategorySchemaNested(CategorySchema):
    dishes = fields.Nested("DishSchema", many=True)
