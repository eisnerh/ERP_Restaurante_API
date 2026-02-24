"""Esquema para tipos de deducción."""
from extensions import ma
from models import DeductionType


class DeductionTypeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = DeductionType
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    description = ma.auto_field()
    can_be_negative = ma.auto_field()
    is_hours_based = ma.auto_field()
    rate_pct = ma.auto_field()
    display_order = ma.auto_field()
