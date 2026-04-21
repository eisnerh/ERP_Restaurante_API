"""
Crea el franquiciado «Cleo Café» (si no existe) y reasigna todos los datos
de otra casa a esa nueva.

Uso:
  python scripts/migrate_to_cleo_cafe.py --from-id 4
  python scripts/migrate_to_cleo_cafe.py --from-id 4 --keep-source-active

Requisito: la casa destino debe estar vacía de datos (primera vez) o no haber
nombres/códigos duplicados con la origen (unique por franquiciado).
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

CLEO_NAME = "Cleo Café"
CLEO_CODE = "CLEO"

# Modelos con franchisee_id NOT NULL (orden libre; sin FK entre ellos hacia franchisee)
MODELS_FRANCHISEE = []


def _register_models():
    global MODELS_FRANCHISEE
    from models import (
        Category,
        Table,
        Supplier,
        Client,
        InventoryItem,
        InventoryAlert,
        PurchaseOrder,
        PayrollLocation,
        Employee,
        Payslip,
        PaymentRecord,
        OperationalExpense,
        Invoice,
        CashRegisterSession,
        DiscountReason,
        PaymentMethod,
    )
    MODELS_FRANCHISEE = [
        Category,
        Table,
        Supplier,
        Client,
        InventoryItem,
        InventoryAlert,
        PurchaseOrder,
        PayrollLocation,
        Employee,
        Payslip,
        PaymentRecord,
        OperationalExpense,
        Invoice,
        CashRegisterSession,
        DiscountReason,
        PaymentMethod,
    ]


def get_or_create_cleo(db):
    from models import Franchisee
    from sqlalchemy import or_

    f = Franchisee.query.filter(
        or_(
            Franchisee.name.ilike(CLEO_NAME),
            Franchisee.name.ilike("Cleo Cafe"),
        )
    ).first()
    if f:
        return f, False
    code = CLEO_CODE
    if Franchisee.query.filter_by(code=code).first():
        code = None
    f = Franchisee(code=code, name=CLEO_NAME, active=True)
    db.session.add(f)
    db.session.flush()
    return f, True


def migrate_app_settings(db, old_id: int, new_id: int) -> int:
    from models import AppSettings

    n = AppSettings.query.filter(AppSettings.franchisee_id == old_id).update(
        {"franchisee_id": new_id},
        synchronize_session=False,
    )
    return n


def main():
    parser = argparse.ArgumentParser(description="Migrar datos a la casa Cleo Café")
    parser.add_argument(
        "--from-id",
        type=int,
        required=True,
        help="ID del franquiciado origen (ej. Plaza San Carlos)",
    )
    parser.add_argument(
        "--keep-source-active",
        action="store_true",
        help="No desactivar el franquiciado origen tras migrar",
    )
    args = parser.parse_args()

    from app import app
    from extensions import db
    from models import Franchisee

    _register_models()

    with app.app_context():
        src = db.session.get(Franchisee, args.from_id)
        if not src:
            print(f"No existe franquiciado id={args.from_id}")
            sys.exit(1)

        cleo, created = get_or_create_cleo(db)
        if cleo.id == src.id:
            print("El origen ya es Cleo Café; no hay nada que migrar.")
            sys.exit(0)

        total = 0
        for Model in MODELS_FRANCHISEE:
            n = Model.query.filter_by(franchisee_id=src.id).update(
                {"franchisee_id": cleo.id},
                synchronize_session=False,
            )
            if n:
                print(f"  {Model.__tablename__}: {n} filas")
            total += n

        n_settings = migrate_app_settings(db, src.id, cleo.id)
        if n_settings:
            print(f"  app_settings: {n_settings} filas")
        total += n_settings

        if not args.keep_source_active:
            src.active = False

        db.session.commit()

        action = "Creado" if created else "Usado existente"
        print(f"\n{action}: {CLEO_NAME} (id={cleo.id}, code={cleo.code or '—'})")
        print(f"Origen id={src.id} ({src.name}): migradas {total} filas con franchisee_id.")
        if not args.keep_source_active:
            print(f"Origen desactivado. Actívalo en Casos si lo necesitas.")
        print(f"\nSelecciona la casa en la app o abre: /?franchisee_id={cleo.id}")


if __name__ == "__main__":
    main()
