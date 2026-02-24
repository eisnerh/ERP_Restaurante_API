"""Esquemas para planilla (trabajos y cargos)."""
from extensions import ma
from models import PayrollLocation, PayrollEntry
from .employee_schema import FlexibleDate


class PayrollLocationSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PayrollLocation
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    name = ma.auto_field()
    display_order = ma.auto_field()


class PayrollEntrySchema(ma.SQLAlchemySchema):
    class Meta:
        model = PayrollEntry
        load_instance = True

    id = ma.auto_field()
    location_id = ma.auto_field()
    employee_id = ma.auto_field()
    position_id = ma.auto_field()
    period_date = FlexibleDate()
    employee_name = ma.auto_field()
    entry_type = ma.auto_field()
    code = ma.auto_field()
    hrs_extra = ma.auto_field()
    creditos_comida = ma.auto_field()
    vale_efectivo = ma.auto_field()
    ccss_rebajos = ma.auto_field()
    dia_psg = ma.auto_field()
    incapacidades = ma.auto_field()
    numero_cuenta = ma.auto_field()
    fecha_ingreso = ma.auto_field()
    notes = ma.auto_field()
