"""Esquemas de mesa."""
from extensions import ma
from models import Table


class TableSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Table
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    number = ma.auto_field()
    capacity = ma.auto_field()
    position_x = ma.auto_field()
    position_y = ma.auto_field()
    occupied = ma.auto_field()
