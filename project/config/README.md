# Configuración (`project/config/`)

La configuración de cada negocio **no vive aquí**: se edita en el panel y se guarda, en versiones, en la base (Neon en la nube).
El motor solo usa la versión publicada. Esta carpeta guarda lo que es de la plataforma y los negocios de ejemplo.

| Carpeta | Qué hay | Quién lo lee |
|---|---|---|
| `system/` | Ajustes de la plataforma: `settings.yaml`, `bot_config.yaml`, `conversation_stage.yaml` y `secrets.yaml` (sin valores reales: los secretos van en variables de entorno). Se leen en ese orden y cada uno completa al anterior | El motor al arrancar (`app/config/settings/base.py`) |
| `tenants/<negocio>/` | Los 9 negocios de ejemplo: `business-config.json`, `engine-settings.json` y `payment-values.json` (datos de pago ficticios) | La importación de ejemplos (panel local, `scripts/`), las pruebas y los laboratorios. Nunca el motor ni producción |
| `contracts/v1/` | El esquema publicado del contrato (`business-config.schema.json`, generado) y un documento de ejemplo | El panel (tipos generados) y las pruebas |
| `business-templates/` | Plantillas para empezar un negocio (restaurante, tienda, software, agencia de viajes, escuela, servicios con cita) | El panel, al crear un negocio |

## Cambiar algo

- **Un negocio real:** en el panel. Se guarda como borrador y llega a los clientes al publicarlo.
- **Un negocio de ejemplo:** su JSON en `tenants/<negocio>/`. Si el cambio es a propósito, regenera su referencia congelada
  (`python tests/golden/regenerate.py <negocio>`); las pruebas comparan cada ejemplo con ella. Los datos de pago van solo en
  `payment-values.json` y deben ser ficticios.
- **El contrato:** el modelo está en `app/domain/business_config/contract/`; después se regenera lo derivado (ver
  `../../CONTRIBUTING.md`).
- **Un ajuste de la plataforma:** `system/settings.yaml` o `system/bot_config.yaml`. Afecta a todos los negocios.

## Historia

Hasta el 11 de noviembre de 2026 cada negocio de ejemplo eran cinco YAML (`business`, `config`, `inventory`, `pricing`, `sales`),
y también había `channels/channels.yaml` y `assets/media.yaml`, que nadie leía. Se retiraron después de comprobar que los JSON
compilan exactamente a lo mismo; lo que el motor recibía de ellos quedó congelado en `tests/golden/`, y adónde fue cada campo
antiguo, en `docs/business-config-traceability.md`.
