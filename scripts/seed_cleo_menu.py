"""
Carga el menú Cleo Café (categorías y platos) para un franquiciado.
Precios en colones costarricenses (₡).

Uso:
  python scripts/seed_cleo_menu.py
  python scripts/seed_cleo_menu.py --franchisee-id 1
  python scripts/seed_cleo_menu.py --force   # reemplaza menú Cleo anterior
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from utils.category_icon import suggest_icon_for_category_name

PREFIX = "Cleo Café"
# Texto en descripción para detectar/reemplazar menú cargado por este script
CLEO_MENU_DESCRIPTION = f"Menú {PREFIX}"


def _cat(name_suffix: str) -> str:
    """Nombre de categoría (máx. 80 caracteres), sin prefijo en pantalla."""
    return name_suffix[:80]


# (nombre categoría corto, lista de (nombre plato, precio, descripción opcional))
MENU: list[tuple[str, list[tuple[str, float, str]]]] = [
    (
        "Repostería salada",
        [
            ("Arreglados de carne y pollo", 2200, ""),
            ("Rollos de jamón y queso", 2100, ""),
            ("Pastel de pollo", 1500, ""),
            ("Pastel de jamón y queso", 1500, ""),
            ("Enchiladas", 1500, ""),
            ("Empanadas tradicionales (chilero de la casa)", 1800, ""),
            ("Almohabanas", 1300, ""),
            ("Palitos de queso", 800, ""),
            ("Orden de palitos de queso", 3000, ""),
            ("Empanada plátano maduro", 2000, ""),
        ],
    ),
    (
        "Repostería dulce",
        [
            ("Queque zanahoria", 2800, ""),
            ("Naranja con caramelo", 2800, ""),
            ("Pastel de chocolate", 2800, ""),
            ("Cheesecake", 2800, ""),
            ("Queque seco", 1800, "Preguntar disponibilidad"),
            ("Integral de nuez", 1800, ""),
            ("Rollos de canela", 2000, ""),
            ("Pan de elote", 1300, ""),
            ("Alfajores", 1200, ""),
            ("Tamal de queso crema", 1800, ""),
            ("Torta chilena", 2800, ""),
            ("Tamal de maicena", 1500, ""),
            ("Galletas coco", 850, ""),
            ("Galletas avena", 850, ""),
            ("Brownie", 1600, ""),
            ("Donas rellenas", 1800, ""),
            ("Queque red velvet", 2800, ""),
            ("Crocante", 2800, ""),
        ],
    ),
    (
        "Café caliente",
        [
            ("Espresso", 1000, ""),
            ("Americano pequeño", 1000, ""),
            ("Café con leche pequeño", 1500, ""),
            ("Café con leche grande", 1800, ""),
            ("Capuchino pequeño tradicional", 1800, ""),
            ("Capuchino grande tradicional", 2300, ""),
            ("Capuchino con sabor pequeño", 1800, ""),
            ("Capuchino con sabor grande", 2800, ""),
            ("Mocachino pequeño", 2000, ""),
            ("Mocachino grande", 2600, ""),
            ("Capuchino baileys", 3000, ""),
            ("Café irlandés", 3500, ""),
            ("Affogato", 2200, ""),
            ("Latte pequeño", 2000, ""),
            ("Latte grande", 2300, ""),
            ("Chocolate caliente", 1800, ""),
            ("Chocolate frangélico", 3000, ""),
            ("Chocolate con marshmallows", 2000, ""),
            ("Agua dulce", 1000, ""),
            ("Té", 1000, ""),
        ],
    ),
    (
        "Smoothies",
        [
            ("Smoothie piña (agua)", 1600, ""),
            ("Smoothie piña (leche)", 1900, ""),
            ("Smoothie papaya (agua)", 1600, ""),
            ("Smoothie papaya (leche)", 1900, ""),
            ("Smoothie frutas mixtas (agua)", 1600, ""),
            ("Smoothie frutas mixtas (leche)", 1900, ""),
            ("Smoothie fresa (agua)", 1600, ""),
            ("Smoothie fresa (leche)", 1900, ""),
            ("Smoothie mora (agua)", 1600, ""),
            ("Smoothie mora (leche)", 1900, ""),
            ("Smoothie sandía (agua)", 1600, ""),
            ("Smoothie sandía (leche)", 1900, ""),
            ("Limonada con HB (agua)", 1600, ""),
            ("Limonada con HB (leche)", 1900, ""),
            ("Piña con HB (agua)", 1600, ""),
            ("Piña con HB (leche)", 1900, ""),
        ],
    ),
    (
        "Burritos",
        [
            ("Burrito de carne", 3200, ""),
            ("Burrito de pollo", 3200, ""),
            ("Burrito mixto", 3500, ""),
        ],
    ),
    (
        "Café de especialidad",
        [
            ("Prensa francesa 2 tazas", 2000, ""),
            ("Prensa francesa 4 tazas", 3600, ""),
            ("Chemex 2 tazas", 2200, ""),
            ("Chemex 4 tazas", 4000, ""),
        ],
    ),
    (
        "Wraps",
        [
            ("Wrap pollo mechado", 4000, ""),
            ("Wrap jamón de pavo", 4000, ""),
            ("Wrap pechuga de pollo", 4000, ""),
        ],
    ),
    (
        "Sándwiches y tostadas",
        [
            ("Tostada Doña Cleo: aguacate, plátano, jamón pavo y queso", 3500, "Saladas"),
            ("Tostada plátano, pollo empanizado y queso fundido", 3800, ""),
            ("Sándwich carne mechada", 3300, "Panini o ciabatta"),
            ("Sándwich pollo mechado", 3300, ""),
            ("Sándwich jamón y queso", 3300, ""),
            ("Sándwich pechuga empanizada", 3900, ""),
        ],
    ),
    (
        "Café en los viajes",
        [
            ("Café Norte (ron crema y chantilly)", 3000, ""),
            ("Invierno (licor café, leche, chantilly, canela)", 3000, ""),
            ("Don Raúl (dulce de leche, chantilly, chocolate)", 3000, ""),
            ("Alaska (leche, whisky, miel, canela)", 3600, ""),
            ("Affogato viajes (helado vainilla, chocolate, espresso)", 3600, ""),
            ("Moca Vianes (chocolate, leche, chocolate rallado)", 3000, ""),
        ],
    ),
    (
        "Crêpes saladas",
        [
            ("Crêpe de pollo", 3000, ""),
            ("Crêpe de jamón y queso", 3000, ""),
        ],
    ),
    (
        "Crêpes dulces",
        [
            ("Crêpe crema de avellana", 3000, ""),
            ("Crêpe leche condensada", 3000, ""),
            ("Crêpe caramelo", 3000, ""),
        ],
    ),
    (
        "Café frío",
        [
            ("Capuchino tradicional frío", 2800, ""),
            ("Capuchino con sabor frío", 2800, ""),
            ("Moka frío", 2800, ""),
            ("Capuchino Oreo", 2700, ""),
            ("Milk shake", 2700, ""),
            ("Irlandés frío", 3200, ""),
            ("Chocolate frío", 2500, ""),
            ("Capuchino Baileys frío", 3000, ""),
            ("Latte frío", 2500, ""),
        ],
    ),
]


def main():
    parser = argparse.ArgumentParser(description="Carga menú Cleo Café")
    parser.add_argument("--franchisee-id", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Elimina menú Cleo previo y vuelve a cargar")
    args = parser.parse_args()

    from app import app
    from extensions import db
    from models import Category, Dish, Franchisee

    with app.app_context():
        if args.franchisee_id is not None:
            f = db.session.get(Franchisee, args.franchisee_id)
            if not f:
                print(f"No existe franquiciado id={args.franchisee_id}")
                sys.exit(1)
            fid = args.franchisee_id
        else:
            fr = Franchisee.query.filter_by(active=True).order_by(Franchisee.id).first()
            if not fr:
                print("No hay franquiciados.")
                sys.exit(1)
            fid = fr.id
            print(f"Usando franquiciado: {fr.name} (id={fid})")

        existing = Category.query.filter(
            Category.franchisee_id == fid,
            Category.description == CLEO_MENU_DESCRIPTION,
        ).first()

        if existing and not args.force:
            print(f"Ya existe menú {PREFIX} (mismas categorías). Usa --force para reemplazarlo.")
            sys.exit(0)

        if args.force:
            cats = Category.query.filter(
                Category.franchisee_id == fid,
                Category.description == CLEO_MENU_DESCRIPTION,
            ).all()
            for c in cats:
                Dish.query.filter_by(category_id=c.id).delete()
            for c in cats:
                db.session.delete(c)
            db.session.commit()
            print("Menú Cleo anterior eliminado.")

        created_c = 0
        created_d = 0
        for cat_short, dishes in MENU:
            cname = _cat(cat_short)
            cat = Category(
                franchisee_id=fid,
                name=cname,
                description=CLEO_MENU_DESCRIPTION,
                icon=suggest_icon_for_category_name(cname),
            )
            db.session.add(cat)
            db.session.flush()
            created_c += 1
            for dname, price, desc in dishes:
                d = Dish(
                    name=dname[:120],
                    description=(desc or "")[:300],
                    price=float(price),
                    available=True,
                    category_id=cat.id,
                )
                db.session.add(d)
                created_d += 1

        db.session.commit()
        print(f"Listo: {created_c} categorías, {created_d} platos.")


if __name__ == "__main__":
    main()
