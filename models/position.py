"""Puesto o cargo: empleado, administrador, administrativo, inventario o personalizado."""
from extensions import db


# Tipos base de puesto (no se eliminan)
POSITION_TYPES = ("empleado", "administrador", "administrativo", "inventario", "custom")


class Position(db.Model):
    """Puesto/cargo. Se pueden crear sobre la marcha. Tipo: empleado, administrador, administrativo, inventario, custom."""
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)  # ej. Líder de Cocina, Cajero, Gerente
    position_type = db.Column(db.String(30), nullable=False, default="empleado")  # empleado|administrador|administrativo|inventario|custom
    display_order = db.Column(db.Integer, default=0)

    franchisee = db.relationship("Franchisee", backref="positions")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "name", name="uq_position_franchisee_name"),)

    def __repr__(self):
        return f"<Position {self.name} ({self.position_type})>"
