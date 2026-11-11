# Inicio rápido

## En la nube

El panel publicado en Vercel es la forma normal de usar la plataforma:

1. Crea tu cuenta (Neon Auth) y tu negocio; puedes empezar desde una plantilla.
2. En **Asistente IA**, completa lo que vendes, precios, pagos y cómo vendes. Guarda y **publica**: el asistente solo usa lo
   publicado.
3. En **Ajustes → Inteligencia artificial**, pega tu clave de OpenRouter y elige el modelo.
4. En **Probar asistente**, conversa con él usando la IA real.
5. En **Canales**, toca «Conectar WhatsApp» y escanea el código QR con el WhatsApp del negocio.
6. Atiende en **Conversaciones**; registra ventas en **Clientes** o **Ventas**; mira el resultado en **Reportes**.

## En este equipo

Requisitos: Python 3.11 o superior, Node (versión de `apps/admin-web/.nvmrc`), PostgreSQL para la memoria del motor (Docker:
`docker compose up -d db`) y, para WhatsApp en local, ngrok.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .\.venv\Scripts\Activate.ps1
pip install -r project/requirements-dev.txt
npm --prefix apps/admin-web install
./run_local.sh                         # Windows: run_local.bat
```

`run_local` arranca:

| Servicio | Dónde |
|---|---|
| Motor (webhooks y pipeline), con el `.env` | `http://127.0.0.1:8082` |
| Túnel ngrok hacia el motor (WhatsApp por QR en local) | la dirección que imprime al arrancar |
| API del panel (solo este equipo, sin cuentas) | `http://127.0.0.1:8010` |
| Panel | <http://localhost:5180> |

`./run_local_stop.sh` lo detiene todo.

La primera vez, en el panel local, **Importar negocios de ejemplo** trae los 9 negocios de ejemplo de
`project/config/tenants/` (ya publicados). Para probarlos con la IA real, cada uno necesita su clave en «Inteligencia
artificial».

Los secretos de este equipo (`.env`, clave de cifrado) se mueven entre Windows y macOS con `secrets.local.env`: ver
[operations.md](operations.md), «Trabajar Desde Windows Y macOS».

## Pruebas

```bash
pytest                                             # sin IA real ni base del .env
npm --prefix apps/admin-web test
npm --prefix apps/admin-web run test:integration
```

`pytest -m integration` usa la IA real y gasta: solo con `OPENROUTER_API_KEY` y cuando haga falta.

## Simulación

`POST /api/v1/simulate` está apagado por defecto (404). Para probar el asistente se usa «Probar asistente» en el panel.
