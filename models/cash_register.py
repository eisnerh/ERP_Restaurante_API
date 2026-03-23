"""Modelo de sesión de caja (apertura/cierre) - Arqueo Z."""
from datetime import datetime
from decimal import Decimal
from extensions import db


# Denominaciones Colón (CR) para desglose de efectivo
COLON_DENOMINATIONS = [20000, 10000, 5000, 2000, 1000, 500, 100, 50, 25]


class CashRegisterSession(db.Model):
    """Sesión de caja: apertura y cierre por franquiciado. Soporta Arqueo Z."""
    __tablename__ = "cash_register_sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    opening_balance = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    closing_balance = db.Column(db.Numeric(12, 2), nullable=True)
    expected_balance = db.Column(db.Numeric(12, 2), nullable=True)
    difference = db.Column(db.Numeric(12, 2), nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    # Arqueo Z
    arqueo_number = db.Column(db.Integer, nullable=True)  # Número consecutivo Z
    declared_json = db.Column(db.Text, nullable=True)  # JSON: {efectivo: N, tarjeta: N, ...}
    cash_breakdown_json = db.Column(db.Text, nullable=True)  # JSON: [{pieza: 20000, unidades: 1}, ...]
    cash_in = db.Column(db.Numeric(12, 2), default=0, nullable=True)  # Entradas
    cash_out = db.Column(db.Numeric(12, 2), default=0, nullable=True)  # Salidas (gastos efectivo)
    retirada = db.Column(db.Numeric(12, 2), nullable=True)  # Monto retirado al cerrar
    new_fianza = db.Column(db.Numeric(12, 2), nullable=True)  # Nueva fianza para próxima apertura

    franchisee = db.relationship("Franchisee", backref="cash_register_sessions")
    orders = db.relationship("Order", backref="cash_register", foreign_keys="Order.cash_register_id")
    operational_expenses = db.relationship("OperationalExpense", backref="cash_register")

    def __repr__(self):
        return f"<CashRegisterSession {self.id} franchisee={self.franchisee_id}>"
