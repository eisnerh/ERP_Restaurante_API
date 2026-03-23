"""Modelo de medio de pago configurable por franquiciado."""
from extensions import db


class PaymentMethod(db.Model):
    """Medios de pago por tienda (Efectivo, SINPE, Tarjeta, Pendiente, etc.)."""
    __tablename__ = "payment_methods"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(50), nullable=True)  # efectivo, sinpe, tarjeta_credito, etc.
    display_order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    franchisee = db.relationship("Franchisee", backref="payment_methods")

    def __repr__(self):
        return f"<PaymentMethod {self.name}>"
