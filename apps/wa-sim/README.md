# WhatsApp simulado

Un WhatsApp falso para probar AI Sales Engine completo en tu equipo, sin números reales: hace de **servidor de uazapi** para el panel
y el motor, y trae un **teléfono de prueba** en el navegador para escribir como cliente.

Solo para desarrollo: no arranca en producción ni en Vercel, vive fuera de `project/` (lo único que se publica) y nada sale a WhatsApp.
Es la misma idea que el simulador de Auream (`Auream-Os/apps/wa-sim`), en Python como el resto del servidor.

## Cómo funciona

```
  Teléfono de prueba (navegador, :3300)
        │  el «cliente» escribe, manda una foto, abre el chat
        ▼
  phone/api ──> core/simulator ──> webhooks/notifier ──> motor /api/v1/channels/whatsapp/<id>
                                                              │
                                    (lectores reales de uazapi, IA, pagos, paso a una persona, bandeja)
                                                              │
  core/simulator <── provider/api <── UazapiClient real (/send/text, /send/media, /message/download…)
        │
        └──> ✓✓ (entregado) al rato y azul (leído) al abrir el chat ──> motor (recibos)
```

El panel y el motor **no cambian de código**: con `WHATSAPP_SIMULATOR_URL`, `uazapi_platform()` usa el simulador como si fuera
el servidor de uazapi (`project/app/infrastructure/channels/platform.py`). Esa variable solo se acepta con `http://localhost` o
`http://127.0.0.1`, y se ignora en producción y en Vercel.

| Carpeta | Responsabilidad |
|---|---|
| `core/` | El estado del WhatsApp falso (números, clientes, mensajes) y sus reglas: vincular por QR, entregar, leer. Se guarda en `.wa-sim/state.json`. |
| `webhooks/` | Traduce lo que pasa al **formato de aviso de uazapi** y se lo envía al motor (solo los eventos que pidió). El QR de prueba. |
| `provider/` | La **API de uazapi** que usan el panel y el motor, con sus mismos tokens y errores. |
| `phone/` | El **teléfono de prueba**: su API (`/_sim/*`) y su página. |

## Probarlo a mano

En tres terminales, desde la raíz del repositorio:

```bash
# 1. El simulador (teléfono de prueba en http://localhost:3300)
cd apps/wa-sim && ../../.venv/bin/python -m wa_sim

# 2. El motor, confiando en el simulador
cd project && WHATSAPP_SIMULATOR_URL=http://127.0.0.1:3300 ../.venv/bin/python -m uvicorn app.main:app --port 8082

# 3. La API del panel, apuntando al simulador y al motor
WHATSAPP_SIMULATOR_URL=http://127.0.0.1:3300 ENGINE_PUBLIC_URL=http://127.0.0.1:8082 .venv/bin/python scripts/run_admin_api.py
```

1. En el panel, **Canales → Conectar WhatsApp**. En el teléfono de prueba aparece el número «Esperando el QR»: toca **Escanear QR**.
2. Agrega un **cliente de prueba** (nombre y número con país, por ejemplo `573001112233`) y abre su chat.
3. Escribe como cliente: el asistente responde con la IA real del negocio (con su clave). Prueba pagos, fotos, notas de voz.
4. Marca **Escribir como el negocio (desde su celular)** para probar lo que el equipo escribe desde su teléfono.
5. **Ver lo que pasó** muestra lo que pidió el panel o el motor y cada aviso enviado, con su respuesta.

**Empezar de cero** borra números, clientes y mensajes del simulador; en el panel hay que volver a conectar.

## Pruebas automáticas

```bash
.venv/bin/python -m pytest tests/test_wa_simulator_contract.py   # el contrato con uazapi
.venv/bin/python -m pytest tests/test_whatsapp_e2e.py            # los recorridos de punta a punta
```

- **El contrato** usa el cliente y los lectores **reales** de uazapi del motor contra el simulador. Si falla, el simulador y el motor
  ya no hablan igual: se ajustan juntos.
- **Los recorridos** levantan solos el simulador y el motor (servidores de verdad, en puertos libres) y el panel, con un modelo de
  IA de respuestas fijas. Cuentan días de negocio:
  - un día por WhatsApp: conectar por QR, saludo, ✓✓ y leído, pregunta, pago por Nequi, «se me borró el número», comprobante en
    foto, respuesta y PDF del equipo, el negocio escribiendo desde su celular y desconectar;
  - un negocio de Perú: Yape, «otro medio» y efectivo;
  - dos negocios a la vez: nada se cruza (chats ni datos de pago);
  - pagos con los 15 medios a la vez: cada uno llega solo (y solo el suyo) al elegirlo o pedirlo de nuevo, dos bancos, una cuenta
    desactivada, un medio que no existe, preguntar sin elegir y la IA que nunca ve los datos;
  - pagos como habla la gente: «pásame el nekui», «me regalas la cuenta de bancolombia», «¿a dónde te consigno?», «¿y Daviplata
    no?», «ya te consigné», «te mando el pantallazo»…
- Dejan un informe en español en `.wa-sim/informe-e2e.md`, sin datos de pago.

Para sumar un escenario: una función `test_…` en `tests/test_whatsapp_e2e.py` con sus pasos (`_run(Report(...), pasos)`).

## Configuración

| Variable | Por defecto | Para qué |
|---|---|---|
| `SIM_PORT` | `3300` | Puerto del simulador y del teléfono (Auream usa el 3200). |
| `SIM_ADMIN_TOKEN` | `simulador` | Token de administrador. Debe coincidir con `WHATSAPP_SIMULATOR_TOKEN` del panel (por defecto `simulador`). |
| `SIM_DATA_DIR` | `.wa-sim` | Estado del simulador. Ignorado por git. |
| `SIM_RECEIPT_SECONDS` | `0.7` | Cuánto tarda el ✓✓ de lo que envía el negocio. |

## Límites (a propósito)

- No imita la red de WhatsApp: no hay bloqueos, límites de envío ni números que no existen.
- El QR no se escanea con un celular: se «escanea» con el botón del teléfono de prueba.
- Telegram todavía no tiene simulador: sus pruebas usan una API de Telegram simulada dentro de `tests/test_telegram_channel.py`.
