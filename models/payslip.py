"""Desglose de pago por empleado: salario por mes/quincena/semana/día/hora y totales."""
from datetime import date
from extensions import db


class Payslip(db.Model):
    __tablename__ = "payslips"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)  # Empleado vinculado
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), nullable=True)  # Puesto vinculado
    location_name = db.Column(db.String(120), nullable=False)
    employee_name = db.Column(db.String(120), nullable=False)  # Se mantiene para import/display
    position = db.Column(db.String(80))  # LIDER DE COCINA, etc. (se mantiene para import/display)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    tipo_pago = db.Column(db.String(20), default="mensual")  # mensual|quincenal|semanal|diario|por_hora

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
    employee = db.relationship("Employee", backref="payslips")
    position_rel = db.relationship("Position", backref="payslips")
    lines = db.relationship("PayslipLine", backref="payslip", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Payslip {self.employee_name} {self.period_start}>"


class PayslipLine(db.Model):
    """Línea de asignación o deducción. amount/quantity pueden ser negativos (ej. horas negociables día libre)."""
    __tablename__ = "payslip_lines"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payslip_id = db.Column(db.Integer, db.ForeignKey("payslips.id"), nullable=False)
    deduction_type_id = db.Column(db.Integer, db.ForeignKey("deduction_types.id"), nullable=True)  # Tipo de deducción
    line_type = db.Column(db.String(20), nullable=False)  # asignacion | deduccion
    concept = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, default=0)  # Puede ser negativo (negociable)
    quantity = db.Column(db.Float)   # ej. horas: 3 o -2 (negativo = horas a negociar)
    rate_or_pct = db.Column(db.Float)  # ej. CCSS 10.83% -> 0.1083

    deduction_type = db.relationship("DeductionType", backref="payslip_lines")

    def __repr__(self):
        return f"<PayslipLine {self.concept} {self.amount}>"
