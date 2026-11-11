# Negocios (tenants)

Cómo se identifica y se aísla cada negocio, y qué son los negocios de ejemplo.

## Qué es un negocio

Un negocio es una fila de `tenants` en la base (Neon en la nube, SQLite o PostgreSQL en este equipo), identificada por su `slug`.
Todo lo demás cuelga de él y se filtra por su id:

| Qué | Dónde |
|---|---|
| Dueño (cuenta de Neon Auth) | `business_members` |
| Configuración comercial, en versiones (borrador, publicada, archivadas) | `business_configs` |
| Datos de pago (cifrados; el documento solo guarda referencias `secret_store:`) | `business_config_secrets` |
| Ajustes técnicos del motor | `business_engine_settings` |
| Clave de IA y modelo (cifrada) | `business_ai_settings` |
| Consumo de IA por día y modelo | `ai_usage` |
| Canal de WhatsApp por QR (token de la instancia, cifrado) | `business_channels` |
| Conversaciones, mensajes y archivos | `conversations`, `conversation_entries`, `conversation_media` |
| Ventas | `sales` |
| Avisos al equipo | `notifications` |

La memoria que el asistente guarda de cada cliente vive en las tablas del motor (`clients`, `conversation_messages`,
`conversation_memory`), por negocio y número del cliente. Eliminar un chat desde el panel borra la conversación y también esa
memoria (ver `architecture.md`, «Eliminar Un Chat»); las ventas se conservan.

Cada consulta del almacén parte de `tenancy.tenant_of(slug)` y solo alcanza las filas de ese negocio. Una cuenta que pide un
negocio ajeno recibe lo mismo que si no existiera (404).

No hay negocio por defecto: cada mensaje dice de qué negocio es, y si no se puede leer su versión publicada el cliente recibe un
mensaje neutro y queda la alerta `business_config_unavailable`.

## Cómo llega un mensaje a su negocio

| Entrada | Cómo sabe de qué negocio es |
|---|---|
| WhatsApp por QR (uazapi): `POST /api/v1/channels/whatsapp/{webhook_id}` | El `webhook_id` secreto de `business_channels`, más el token de la instancia que trae cada aviso |
| WhatsApp Cloud API de Meta: `POST /api/v1/whatsapp/webhook` | El `phone_number_id` del aviso (`services/tenant_channel_resolver.py`), con la firma de Meta |
| Panel en la nube (`/panel/api/...`) | La cuenta de Neon Auth (JWT) y su fila en `business_members` |
| Panel local (`127.0.0.1:8010`) | Solo este equipo, sin cuentas: el operador local ve todos los negocios |

Con el negocio identificado, el motor carga su versión publicada (`application/runtime/tenant_runtime_loader.py`) y responde con
la clave de IA de ese negocio.

## Negocios de ejemplo

`project/config/tenants/<slug>/` tiene 9 negocios de ejemplo (agencia de viajes, asesor de IA, clínica, demo, ecommerce, escuela
de conducción, restaurante, software y tienda de ropa). Cada uno son tres archivos en el formato del contrato:

- `business-config.json`: el documento comercial; los datos de pago son referencias `secret_store:`, nunca valores.
- `engine-settings.json`: sus ajustes técnicos.
- `payment-values.json`: los datos de pago de ejemplo (ficticios); al importarlos se guardan cifrados.

Siembran este equipo («Importar negocios de ejemplo» en el panel local o `scripts/init_local_business_config.py
--import-tenants`), la rama `pruebas` de Neon (`scripts/setup_cloud_database.py`), las pruebas automáticas y los laboratorios.
**Nunca se cargan en producción** y el motor nunca los lee: en la nube cada cuenta crea sus negocios.

Para cambiar un ejemplo se edita su JSON. Si el cambio es a propósito, se regenera su referencia congelada
(`python tests/golden/regenerate.py <slug>`). Las pruebas comprueban que cada ejemplo compila exactamente a su referencia.

Antes eran cinco YAML por negocio (`business`, `config`, `inventory`, `pricing`, `sales`). Se retiraron el 11 de noviembre de
2026, después de comprobar que los JSON compilan exactamente a lo mismo (`tests/golden/README.md`).

## Planes y cobros

La plataforma no cobra ni tiene suscripciones (decisión del 10 de noviembre de 2026). Los precios, planes, catálogos y medios de
pago de cada configuración son lo que ese negocio vende a sus propios clientes.
