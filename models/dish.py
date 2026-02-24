"""Modelo de plato del menú."""
from extensions import db


class Dish(db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    def __repr__(self):
        return f"<Dish {self.name}>"
