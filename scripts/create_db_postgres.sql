-- Script SQL para crear la base de datos PostgreSQL manualmente.
--
-- Ejecutar:
--   psql -U postgres -f scripts/create_db_postgres.sql
--
-- O desde psql conectado como postgres:
--   \i scripts/create_db_postgres.sql
--
-- Luego crear las tablas con:
--   python scripts/create_tables.py

CREATE DATABASE restaurant_erp;  -- Si ya existe, dará error (ignorar)
