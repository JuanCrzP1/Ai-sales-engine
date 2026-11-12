# API del asistente

Otra plataforma (Leona, una página web, un servidor propio) le manda al asistente de un negocio el mensaje de un cliente y recibe la
respuesta para enviársela. Es el mismo asistente que atiende WhatsApp: responde con la configuración publicada del negocio, recuerda
a cada cliente, pasa el chat a una persona según el horario del equipo y gasta la clave de IA del negocio.

En el panel: **Integraciones → API del asistente** (dirección, claves, ejemplo para Leona y prueba).

## Autenticación

Cada petición lleva una clave de API del negocio:

```
Authorization: Bearer ase_live_...
```

- Las claves se crean en **Integraciones → Claves de API**. Se muestran **una sola vez**: la plataforma guarda solo su huella.
- La clave decide el negocio: la petición no lo elige.
- Necesita el permiso **Conversar con el asistente** (`assistant:chat`).
- Una clave revocada deja de funcionar enseguida (401).
- La clave es secreta: úsala desde un servidor o una plataforma como Leona, nunca en el código de una página web.

## Enviar un mensaje

```
POST {motor}/api/v1/assistant/messages
Content-Type: application/json
```

En producción, `{motor}` es `https://ai-sales-engine-mocha.vercel.app`.

### Cuerpo

```json
{
  "contact": { "id": "573001112233", "name": "Laura" },
  "message": "Hola, ¿qué precios tienen?"
}
```

| Campo | Obligatorio | Qué es |
|---|---|---|
| `contact.id` | Sí | Quién escribe: su teléfono o su id en tu plataforma (hasta 120 caracteres). El asistente recuerda a cada cliente por este dato. Con el mismo teléfono que usa en WhatsApp, el asistente lo reconoce como el mismo cliente |
| `contact.name` | No | Su nombre, para la bandeja (hasta 120) |
| `message` | Sí | Lo que escribió el cliente (hasta 4.000 caracteres) |

También acepta los campos sueltos `contact_id`, `contact_name` o `phone`, y `message` como `{"text": "..."}`, porque así arman el cuerpo
algunas plataformas de automatización.

### Encabezado opcional: `Idempotency-Key`

Si tu plataforma puede repetir un pedido (por ejemplo, porque no le llegó la respuesta), manda un identificador único por mensaje:

```
Idempotency-Key: leona-mensaje-8f3a2
```

Durante 24 horas, el mismo identificador devuelve **exactamente la misma respuesta** con `"duplicate": true`, sin volver a gastar la IA
ni repetir el mensaje en la bandeja. Si el primero todavía se está respondiendo, devuelve **409**.

### Respuesta (200)

```json
{
  "conversation_id": "6f1c...",
  "reply": "¡Hola Laura! El plan básico cuesta $50.000 al mes...",
  "parts": ["¡Hola Laura! El plan básico cuesta $50.000 al mes..."],
  "handoff": false,
  "handoff_reason": null,
  "attended_by": "assistant",
  "intent": "info",
  "stage": "interested",
  "fallback": false,
  "duplicate": false
}
```

| Campo | Qué es |
|---|---|
| `reply` | Todo lo que hay que enviarle al cliente. Vacío si el chat lo atiende el equipo |
| `parts` | Lo mismo en mensajes separados (por ejemplo, la respuesta y el aviso de espera), por si prefieres enviarlos uno por uno |
| `handoff` | `true` si el chat necesita a una persona: pásalo a tu equipo en tu plataforma |
| `handoff_reason` | Por qué: `human_request` (pidió una persona), `complaint` (reclamo), `payment_review` (reportó un pago) o `assistant` |
| `attended_by` | Quién atiende ahora: `assistant` o `team`. Con `team`, la IA está pausada en ese chat y no responde |
| `intent` | Lo que quiere el cliente: `info`, `pain`, `objection` o `buy` (puede ser `null`) |
| `stage` | La etapa del cliente: `new`, `interested`, `ready`, `payment` o `customer` |
| `fallback` | `true` si respondió con el mensaje de respaldo del negocio porque la IA no pudo (sin clave, sin saldo o el proveedor caído) |
| `duplicate` | `true` si es la respuesta guardada de un pedido repetido (`Idempotency-Key`) |
| `conversation_id` | El chat en la bandeja del panel |

