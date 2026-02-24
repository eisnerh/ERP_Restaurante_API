"""Esquema de unidad de medida."""
from extensions import ma
from models import Unit


class UnitSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Unit
        load_instance = True

    id = ma.auto_field()
    symbol = ma.auto_field()
    name = ma.auto_field()
