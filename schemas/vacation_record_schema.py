"""Esquema para registros de vacaciones."""
from extensions import ma
from models import VacationRecord
from .employee_schema import FlexibleDate


class VacationRecordSchema(ma.SQLAlchemySchema):
    class Meta:
        model = VacationRecord
        load_instance = True

    id = ma.auto_field()
    employee_id = ma.auto_field()
    fecha_desde = FlexibleDate()
    fecha_hasta = FlexibleDate()
    dias_tomados = ma.auto_field()
    tipo = ma.auto_field()
    notes = ma.auto_field()
