"""Tipo de deducción: CCSS, día libre intercambiado, etc. Estándar global."""
from extensions import db


class DeductionType(db.Model):
    """
    Tipo de deducción estándar para planilla. Lista global compartida.
    - can_be_negative: si True, amount/quantity pueden ser negativos (ej. día libre intercambiado = horas negociables).
    - is_hours_based: si True, quantity son horas (pueden ser negativas para indicar horas a negociar).
    """
    __tablename__ = "deduction_types"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)  # ej. CCSS, Día libre intercambiado
    description = db.Column(db.String(200))  # ej. Horas negativas = horas negociables para día libre
    can_be_negative = db.Column(db.Boolean, default=False)  # Permite negativos (horas/monto negociable)
    is_hours_based = db.Column(db.Boolean, default=False)  # quantity = horas (ej. -2 = 2 hrs a negociar)
    rate_pct = db.Column(db.Float)  # % para cálculo automático (ej. 0.1083 = CCSS 10.83%)
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<DeductionType {self.name}>"
