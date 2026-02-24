"""Empleado perteneciente a una franquicia. Campos y cálculos según Código de Trabajo Costa Rica."""
from datetime import date, timedelta
from extensions import db


def _weeks_worked(start_date, as_of_date):
    """Semanas laboradas entre start_date y as_of_date."""
    if not start_date or not as_of_date or as_of_date < start_date:
        return 0
    delta = (as_of_date - start_date).days
    return max(0, delta // 7)


def _months_worked_since(start_date, as_of_date):
    """Meses completos entre start_date y as_of_date (inclusive del mes si ya pasó el mismo día)."""
    if not start_date or not as_of_date or as_of_date < start_date:
        return 0
    months = (as_of_date.year - start_date.year) * 12 + (as_of_date.month - start_date.month)
    if as_of_date.day < start_date.day:
        months -= 1
    return max(0, months)


# CR: 14 días de vacaciones por cada 50 semanas (Código de Trabajo art. 177)
VACACIONES_DIAS_POR_50_SEMANAS = 14


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("payroll_locations.id"), nullable=True)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(40))  # Código interno
    cedula = db.Column(db.String(20))  # Cédula o identificación
    numero_cuenta = db.Column(db.String(120))  # Cuenta bancaria para depósitos
    fecha_ingreso = db.Column(db.Date)  # Fecha de contratación
    fecha_salida = db.Column(db.Date)  # Fecha de terminación (null si activo)
    salario_base = db.Column(db.Float)  # Salario mensual base (para aguinaldo, prestaciones)
    salario_hora = db.Column(db.Float)  # Tarifa por hora (₡) - para empleados pagados por hora
    horas_por_dia = db.Column(db.Float, default=8)  # Horas que debe trabajar por día (para cálculo)
    periodo_pago = db.Column(db.String(20), default="mensual")  # mensual|quincenal|semanal|diario|por_hora
    tipo_contrato = db.Column(db.String(30), default="indefinido")  # indefinido | temporal | prueba
    jornada = db.Column(db.String(20), default="completa")  # completa | media | parcial
    vacaciones_dias_tomados = db.Column(db.Float, default=0)  # Días de vacaciones ya utilizados
    active = db.Column(db.Boolean, default=True)

    franchisee = db.relationship("Franchisee", backref="employees")
    location = db.relationship("PayrollLocation", backref="employees")
    position = db.relationship("Position", backref="employees")

    def _fecha_fin(self, as_of_date=None):
        """Fecha efectiva de fin: fecha_salida si existe, sino as_of_date."""
        if self.fecha_salida:
            return min(self.fecha_salida, as_of_date or date.today())
        return as_of_date or date.today()

    def vacation_days_earned(self, as_of_date=None):
        """Días de vacaciones ganados según CR: 14 días por cada 50 semanas laboradas."""
        if not self.fecha_ingreso:
            return 0
        end = self._fecha_fin(as_of_date)
        weeks = _weeks_worked(self.fecha_ingreso, end)
        return (weeks / 50) * VACACIONES_DIAS_POR_50_SEMANAS

    def _vacation_days_taken(self, as_of_date=None):
        """Días tomados = suma de registros de vacaciones disfrutadas (vacation_records)."""
        from sqlalchemy import func
        from models import VacationRecord
        q = VacationRecord.query.filter_by(employee_id=self.id)
        if as_of_date:
            q = q.filter(VacationRecord.fecha_desde <= as_of_date)
        total = q.with_entities(func.coalesce(func.sum(VacationRecord.dias_tomados), 0)).scalar()
        return float(total or 0)

    def vacation_days(self, as_of_date=None):
        """Días de vacaciones disponibles = ganados - tomados (solo se deducen con registros)."""
        earned = self.vacation_days_earned(as_of_date)
        taken = self._vacation_days_taken(as_of_date)
        return max(0, round(earned - taken, 1))

    def vacation_days_simple(self, as_of_date=None):
        """Alternativa: 1 día por mes completo (política interna)."""
        if not self.fecha_ingreso:
            return 0
        end = self._fecha_fin(as_of_date)
        return _months_worked_since(self.fecha_ingreso, end)

    def aguinaldo_proporcional(self, as_of_date=None):
        """Aguinaldo proporcional: 8.33% (1/12) del salario por mes laborado en el año."""
        if not self.salario_base or not self.fecha_ingreso:
            return 0
        end = self._fecha_fin(as_of_date)
        year = end.year
        start_year = max(self.fecha_ingreso, date(year, 1, 1))
        months = _months_worked_since(start_year, end)
        if months <= 0:
            return 0
        return round(self.salario_base * (months / 12), 2)

    def antiguedad_meses(self, as_of_date=None):
        """Antigüedad en meses completos."""
        if not self.fecha_ingreso:
            return 0
        return _months_worked_since(self.fecha_ingreso, self._fecha_fin(as_of_date))

    def __repr__(self):
        return f"<Employee {self.name}>"
