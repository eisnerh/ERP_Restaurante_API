"""Registro de planilla: empleado o cargo adicional (ej. MERMAS) por ubicación y fecha."""
from datetime import date
from extensions import db


class PayrollEntry(db.Model):
    __tablename__ = "payroll_entries"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("payroll_locations.id"), nullable=False)
    period_date = db.Column(db.Date, nullable=True)  # Fecha de la planilla / periodo (rebajos y pagos)
    employee_name = db.Column(db.String(120), nullable=False)
    entry_type = db.Column(db.String(20), default="employee")  # employee | mermas | other
    code = db.Column(db.String(40))
    hrs_extra = db.Column(db.Float)           # HRS EXTRAS: positivas o negativas
    creditos_comida = db.Column(db.Float, default=0)  # Créditos comida (suelen ser negativos)
    vale_efectivo = db.Column(db.Float)
    ccss_rebajos = db.Column(db.Float)        # CCSS / rebajos
    dia_psg = db.Column(db.String(80))      # Día PSG
    incapacidades = db.Column(db.String(80))
    numero_cuenta = db.Column(db.String(120))
    fecha_ingreso = db.Column(db.Date)        # Fecha de ingreso del empleado
    notes = db.Column(db.String(300))

    def __repr__(self):
        return f"<PayrollEntry {self.employee_name} @ {self.location_id}>"
