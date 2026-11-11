# Motor y API del panel (`project/`)

El backend de AI Sales Engine (FastAPI). En la nube corre en Vercel con Neon; en este equipo, con `run_local`.

## Qué hace

- Recibe los mensajes de los canales (WhatsApp por QR con uazapi y la API de Meta), identifica el negocio y responde con su
  versión publicada y su propia clave de IA.
- Guarda cada conversación para la bandeja del panel, entiende fotos y notas de voz, y pasa la conversación a una persona cuando
  corresponde.
- Publica la API del panel: en la nube bajo `/panel` (cuentas de Neon Auth); en este equipo, `scripts/run_admin_api.py` en
  `127.0.0.1:8010`, sin cuentas.

## Rutas del motor

| Ruta | Para qué |
|---|---|
| `GET /health` | Estado del motor (no nombra ningún negocio) |
| `POST /api/v1/channels/whatsapp/{webhook_id}` | Avisos de la instancia de WhatsApp por QR de cada negocio |
| `GET`/`POST /api/v1/whatsapp/webhook` | Webhook de la API de Meta (exige su firma) |
| `POST /api/v1/simulate` | Apagado por defecto (404) |
| `/panel/api/...` | API del panel en la nube (solo con `NEON_AUTH_URL`) |

## Dónde está cada cosa

| Carpeta | Qué hay |
|---|---|
| `app/api/` | Rutas del motor: webhooks y simulación |
| `app/application/` | Pipeline de la IA (`ai_pipeline.py`, `pipeline/`), carga de lo publicado (`runtime/`), entrada de WhatsApp (`channels/`) |
| `app/infrastructure/ai/prompting/` | El prompt por bloques |
| `app/domain/business_config/` | El contrato del negocio, su compilador y sus reglas |
| `app/business_config_application/` | Casos de uso del panel: configuración, conversaciones, ventas, canales, IA, «Probar» |
| `app/infrastructure/business_config/` | El almacén (tablas, migraciones, cifrado, conversaciones, ventas) y los negocios de ejemplo |
| `app/admin_api/` | La API del panel |
| `app/cloud_panel.py` | Arma la API del panel de la nube y aplica las migraciones al arrancar |
| `config/system/` | Ajustes de la plataforma: `settings.yaml`, `bot_config.yaml`, `conversation_stage.yaml`, `secrets.yaml` |
| `config/tenants/<negocio>/` | Los negocios de ejemplo (JSON); ver `../docs/tenants.md` |
| `config/contracts/v1/` | Esquema del contrato y un documento de ejemplo |
| `config/business-templates/` | Plantillas para empezar un negocio desde el panel |
| `docs/postgresql_schema.sql` | Esquema de las tablas del motor (lo aplica `setup_cloud_database.py` si faltan) |
| `db/migrations/` | Migraciones del almacén, en orden |

## Ejecutar

Desde la raíz: `./run_local.sh` (o `run_local.bat`). Ver `../docs/quickstart.md`.

## Variables

Ver `../docs/operations.md`, «Variables De Entorno». Lo esencial: `DATABASE_URL` (memoria del motor),
`BUSINESS_CONFIG_DATABASE_URL` y `BUSINESS_CONFIG_SECRETS_KEY` (almacén y cifrado), `NEON_AUTH_URL` (panel en la nube),
`UAZAPI_BASE_URL` y `UAZAPI_ADMIN_TOKEN` (WhatsApp por QR, de la plataforma). La clave de IA no es una variable: cada negocio pone
la suya en el panel.

## Scripts (`../scripts/`)

| Script | Para qué |
|---|---|
| `run_admin_api.py` | API local del panel, solo en `127.0.0.1:8010` |
| `init_local_business_config.py` | Crea el almacén local; con `--import-tenants`, importa los negocios de ejemplo |
| `setup_cloud_database.py` | Deja lista una rama de Neon (`production`: solo el esquema; `pruebas`: también los ejemplos) |
| `bootstrap_saas_data.py` | Filas del sistema anterior por cada negocio de ejemplo (lo usa `setup_cloud_database.py`) |
| `assign_business_to_account.py` | Crea en una rama de Neon un negocio de ejemplo a nombre de una cuenta que ya existe, o la agrega como dueña |
| `local_secrets.py` | Mueve y comprueba los secretos locales (`secrets.local.env`) sin mostrarlos |
| `export_business_config_schema.py`, `generate_business_config_types.py`, `generate_traceability_matrix.py` | Regeneran lo derivado del contrato (`--check` para comprobar) |
| `reset_conversation_state.py` | Borra la memoria conversacional en PostgreSQL |

## Pruebas

Desde la raíz: `pytest`. Ver `../CONTRIBUTING.md`.
