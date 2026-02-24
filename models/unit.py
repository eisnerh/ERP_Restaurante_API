"""Modelo de unidad de medida para inventario."""
from extensions import db


class Unit(db.Model):
    __tablename__ = "units"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)  # KG, UND, GR, CJ
    name = db.Column(db.String(80))  # Nombre opcional: Kilogramo, Unidad, etc.

    def __repr__(self):
        return f"<Unit {self.symbol}>"
