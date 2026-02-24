"""Desglose de pago por empleado: salario por mes/quincena/semana/día/hora y totales."""
from datetime import date
from extensions import db


class Payslip(db.Model):
    __tablename__ = "payslips"

    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    location_name = db.Column(db.String(120), nullable=False)
    employee_name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(80))  # LIDER DE COCINA, COLABORADOR FIJO, etc.
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    # Desglose del salario
    salary_mes = db.Column(db.Float)
    salary_quincena = db.Column(db.Float)
    salary_semana = db.Column(db.Float)
    salary_dia = db.Column(db.Float)
    salary_hora_ordinaria = db.Column(db.Float)
    salary_hora_extra = db.Column(db.Float)

    total_asignaciones = db.Column(db.Float)
    total_deducciones = db.Column(db.Float)
    total_depositado = db.Column(db.Float)

    numero_cuenta = db.Column(db.String(120))
    notes = db.Column(db.String(300))

    franchisee = db.relationship("Franchisee", backref="payslips")
    lines = db.relationship("PayslipLine", backref="payslip", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Payslip {self.employee_name} {self.period_start}>"


class PayslipLine(db.Model):
    """Línea de asignación o deducción (SALARIO QUINCENAL, HORAS EXTRA, CCSS, etc.)."""
    __tablename__ = "payslip_lines"

    id = db.Column(db.Integer, primary_key=True)
    payslip_id = db.Column(db.Integer, db.ForeignKey("payslips.id"), nullable=False)
    line_type = db.Column(db.String(20), nullable=False)  # asignacion | deduccion
    concept = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float)   # ej. horas extra: 3
    rate_or_pct = db.Column(db.Float)  # ej. CCSS 10.83% -> 0.1083

    def __repr__(self):
        return f"<PayslipLine {self.concept} {self.amount}>"
