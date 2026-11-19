-- ============================================================================
-- 0023_retire_legacy_tables.sql
--
-- Retira las tablas del sistema anterior que ya no usa ningún código (el
-- código se retiró el 18 de noviembre de 2026, docs/plan-v1.md, Fase 6):
-- - admin_users: las cuentas del login viejo (las cuentas son de Neon Auth y
--   cada negocio llega a las suyas por business_members).
-- - tenant_secrets: las credenciales de los conectores viejos (las de cada
--   canal viven cifradas en business_channels).
-- - tenant_channels: los canales del webhook de Meta, que ya no existe.
-- - tenant_settings: ajustes por negocio que nadie leía (lo publicado vive en
--   business_configs y business_engine_settings).
-- En producción las cuatro estaban vacías al retirarlas. Nada depende de ellas:
-- solo tienen llaves hacia tenants, que se queda (es la raíz de la memoria del
-- motor y del almacén). Sin CASCADE a propósito: si algo inesperado dependiera
-- de una, la migración falla y no borra nada. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

DROP TABLE IF EXISTS admin_users;
DROP TABLE IF EXISTS tenant_secrets;
DROP TABLE IF EXISTS tenant_channels;
DROP TABLE IF EXISTS tenant_settings;

COMMIT;
