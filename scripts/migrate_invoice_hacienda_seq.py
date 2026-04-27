"""
Añade app_settings.invoice_hacienda_last_seq y alinea con facturas ya emitidas por franquicia.
Ejecutar: python scripts/migrate_invoice_hacienda_seq.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from sqlalchemy import text


def migrate():
    with app.app_context():
        db.create_all()
        conn = db.engine.connect()
        try:
            r = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'app_settings'
                  AND column_name = 'invoice_hacienda_last_seq'
            """))
            if r.fetchone() is None:
                conn.execute(text(
                    "ALTER TABLE app_settings ADD COLUMN invoice_hacienda_last_seq INTEGER NOT NULL DEFAULT 0"
                ))
                conn.commit()
                print("Columna invoice_hacienda_last_seq añadida.")
            else:
                print("Columna invoice_hacienda_last_seq ya existe.")

            # Alinear: último secuencial = cantidad de facturas ya guardadas (comportamiento previo next = count + 1)
            conn.execute(text("""
                UPDATE app_settings AS a
                SET invoice_hacienda_last_seq = sub.cnt
                FROM (
                    SELECT franchisee_id, COUNT(*)::integer AS cnt
                    FROM invoices
                    GROUP BY franchisee_id
                ) AS sub
                WHERE a.franchisee_id IS NOT NULL
                  AND a.franchisee_id = sub.franchisee_id
            """))
            conn.commit()
            print("Valores iniciales sincronizados con facturas existentes (por franquicia).")

            r = conn.execute(text(
                "SELECT 1 FROM pg_constraint WHERE conname = 'uq_app_settings_franchisee_id'"
            ))
            if r.fetchone() is None:
                conn.execute(text("""
                    DELETE FROM app_settings WHERE id IN (
                        SELECT id FROM (
                            SELECT id,
                                ROW_NUMBER() OVER (
                                    PARTITION BY franchisee_id
                                    ORDER BY invoice_hacienda_last_seq DESC, id DESC
                                ) AS rn
                            FROM app_settings
                            WHERE franchisee_id IS NOT NULL
                        ) d WHERE d.rn > 1
                    )
                """))
                conn.commit()
                conn.execute(text(
                    "ALTER TABLE app_settings "
                    "ADD CONSTRAINT uq_app_settings_franchisee_id UNIQUE (franchisee_id)"
                ))
                conn.commit()
                print("Restricción UNIQUE(franchisee_id) añadida en app_settings (duplicados eliminados).")
            else:
                print("Restricción uq_app_settings_franchisee_id ya existe.")
        except Exception as e:
            print("Error:", e)
            conn.rollback()
        finally:
            conn.close()
    print("Listo.")


if __name__ == "__main__":
    migrate()
