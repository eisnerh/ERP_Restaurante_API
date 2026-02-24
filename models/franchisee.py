"""Modelo de franquiciado (sucursal de la franquicia)."""
from extensions import db


class Franchisee(db.Model):
    __tablename__ = "franchisees"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)  # Código: PLAZA-SC, CENTRO, etc.
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(300))
    phone = db.Column(db.String(40))
    email = db.Column(db.String(120))
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Franchisee {self.name}>"
