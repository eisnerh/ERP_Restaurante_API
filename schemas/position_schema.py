"""Esquema para puestos/cargos."""
from extensions import ma
from models import Position


class PositionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Position
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    position_type = ma.auto_field()
    display_order = ma.auto_field()
    salario_base = ma.auto_field()
    horas_por_dia = ma.auto_field()
    dias_por_semana = ma.auto_field()
    ccss_pct = ma.auto_field()
    aplicar_ccss = ma.auto_field()
