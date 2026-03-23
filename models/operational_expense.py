"""Modelo de gastos operacionales diarios (saliendo de caja)."""
from datetime import datetime
from extensions import db


class OperationalExpense(db.Model):
    """Gastos del día: compras menores, servicios, etc. Se asocian a sesión de caja."""
    __tablename__ = "operational_expenses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    cash_register_id = db.Column(db.Integer, db.ForeignKey("cash_register_sessions.id"), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)  # Vincula con compra
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    payment_type = db.Column(db.String(50), nullable=True)  # efectivo, sinpe, tarjeta_credito, tarjeta_debito
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    franchisee = db.relationship("Franchisee", backref="operational_expenses")
    purchase_order = db.relationship("PurchaseOrder", backref="operational_expenses")

    def __repr__(self):
        return f"<OperationalExpense {self.id} {self.amount}>"
