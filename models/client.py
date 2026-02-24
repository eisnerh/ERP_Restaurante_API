"""Modelo de cliente (ERP)."""
from extensions import db


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    tax_id = db.Column(db.String(50))  # Cédula, RUC, NIF
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    address = db.Column(db.String(300))
    notes = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)

    franchisee = db.relationship("Franchisee", backref="clients")

    def __repr__(self):
        return f"<Client {self.name}>"
