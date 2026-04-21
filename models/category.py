"""Modelo de categoría del menú (entrantes, platos principales, postres, bebidas)."""
from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    # Sufijo de Bootstrap Icons, ej. cup-hot -> bi bi-cup-hot (nullable = sugerir por nombre)
    icon = db.Column(db.String(64), nullable=True)

    franchisee = db.relationship("Franchisee", backref="categories")
    dishes = db.relationship("Dish", backref="category", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "name", name="uq_category_franchisee_name"),)

    def __repr__(self):
        return f"<Category {self.name}>"
