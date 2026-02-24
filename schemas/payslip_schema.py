"""Esquemas para desglose de planilla (payslip)."""
from extensions import ma
from models import Payslip, PayslipLine


class PayslipLineSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PayslipLine
        load_instance = True

    id = ma.auto_field()
    line_type = ma.auto_field()
    concept = ma.auto_field()
    amount = ma.auto_field()
    quantity = ma.auto_field()
    rate_or_pct = ma.auto_field()


class PayslipSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Payslip
        load_instance = True

    id = ma.auto_field()
    location_name = ma.auto_field()
    employee_name = ma.auto_field()
    position = ma.auto_field()
    period_start = ma.auto_field()
    period_end = ma.auto_field()
    salary_mes = ma.auto_field()
    salary_quincena = ma.auto_field()
    salary_semana = ma.auto_field()
    salary_dia = ma.auto_field()
    salary_hora_ordinaria = ma.auto_field()
    salary_hora_extra = ma.auto_field()
    total_asignaciones = ma.auto_field()
    total_deducciones = ma.auto_field()
    total_depositado = ma.auto_field()
    numero_cuenta = ma.auto_field()
    notes = ma.auto_field()
    lines = ma.Nested(PayslipLineSchema, many=True)
