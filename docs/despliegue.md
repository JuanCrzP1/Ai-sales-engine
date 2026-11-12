# Desplegar AI Sales Engine

Qué necesita el proyecto para funcionar, en Vercel (como hoy) o en cualquier otro lugar: las piezas, los servicios externos y cada
variable, con dónde va. La plantilla con todas las variables es [`project/.env.example`](../project/.env.example); una prueba
(`tests/test_env_example.py`) falla si el código empieza a leer una variable que no está ahí.

## Las piezas

| Pieza | Qué es | Hoy | Si se mueve a otra parte, necesita |
|---|---|---|---|
| **Motor** | La API en Python (FastAPI): webhooks de WhatsApp, la IA, la API del panel (`/panel/api`) y la revisión de la atención humana | Vercel, proyecto `ai-sales-engine` (carpeta raíz `project`) | Python 3.11 o más; `pip install -r project/requirements.txt`; arrancar `uvicorn app.main:app` desde `project/`. Que las tareas en segundo plano terminen después de responder (en un servidor propio, siempre) |
| **Panel** | La aplicación web (React + Vite): archivos estáticos | Vercel, proyecto `ai-sales-engine-panel` (carpeta `apps/admin-web`) | `npm ci && npm run build` → servir `dist/`. Dos reglas: `/api/*` → `{motor}/panel/api/*`, y todo lo demás → `index.html`. Servir `sw.js` sin caché |
| **Base de datos** | PostgreSQL con las tablas del motor y del panel | Neon (rama `production`; `pruebas` para Preview) | Cualquier PostgreSQL. Las migraciones se aplican solas al arrancar la API del panel (`project/db/migrations`) |
| **Cuentas** | Inicio de sesión de los dueños de negocio | Neon Auth (Better Auth), de la misma base | Neon Auth u otro Better Auth compatible: el motor verifica sus tokens con sus claves públicas (`NEON_AUTH_URL`) |
| **Revisión periódica** | La IA retoma los chats que nadie atendió | Vercel Schedules cada 15 min (`project/vercel.json`) | Cualquier cron que llame `POST {motor}/api/v1/internal/attention/run` con `Authorization: Bearer <CRON_SECRET>` (cada 1 a 15 min) |

## Los servicios externos

| Servicio | Para qué | Quién lo paga | Obligatorio |
|---|---|---|---|
| [OpenRouter](https://openrouter.ai) | La IA de cada negocio | Cada negocio, con su propia clave (se guarda en el panel) | Sí, por negocio |
| [uazapi](https://uazapi.com) | WhatsApp por código QR | La plataforma (un servidor y su token de administrador) | Para WhatsApp |
| [Resend](https://resend.com) | Correos de aviso al equipo | La plataforma (gratis hasta 3.000 al mes) | No: sin él, los avisos llegan por la campana y las notificaciones |
| Neon | Base y cuentas | La plataforma | Sí (o PostgreSQL + Better Auth) |
| Vercel | Motor y panel | La plataforma (Hobby para probar; Pro para vender) | No: cualquier hosting con lo de la tabla de arriba |

Las notificaciones del celular (Web Push) no usan un servicio pago: el navegador las entrega, y las claves de la plataforma se crean
solas en la base.

## Las variables

### Motor, en producción

| Variable | Qué poner | Secreta | Obligatoria |
|---|---|---|---|
| `MODE` | `production` | No | Sí |
| `DATABASE_URL` | La cadena de PostgreSQL (con pooling en Neon) | Sí | Sí |
| `BUSINESS_CONFIG_DATABASE_URL` | La misma cadena | Sí | Sí |
| `BUSINESS_CONFIG_SECRETS_KEY` | Una clave Fernet propia (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`). **Guárdala aparte** (`secrets.production.env`): sin ella, los datos de pago y las claves de IA cifrados no se pueden leer | Sí | Sí |
| `NEON_AUTH_URL` | La dirección de Neon Auth (Neon → la rama → Better Auth → Auth URL). Sin ella, el motor no publica la API del panel | No | Sí |
| `UAZAPI_BASE_URL` | El servidor de uazapi de la plataforma | No | Para WhatsApp |
| `UAZAPI_ADMIN_TOKEN` | Su token de administrador | Sí | Para WhatsApp |
| `ENGINE_PUBLIC_URL` | La dirección pública del motor. En Vercel no hace falta (usa `VERCEL_PROJECT_PRODUCTION_URL`) | No | Fuera de Vercel, para WhatsApp |
| `RESEND_API_KEY` | La clave de Resend | Sí | Para los correos |
| `EMAIL_FROM` | El remitente, con el dominio verificado en Resend (`AI Sales Engine <avisos@tudominio.com>`). Sin él: `onboarding@resend.dev`, que solo entrega al correo de la cuenta de Resend | No | Para correos a cualquiera |
| `CRON_SECRET` | Un texto largo inventado (16 o más caracteres) | Sí | Para la revisión periódica |
| `PANEL_URL` | La dirección del panel, si no es `ai-sales-engine-panel.vercel.app` | No | Si el panel cambia de dirección |
| `LLM_PROVIDER`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL` | `openrouter`, `https://openrouter.ai/api/v1` y el modelo por defecto (`openai/gpt-4o-mini`) | No | Recomendadas |
| `MEDIA_AI_MODEL` | El modelo que entiende fotos y audios (por defecto `google/gemini-2.5-flash-lite`) | No | No |

### Panel

| Variable | Qué poner | Cuándo |
|---|---|---|
| `VITE_NEON_AUTH_URL` | La misma de `NEON_AUTH_URL` | Al compilar. Sin ella, el panel funciona como el de este equipo (sin cuentas) |

La dirección del motor no es una variable del panel: está en la regla `/api/*` de `apps/admin-web/vercel.json`. En otro hosting, esa
misma regla.

### Este equipo

Lo de la sección 1 de [`project/.env.example`](../project/.env.example), en `.env`. Los lanzadores (`./run_local.sh`,
`run_local.bat`) ponen solos `ENGINE_PUBLIC_URL` (ngrok), `PANEL_URL` y `ATTENTION_SWEEP_ON_TRAFFIC`. Los secretos viajan entre
equipos con `python scripts/local_secrets.py export` (ver [Operación](operations.md), «Trabajar Desde Windows Y macOS»).

## Dónde está cada valor real

| Archivo o lugar | Qué guarda | En GitHub |
|---|---|---|
| Vercel → cada proyecto → Environment Variables | Todos los valores de producción y Preview | No |
| `.env` (raíz) | Lo de este equipo | No (`.gitignore`) |
| `secrets.local.env` | La copia que lleva los secretos de este equipo a otro | No |
| `secrets.production.env` | Copia de respaldo de `BUSINESS_CONFIG_SECRETS_KEY` de producción | No |
| `project/.env.example`, `secrets.local.env.example` | Plantillas sin valores | Sí |

## Después de desplegar

1. `GET {motor}/health` responde `{"status": "ok"}` y `{motor}/` lleva al panel.
2. `POST {motor}/api/v1/internal/attention/run` sin clave responde **401** (con `CRON_SECRET` configurado; **503** si falta).
3. Entrar al panel, crear un negocio, poner su clave de IA y probarlo en «Probar».
4. Configuración → Atención humana: «Enviar correo de prueba» y «Activar notificaciones».
5. Canales: conectar WhatsApp con el QR y escribirle desde otro número.
