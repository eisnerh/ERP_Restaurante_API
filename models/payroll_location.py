"""Sucursal o ubicación para planilla (trabajos y cargos)."""
from extensions import db


class PayrollLocation(db.Model):
    __tablename__ = "payroll_locations"

    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    display_order = db.Column(db.Integer, default=0)

    franchisee = db.relationship("Franchisee", backref="payroll_locations")
    entries = db.relationship("PayrollEntry", backref="location", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "name", name="uq_payroll_loc_franchisee_name"),)

    def __repr__(self):
        return f"<PayrollLocation {self.name}>"
