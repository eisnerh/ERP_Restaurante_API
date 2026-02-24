"""Esquema para registros de pago."""
from extensions import ma
from models import PaymentRecord
from .employee_schema import FlexibleDate


class PaymentRecordSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PaymentRecord
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    employee_id = ma.auto_field()
    payslip_id = ma.auto_field()
    location_id = ma.auto_field()
    amount = ma.auto_field()
    hours_worked = ma.auto_field()
    hours_extra = ma.auto_field()
    hours_extra_festivo = ma.auto_field()
    hourly_rate = ma.auto_field()
    days_worked = ma.auto_field()
    include_sundays = ma.auto_field()
    payment_date = FlexibleDate()
    period_start = FlexibleDate()
    period_end = FlexibleDate()
    periodo_tipo = ma.auto_field()
    notes = ma.auto_field()
    created_at = ma.auto_field()
