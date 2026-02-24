"""Esquema para empleados."""
from datetime import datetime
from marshmallow import fields
from extensions import ma
from models import Employee


def _to_date(val):
    """Convierte cualquier valor a date o None. Acepta None, '', string YYYY-MM-DD, o date."""
    if val is None or val == "":
        return None
    if hasattr(val, "year") and hasattr(val, "month"):
        return val
    s = str(val).strip()[:10]
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


class FlexibleDate(fields.Field):
    """Campo de fecha que acepta None, '', string o date sin fallar."""

    def _deserialize(self, value, attr, data, **kwargs):
        return _to_date(value)

    def _serialize(self, value, attr, obj, **kwargs):
        return value.isoformat() if value else None


class EmployeeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Employee
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    location_id = ma.auto_field()
    position_id = ma.auto_field()
    name = ma.auto_field()
    code = ma.auto_field()
    cedula = ma.auto_field()
    numero_cuenta = ma.auto_field()
    fecha_ingreso = FlexibleDate()
    fecha_salida = FlexibleDate()
    salario_base = ma.auto_field()
    salario_hora = ma.auto_field()
    horas_por_dia = ma.auto_field()
    periodo_pago = ma.auto_field()

    tipo_contrato = ma.auto_field()
    jornada = ma.auto_field()
    vacaciones_dias_tomados = ma.auto_field()
    active = ma.auto_field()
    vacation_days = fields.Method("get_vacation_days", dump_only=True)
    vacation_days_earned = fields.Method("get_vacation_days_earned", dump_only=True)
    aguinaldo_proporcional = fields.Method("get_aguinaldo", dump_only=True)
    antiguedad_meses = fields.Method("get_antiguedad", dump_only=True)

    def get_vacation_days(self, obj):
        return round(obj.vacation_days(), 1) if obj else 0

    def get_vacation_days_earned(self, obj):
        return round(obj.vacation_days_earned(), 1) if obj else 0

    def get_aguinaldo(self, obj):
        return obj.aguinaldo_proporcional() if obj else 0

    def get_antiguedad(self, obj):
        return obj.antiguedad_meses() if obj else 0
