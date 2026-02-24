"""
Añade campos HR a employees: cedula, fecha_salida, salario_base, tipo_contrato, jornada, vacaciones_dias_tomados.
Crea tabla vacation_records.
Uso: python scripts/migrate_hr_employee_fields.py
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

        float_type = "DOUBLE PRECISION" if dialect == "postgresql" else "REAL"
        cols = [
            ("cedula", "VARCHAR(20)"),
            ("fecha_salida", "DATE"),
            ("salario_base", float_type),
            ("tipo_contrato", "VARCHAR(30)"),
            ("jornada", "VARCHAR(20)"),
            ("vacaciones_dias_tomados", float_type),
        ]
        insp = inspect(db.engine)
        if "employees" in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns("employees")]
            for col_name, col_type in cols:
                if col_name in existing:
                    print(f"  employees.{col_name} ya existe.")
                else:
                    try:
                        db.session.execute(text(f"ALTER TABLE employees ADD COLUMN {col_name} {col_type}"))
                        db.session.commit()
                        print(f"  employees.{col_name} añadida.")
                    except Exception as e:
                        db.session.rollback()
                        print(f"  Error {col_name}:", e)

        print("Migración completada.")


if __name__ == "__main__":
    main()
