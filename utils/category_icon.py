"""Iconos Bootstrap Icons (sin prefijo bi-) sugeridos según el nombre de categoría."""
from __future__ import annotations

# Nombres válidos: https://icons.getbootstrap.com/ (clase sin prefijo bi-)


def suggest_icon_for_category_name(name: str | None) -> str:
    """
    Devuelve el sufijo de icono Bootstrap, p. ej. 'cup-hot' -> clase 'bi bi-cup-hot'.
    Valor por defecto: 'tag'.
    """
    if not name or not str(name).strip():
        return "tag"
    n = str(name).strip().lower()

    exact = {
        "repostería salada": "shop",
        "reposteria salada": "shop",
        "repostería dulce": "cake2",
        "reposteria dulce": "cake2",
        "café caliente": "cup-hot",
        "cafe caliente": "cup-hot",
        "smoothies": "cup-straw",
        "burritos": "bag-heart",
        "café de especialidad": "filter",
        "cafe de especialidad": "filter",
        "wraps": "list-ul",
        "sándwiches y tostadas": "egg-fried",
        "sandwiches y tostadas": "egg-fried",
        "café en los viajes": "airplane-fill",
        "cafe en los viajes": "airplane-fill",
        "crêpes saladas": "circle-half",
        "crepes saladas": "circle-half",
        "crêpes dulces": "heart-fill",
        "crepes dulces": "heart-fill",
        "café frío": "snow",
        "cafe frio": "snow",
        "café frio": "snow",
    }
    if n in exact:
        return exact[n]

    # Palabras clave (orden: más específico primero)
    if any(x in n for x in ("smoothie", "jugo", "batido")):
        return "cup-straw"
    if any(x in n for x in ("frío", "frio", "helado", "frappe")):
        return "snow"
    if any(x in n for x in ("café", "cafe", "coffee", "espresso", "moka", "latte", "capuchino", "té", "te ")):
        return "cup-hot"
    if any(x in n for x in ("dulce", "postre", "pastel", "queque", "torta", "brownie", "donut")):
        return "cake2"
    if any(x in n for x in ("salada", "salado", "empanada", "burrito", "wrap", "sandwich", "sándwich", "tostada")):
        return "egg-fried"
    if any(x in n for x in ("burrito",)):
        return "bag-heart"
    if any(x in n for x in ("wrap",)):
        return "list-ul"
    if any(x in n for x in ("crep", "crepa")):
        return "circle-half"
    if any(x in n for x in ("bebida", "agua", "gaseosa", "refresco")):
        return "droplet"
    if any(x in n for x in ("especial", "chef", "plato principal")):
        return "stars"
    if any(x in n for x in ("entrante", "ensalada", "sopa")):
        return "leaf"
    if any(x in n for x in ("desayuno",)):
        return "sunrise"
    if any(x in n for x in ("cena", "almuerzo", "menú del día", "menu del dia")):
        return "calendar-event"
    return "tag"


# Emoji para etiquetas en <select> (HTML no permite iconos en <option>)
ICON_EMOJI: dict[str, str] = {
    "tag": "📁",
    "shop": "🥐",
    "cake2": "🍰",
    "cup-hot": "☕",
    "cup-straw": "🥤",
    "snow": "🧊",
    "bag-heart": "🌯",
    "filter": "⚗️",
    "list-ul": "🌯",
    "egg-fried": "🥪",
    "airplane-fill": "✈️",
    "circle-half": "🥞",
    "heart-fill": "💗",
    "droplet": "💧",
    "stars": "⭐",
    "leaf": "🥗",
    "sunrise": "🌅",
    "calendar-event": "📅",
    "heart": "💝",
}


def emoji_for_icon_suffix(icon: str | None) -> str:
    if not icon:
        return ICON_EMOJI["tag"]
    return ICON_EMOJI.get(icon.strip(), "📁")
