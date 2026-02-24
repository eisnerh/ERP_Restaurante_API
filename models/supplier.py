"""Modelo de proveedor (inventario). Mismo catálogo; datos de contacto editables por franquiciado/ubicación."""
from extensions import db


class Supplier(db.Model):
    """Proveedor. Mismo nombre para todos; cada franquiciado edita su teléfono, contacto, día de visita."""
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    contact = db.Column(db.String(120))
    visit_day = db.Column(db.String(60))
    visit_schedule = db.Column(db.String(40))  # bisemanal, semanal, diario

    franchisee = db.relationship("Franchisee", backref="suppliers")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "name", name="uq_supplier_franchisee_name"),)

    def __repr__(self):
        return f"<Supplier {self.name}>"
