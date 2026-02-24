-- Añade la columna purchase_price a inventory_items (PostgreSQL)
-- Ejecutar con: psql -U postgres -d restaurant_erp -f scripts/add_purchase_price.sql
-- O desde psql: \i scripts/add_purchase_price.sql

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'inventory_items' AND column_name = 'purchase_price'
  ) THEN
    ALTER TABLE inventory_items ADD COLUMN purchase_price DOUBLE PRECISION;
    RAISE NOTICE 'Columna purchase_price añadida.';
  ELSE
    RAISE NOTICE 'La columna purchase_price ya existe.';
  END IF;
END $$;
