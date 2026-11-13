-- ============================================================================
-- 0018_telegram.sql
--
-- Telegram como canal de cada negocio: el negocio crea su bot con @BotFather y
-- pega el código (token) en Canales. Va en `business_channels` con
-- channel = 'telegram': el token cifrado, el identificador secreto del webhook
-- y el estado. Aquí se agrega la cuenta del canal: el id del bot en Telegram
-- (`account_id`) y su usuario (`account_username`, para el enlace t.me/...).
-- Un mismo bot nunca queda en dos negocios: lo garantiza el índice único, no el
-- código (dos personas pueden conectarlo a la vez).
-- Aditiva. La misma definición, para SQLAlchemy, está en
-- project/app/infrastructure/business_config/tables.py. Se puede aplicar más de
-- una vez.
-- ============================================================================

BEGIN;

ALTER TABLE business_channels ADD COLUMN IF NOT EXISTS account_id TEXT;
ALTER TABLE business_channels ADD COLUMN IF NOT EXISTS account_username TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS business_channels_account_key
  ON business_channels (channel, account_id)
  WHERE account_id IS NOT NULL;

COMMIT;
