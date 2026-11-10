-- ============================================================================
-- 0006_rate_limits.sql
--
-- Límites de uso: un contador por ventana de tiempo (`bucket` dice qué se cuenta y
-- de quién, por ejemplo `playground_user:<usuario>`). Lo comparten todas las
-- instancias del servidor. Cada contador borra sus ventanas viejas al contar.
-- La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py; una prueba comprueba que
-- ambas coinciden. Se puede aplicar más de una vez.
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS rate_limits (
  bucket        TEXT NOT NULL,
  window_start  TIMESTAMPTZ NOT NULL,
  hits          INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket, window_start)
);

COMMIT;
