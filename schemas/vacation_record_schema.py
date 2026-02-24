"""Esquema para registros de vacaciones."""
from extensions import ma
from models import VacationRecord


class VacationRecordSchema(ma.SQLAlchemySchema):
    class Meta:
        model = VacationRecord
        load_instance = True

    id = ma.auto_field()
    employee_id = ma.auto_field()
    fecha_desde = ma.auto_field()
    fecha_hasta = ma.auto_field()
    dias_tomados = ma.auto_field()
    tipo = ma.auto_field()
    notes = ma.auto_field()