### Cuando el chat pasa a una persona

Igual que en WhatsApp, según **Configuración → Atención humana**:

- **Dentro del horario del equipo:** `handoff: true`, `attended_by: "team"`, y `parts` trae además el aviso de espera («Una persona
  de nuestro equipo te responderá en unos 10 minutos»). La IA se pausa en ese chat: los mensajes siguientes devuelven `reply` vacío y
  `attended_by: "team"` hasta que alguien toque **Reanudar IA** en ese chat del panel, o hasta que la IA lo retome sola si nadie lo
  atendió a tiempo. Por la API no hay por dónde escribirle al cliente: la IA responde su próximo mensaje.
- **Fuera del horario:** `handoff: true`, `attended_by: "assistant"`. La IA sigue ayudando y `parts` trae el horario y cuándo lo
  atienden.

El equipo recibe el aviso en la campana del panel, por correo y en su celular.

## Errores

Siempre con el mismo formato:

```json
{ "code": "invalid", "message": "Revisa la petición.", "issues": [{ "path": "message", "message": "Envía el mensaje del cliente." }] }
```

| Estado | `code` | Qué pasó |
|---|---|---|
| 400 | `invalid_json` | El cuerpo no es un JSON válido |
| 401 | `invalid_api_key` | Falta la clave, no existe o fue revocada |
| 403 | `forbidden` | La clave no tiene el permiso para conversar |
| 409 | `duplicate_in_progress` | El mismo `Idempotency-Key` se está respondiendo: vuelve a intentarlo en unos segundos |
| 422 | `invalid` | Faltan datos o son demasiado largos (ver `issues`) |
| 429 | `rate_limited` | Demasiados mensajes seguidos: espera lo que dice `Retry-After` (segundos) |
| 503 | `unavailable` | El asistente no pudo responder: vuelve a intentarlo |

## Límites

- 60 mensajes por minuto por clave.
- 1.500 mensajes por hora por negocio, entre todas sus claves.

Protegen el saldo de IA del negocio si una clave se filtra o un flujo queda en un ciclo.

## Ejemplo: Leona

En el flujo, un bloque **Integración HTTP**:

| Campo del bloque | Valor |
|---|---|
| Método | `POST` |
| URL | `{motor}/api/v1/assistant/messages` |
| Encabezados | `Authorization: Bearer <tu clave>` y `Content-Type: application/json` |
| Cuerpo | `{"contact": {"id": "{customer.phone}", "name": "{customer.name}"}, "message": "{last_message}"}` |
| Campos de respuesta | `body.reply` → un campo del cliente (por ejemplo `respuesta_ia`); `body.handoff` → otro |

En la salida de éxito, un bloque **Mensaje** que envíe `{customer.respuesta_ia}`. Si `handoff` es `true`, pasa el chat al equipo
dentro de Leona. En la salida de fallo, un mensaje de respaldo o el paso al equipo.

## Ejemplo: terminal

```bash
curl -X POST "https://ai-sales-engine-mocha.vercel.app/api/v1/assistant/messages" \
  -H "Authorization: Bearer $AI_SALES_ENGINE_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: prueba-1" \
  -d '{"contact": {"id": "573001112233", "name": "Laura"}, "message": "Hola, ¿qué precios tienen?"}'
```

## Para quien mantiene la plataforma

- Ruta: `project/app/api/controllers/assistant_api.py`. Flujo: `project/app/application/channels/assistant_api.py`. Formato:
  `project/app/domain/business_config/assistant_api.py`.
- Tablas: `api_keys` (huella SHA-256 y comienzo visible de cada clave) y `api_idempotency` (respuestas cifradas, 24 horas),
  migración `0012_assistant_api.sql`. Los chats usan el canal `api` de `conversations`.
- Pruebas: `tests/test_assistant_api.py`.
