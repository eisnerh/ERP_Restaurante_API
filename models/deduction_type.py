"""Tipo de deducción: CCSS, día libre intercambiado, etc. Permite valores negativos (ej. horas negociables)."""
from extensions import db


class DeductionType(db.Model):
    """
    Tipo de deducción para planilla.
    - can_be_negative: si True, amount/quantity pueden ser negativos (ej. día libre intercambiado = horas negociables).
    - is_hours_based: si True, quantity son horas (pueden ser negativas para indicar horas a negociar).
    """
    __tablename__ = "deduction_types"

    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)  # ej. CCSS, Día libre intercambiado
    description = db.Column(db.String(200))  # ej. Horas negativas = horas negociables para día libre
    can_be_negative = db.Column(db.Boolean, default=False)  # Permite negativos (horas/monto negociable)
    is_hours_based = db.Column(db.Boolean, default=False)  # quantity = horas (ej. -2 = 2 hrs a negociar)
    display_order = db.Column(db.Integer, default=0)

    franchisee = db.relationship("Franchisee", backref="deduction_types")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "name", name="uq_deduction_type_franchisee_name"),)

    def __repr__(self):
        return f"<DeductionType {self.name}>"
