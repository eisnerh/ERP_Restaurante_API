"""Modelo de motivo de descuento configurable por franquiciado."""
from extensions import db


class DiscountReason(db.Model):
    """Motivos de descuento (Desc. Empleados 20%, Descuento comercial, etc.)."""
    __tablename__ = "discount_reasons"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    percentage = db.Column(db.Float, nullable=True)  # Opcional: 20 = 20%
    description = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean, default=True)

    franchisee = db.relationship("Franchisee", backref="discount_reasons")

    def __repr__(self):
        return f"<DiscountReason {self.name}>"
