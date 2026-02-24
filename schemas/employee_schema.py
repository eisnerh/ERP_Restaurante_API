"""Esquema para empleados."""
from marshmallow import fields
from extensions import ma
from models import Employee


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
    fecha_ingreso = ma.auto_field()
    fecha_salida = ma.auto_field()
    salario_base = ma.auto_field()
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
