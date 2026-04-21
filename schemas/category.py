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
    icon = ma.auto_field(required=False, allow_none=True)
    icon_emoji = fields.Method("get_icon_emoji", dump_only=True)

    def get_icon_emoji(self, obj):
        from utils.category_icon import emoji_for_icon_suffix, suggest_icon_for_category_name

        suf = getattr(obj, "icon", None) or suggest_icon_for_category_name(getattr(obj, "name", None))
        return emoji_for_icon_suffix(suf)


class CategorySchemaNested(CategorySchema):
    dishes = fields.Nested("DishSchema", many=True)
