"""Tipo de registro de planilla: empleado, mermas, por contrato, servicios profesionales, etc."""
from extensions import db


class PayrollEntryType(db.Model):
    """Tipos de registro configurables. Define cómo se clasifica cada entrada de planilla."""
    __tablename__ = "payroll_entry_types"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(40), nullable=False, unique=True)  # empleado, mermas, por_contrato, servicios_profesionales
    name = db.Column(db.String(80), nullable=False)  # Nombre para mostrar
    description = db.Column(db.String(200))  # Descripción opcional
    display_order = db.Column(db.Integer, default=0)  # Orden en el selector
    hide_puesto = db.Column(db.Boolean, default=False)  # Si True, no mostrar campo Puesto (ej. mermas)

    def __repr__(self):
        return f"<PayrollEntryType {self.code}>"
