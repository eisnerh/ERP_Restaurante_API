"""
Crea tablas positions y deduction_types, añade position_id a employees, payroll_entries, payslips
y deduction_type_id a payslip_lines.
Uso: python scripts/migrate_add_positions_deductions.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def main():
    from app import app
    from extensions import db

    with app.app_context():
        from sqlalchemy import text, inspect
        dialect = db.engine.dialect.name
        print(f"Conectado a: {dialect}")

        db.create_all()

        alterations = [
            ("employees", "position_id"),
            ("payroll_entries", "position_id"),
            ("payslips", "position_id"),
            ("payslip_lines", "deduction_type_id"),
        ]
        for table, col_to_add in alterations:
            try:
                insp = inspect(db.engine)
                if table not in insp.get_table_names():
                    continue
                cols = [c["name"] for c in insp.get_columns(table)]
                if col_to_add in cols:
                    print(f"  {table}.{col_to_add} ya existe.")
                else:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_to_add} INTEGER"))
                    db.session.commit()
                    print(f"  {table}.{col_to_add} añadida.")
            except Exception as e:
                db.session.rollback()
                err = str(e).lower()
                if "duplicate column" in err or "already exists" in err:
                    print(f"  {table}.{col_to_add} ya existe.")
                else:
                    print(f"  Error en {table}:", e)

        print("Migración completada.")


if __name__ == "__main__":
    main()
