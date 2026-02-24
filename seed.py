"""Carga datos de ejemplo en la base de datos."""
import os
import sys

# Asegurar que el directorio del proyecto está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models import Category, Dish, Table


def seed():
    with app.app_context():
        if Category.query.first():
            print("Ya hay datos. No se ejecuta seed.")
            return

        # Categorías
        entrantes = Category(name="Entrantes", description="Para empezar")
        principales = Category(name="Platos principales", description="Segundos")
        postres = Category(name="Postres", description="Dulces y café")
        bebidas = Category(name="Bebidas", description="Refrescos y más")
        db.session.add_all([entrantes, principales, postres, bebidas])
        db.session.flush()

        # Platos
        dishes = [
            Dish(name="Ensalada César", description="Lechuga, pollo, parmesano", price=8.50, category_id=entrantes.id),
            Dish(name="Croquetas de jamón", description="8 unidades", price=6.00, category_id=entrantes.id),
            Dish(name="Entrecot a la parrilla", description="300g con patatas", price=18.00, category_id=principales.id),
            Dish(name="Pasta carbonara", description="Bacon y nata", price=12.00, category_id=principales.id),
            Dish(name="Tarta de queso", description="Con coulis de frutos rojos", price=5.50, category_id=postres.id),
            Dish(name="Café con leche", description="", price=2.20, category_id=bebidas.id),
            Dish(name="Agua mineral", description="500ml", price=2.00, category_id=bebidas.id),
        ]
        db.session.add_all(dishes)

        # Mesas
        for n in range(1, 11):
            db.session.add(Table(number=n, capacity=4 if n <= 6 else 6))

        db.session.commit()
        print("Datos de ejemplo cargados correctamente.")


if __name__ == "__main__":
    seed()
