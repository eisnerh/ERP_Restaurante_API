"""Registro de pago efectuado a un empleado."""
from extensions import db


# Períodos de pago soportados
PERIODO_PAGO_CHOICES = ("mensual", "quincenal", "semanal", "diario", "por_hora")


class PaymentRecord(db.Model):
    """Registro de un pago realizado a un empleado."""
    __tablename__ = "payment_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    payslip_id = db.Column(db.Integer, db.ForeignKey("payslips.id"), nullable=True)  # Opcional: vincula al desglose
    location_id = db.Column(db.Integer, db.ForeignKey("payroll_locations.id"), nullable=True)

    amount = db.Column(db.Float, nullable=False)  # Monto pagado
    hours_worked = db.Column(db.Float, nullable=True)  # Horas ordinarias trabajadas
    hours_extra = db.Column(db.Float, nullable=True)  # Horas extras (CR: recargo 50% = 1.5x)
    hours_extra_festivo = db.Column(db.Boolean, default=False)  # Si horas extras son en día festivo (CR: 2x)
    hourly_rate = db.Column(db.Float, nullable=True)  # Tarifa por hora (₡)
    days_worked = db.Column(db.Float, nullable=True)  # Días trabajados (para pago diario)
    include_sundays = db.Column(db.Boolean, default=False)  # Si incluir domingos en cálculo diario
    payment_date = db.Column(db.Date, nullable=False)  # Fecha en que se pagó
    period_start = db.Column(db.Date, nullable=True)  # Inicio del período que cubre
    period_end = db.Column(db.Date, nullable=True)  # Fin del período que cubre
    periodo_tipo = db.Column(db.String(20), default="mensual")  # mensual|quincenal|semanal|diario|por_hora

    notes = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    franchisee = db.relationship("Franchisee", backref="payment_records")
    employee = db.relationship("Employee", backref="payment_records")
    payslip = db.relationship("Payslip", backref="payment_records")
    location = db.relationship("PayrollLocation", backref="payment_records")

    def __repr__(self):
        return f"<PaymentRecord {self.employee_id} {self.amount} {self.payment_date}>"
