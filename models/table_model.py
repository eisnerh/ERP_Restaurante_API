"""Modelo de mesa del restaurante."""
from extensions import db


class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    position_x = db.Column(db.Integer, default=0)
    position_y = db.Column(db.Integer, default=0)
    occupied = db.Column(db.Boolean, default=False)

    franchisee = db.relationship("Franchisee", backref="tables")
    orders = db.relationship("Order", backref="table", lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "number", name="uq_table_franchisee_number"),)

    def __repr__(self):
        return f"<Table {self.number}>"
