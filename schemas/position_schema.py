"""Esquema para puestos/cargos."""
from extensions import ma
from models import Position


class PositionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Position
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    name = ma.auto_field()
    position_type = ma.auto_field()
    display_order = ma.auto_field()
