"""Normalización de entradas del CRUD de clientes."""

TEXT_LIMITS = {"name": 200, "tax_id": 50, "email": 120, "phone": 40, "address": 300, "notes": 500}


def parse_active(value):
    if isinstance(value, bool):
        return value
    if type(value) is int and value in (0, 1):
        return value == 1
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "1", "yes"):
            return True
        if text in ("false", "0", "no"):
            return False
    raise ValueError("El estado activo debe ser true, false, 1 o 0")


def normalize_client_payload(data, partial=False):
    if not isinstance(data, dict):
        raise ValueError("Se requiere un objeto JSON")
    result = {}
    for field, maximum in TEXT_LIMITS.items():
        if field not in data and (partial or field != "name"):
            continue
        value = data.get(field)
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"El campo {field} debe ser texto")
        value = value.strip()
        if field == "name" and not value:
            raise ValueError("El nombre es obligatorio")
        if len(value) > maximum:
            raise ValueError(f"El campo {field} admite hasta {maximum} caracteres")
        result[field] = value or None
    if "active" in data:
        result["active"] = parse_active(data["active"])
    elif not partial:
        result["active"] = True
    return result
