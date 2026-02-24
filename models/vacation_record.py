"""Registro de vacaciones tomadas por empleado (Código de Trabajo CR)."""
from datetime import date
from extensions import db


class VacationRecord(db.Model):
    """Registro de período de vacaciones tomadas."""
    __tablename__ = "vacation_records"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    fecha_desde = db.Column(db.Date, nullable=False)
    fecha_hasta = db.Column(db.Date, nullable=False)
    dias_tomados = db.Column(db.Float, nullable=False)  # Días efectivos de vacaciones
    tipo = db.Column(db.String(30), default="vacaciones")  # vacaciones | permiso | incapacidad
    notes = db.Column(db.String(200))

    employee = db.relationship("Employee", backref="vacation_records")

    def __repr__(self):
        return f"<VacationRecord {self.employee_id} {self.fecha_desde}>"
