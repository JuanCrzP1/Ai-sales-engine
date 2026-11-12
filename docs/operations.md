# Operación Del Sistema

## Propósito De Este Documento

Este documento explica cómo ejecutar, probar y depurar el sistema tal como existe hoy en el repositorio. Está orientado a operación local, validación del runtime y soporte técnico del entorno.

No reemplaza el README. El README posiciona el producto; este documento describe cómo operarlo.

## Cómo Levantar El Sistema

## 1. Preparar Entorno

Desde la raíz del repositorio:

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r project/requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r project/requirements.txt
```

## 2. Ejecutar El Servidor

El runtime activo corre desde `project/`:

```bash
cd project
uvicorn app.main:app --reload
```

Con esa ejecución, el sistema queda disponible localmente en:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Validación mínima esperada:

- `GET /health` responde `200`
- `GET /docs` expone la superficie HTTP activa

## Variables De Entorno

Las variables relevantes salen de `project/app/config/settings/base.py`.

Las más importantes para operación real son:

```env
DATABASE_URL=

LLM_PROVIDER=openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_ADVANCED_MODEL=openai/gpt-4.1-mini
LLM_TIMEOUT_SECONDS=15

PUBLIC_BASE_URL=http://localhost:8000

META_ACCESS_TOKEN=
META_PHONE_NUMBER_ID=
META_VERIFY_TOKEN=
META_APP_SECRET=
META_BUSINESS_ACCOUNT_ID=

ENABLE_AI_RESPONSES=true
ENABLE_SIMULATION_ENDPOINT=false
ENABLE_WEBHOOK_PROCESSING=true
```

## Qué Hace Cada Grupo De Variables

### Base De Datos

- `DATABASE_URL`: conexión principal a la base de datos.

### Autenticación

- `JWT_SECRET`: lo usa el sistema de autenticación actual, aplazado (ver «Autenticación»). `/simulate` no se registra sin un valor propio, porque el de por defecto está publicado en el repositorio. Si `CONNECTOR_SECRETS_KEY` está vacío, los conectores guardados se cifran con este valor: al cambiarlo dejan de poder leerse hasta definir `CONNECTOR_SECRETS_KEY` con el valor anterior.

### Runtime AI

- `LLM_PROVIDER`: proveedor activo; hoy el runtime espera OpenRouter.
- La clave de la IA no es una variable del motor: cada negocio guarda la suya en el panel (Inteligencia artificial) y el motor
  la usa en cada mensaje de ese negocio, con su modelo. La plataforma no tiene clave propia: un negocio sin clave no responde
  con IA y nunca usa la de otro. `OPENROUTER_API_KEY` en el `.env` solo la usan las pruebas en vivo (`pytest -m integration`).
- `OPENROUTER_BASE_URL`: endpoint base del proveedor.
- `OPENROUTER_MODEL`: modelo para los negocios que no eligen uno.
- `OPENROUTER_ADVANCED_MODEL`: modelo adicional para casos que lo requieran.
- `LLM_TIMEOUT_SECONDS`: timeout de request al modelo.

### Canal Meta WhatsApp

- `META_ACCESS_TOKEN`: token de envío hacia Meta.
- `META_PHONE_NUMBER_ID`: identificador del número activo.
- `META_VERIFY_TOKEN`: token de verificación del webhook.
- `META_APP_SECRET`: secreto de aplicación de Meta.

### WhatsApp Por Código QR (uazapi)

- `ENGINE_PUBLIC_URL`: la dirección pública del motor (sin `/api/v1`). Con ella, al conectar un negocio la API del panel registra
  en uazapi el webhook `{ENGINE_PUBLIC_URL}/api/v1/channels/whatsapp/{identificador secreto del negocio}`. En este equipo
  `./run_local.sh` la toma sola de ngrok; en Vercel no hace falta, porque se usa `VERCEL_PROJECT_PRODUCTION_URL`. Sin ella la
  conexión funciona, pero los mensajes no llegan al motor, y el panel lo avisa.
- `UAZAPI_BASE_URL` y `UAZAPI_ADMIN_TOKEN`: el servidor de uazapi **de la plataforma** y su token de administrador (en Vercel,
  *Sensitive*). El negocio nunca los ve: en Canales solo toca «Conectar WhatsApp» y escanea el QR. Con el token de administrador
  se crea una instancia por negocio, cuyo token queda cifrado con `BUSINESS_CONFIG_SECRETS_KEY` (tabla `business_channels`,
  migración 0008). Desconectar borra la instancia del servidor. Sin estas variables (o sin dirección pública del motor), Canales
  dice que la conexión todavía no está activa.
- El webhook solo acepta avisos con el token de la instancia guardada e ignora grupos, canales y lo que envía la API. Lo que el
  negocio escribe desde su celular en el chat de un cliente sí llega: queda como respuesta del equipo y pausa la IA en ese chat. Las
  instancias conectadas antes del 11 de noviembre de 2026 lo reciben después de volver a conectar (así se registra el webhook nuevo). Recibe mensajes, recibos de entregado y leído (`messages_update`) y cambios de conexión. El flujo completo está en
  `app/application/channels/whatsapp_inbound.py`:
  1. El mensaje del cliente se guarda en la bandeja apenas llega. El mismo aviso repetido no se guarda ni se responde dos veces (lo
     garantiza un índice único en la base).
  2. Mientras el asistente responde, la bandeja y el WhatsApp del cliente dicen «escribiendo…».
  3. Las fotos, audios y documentos se descargan y se guardan (`conversation_media`, hasta 4 MB), porque el enlace de WhatsApp vence.
     La IA describe la foto (y si es un comprobante de pago) o transcribe la nota de voz con la clave del negocio y un modelo económico
     (`MEDIA_AI_MODEL`, por omisión `google/gemini-2.5-flash-lite`); eso es lo que lee el asistente, y su costo va al consumo del
     negocio.
  4. Si el cliente pide una persona, reclama o reporta un pago, la conversación pasa al equipo según su horario (ver «Atención
     Humana» abajo). Si alguien del equipo toma el chat mientras el asistente piensa, no se envía nada.
  5. Desde la bandeja, el equipo responde (sale por WhatsApp y pausa la IA) y reanuda la IA cuando quiera.
- Los contactos que WhatsApp identifica con `@lid` se atienden en su número (`sender_pn`).
- El servidor gratuito (`https://free.uazapi.com`) sirve para probar: borra las instancias a la hora (conectar de nuevo crea
  otra). Para clientes reales se usa un servidor de pago de uazapi.

### Atención Humana: Correo, Notificaciones Y Revisión Periódica

Lo que hace cada negocio está en Configuración → Atención humana (ver `docs/architecture.md`, «Atención Humana»). La plataforma pone:

| Variable (proyecto del motor) | Para qué | Si falta |
|---|---|---|
| `RESEND_API_KEY` (*Sensitive*) | La clave de [Resend](https://resend.com) para los correos de aviso | No salen correos; el panel dice «El correo de avisos aún no está activado en la plataforma». Todo lo demás funciona |
| `EMAIL_FROM` | El remitente, p. ej. `AI Sales Engine <avisos@tudominio.com>`, con el dominio verificado en Resend | Se usa `onboarding@resend.dev`, el de pruebas de Resend, que **solo entrega al correo de la cuenta de Resend** |
| `CRON_SECRET` (*Sensitive*, 16 caracteres o más) | Protege `/api/v1/internal/attention/run`, que Vercel llama cada 15 minutos (`project/vercel.json`) | La ruta responde 503 y la IA retoma los chats solo con el tráfico del motor y del panel |
| `PANEL_URL` | La dirección del panel para los enlaces de los correos y la raíz del motor | `https://ai-sales-engine-panel.vercel.app` |

- **Notificaciones (Web Push):** no llevan variables. Las claves VAPID se crean solas la primera vez (tabla `platform_keys`, la parte
  secreta cifrada con `BUSINESS_CONFIG_SECRETS_KEY`). Cada persona las activa en cada navegador desde Configuración → Atención humana o la
  campana. En iPhone y iPad solo funcionan con el panel instalado («Agregar a pantalla de inicio»).
- **Puntualidad:** en el plan Hobby, Vercel corre la revisión cada 15 minutos, así que una espera de 30 minutos se retoma entre los
  30 y los 45 minutos si nadie usa la plataforma; con tráfico (el panel abierto o mensajes entrantes), al minuto. En Pro se puede
  cada minuto (`* * * * *` en `project/vercel.json`).
- **En este equipo:** los lanzadores ponen `ATTENTION_SWEEP_ON_TRAFFIC=1`, así la revisión corre con el tráfico local.
- **Registros útiles:** `whatsapp_qr_paso_a_una_persona` (con `team_available` y `ai_paused`), `aviso_por_correo_enviado`,
  `aviso_por_correo_fallido`, `aviso_por_notificacion` (cuántos dispositivos), `ia_retomo_chat`, `revision_de_atencion_fallida`.
  Cómo salió cada aviso queda en `notification_deliveries` (`sent`, `failed` con su motivo o `skipped`).

### Flags De Operación

- `ENABLE_AI_RESPONSES`: habilita respuesta por IA.
- `ENABLE_SIMULATION_ENDPOINT`: registra `/api/v1/simulate`. Está en `false` por defecto y solo tiene efecto junto con un `JWT_SECRET` propio. Déjala en `false`: la ruta no se puede usar hasta que exista la autenticación definitiva.
- `ENABLE_WEBHOOK_PROCESSING`: habilita `/api/v1/whatsapp/webhook`.

## Cómo Probar El Sistema

## Endpoint De Simulación

`POST /api/v1/simulate` es una ruta de prueba controlada. Está apagada por defecto y **hoy no se puede usar de extremo a extremo**: exige un token de administrador, y ningún entorno puede emitirlo ni verificarlo hasta que exista la autenticación definitiva (ver «Autenticación»).

Estado actual, comprobado con la aplicación real:

| Situación | Respuesta |
|---|---|
| Por defecto, o sin `ENABLE_SIMULATION_ENDPOINT=true` y un `JWT_SECRET` propio | 404: la ruta no se registra y no aparece en `/docs` |
| Habilitada, sin token | 401 |
| Habilitada, con cualquier token | 500: no se puede verificar y la petición no llega al motor |

Cambiar la configuración exige reiniciar el proceso.

Protecciones implementadas, comprobadas en `tests/test_simulation_endpoint_security.py`. Como hoy no hay tokens, esas pruebas simulan únicamente su verificación:

- **Acceso.** Usa `get_current_user` y `get_current_tenant`: un token de otro negocio responde 403 y `X-Tenant-Slug` no basta. Solo se acepta como negocio un nombre simple de carpeta.
- **Memoria aislada.** `user_id` es la etiqueta de una conversación simulada del administrador que llama. Vive en la RAM del proceso, separada por administrador (hasta 200 sesiones; se pierde al reiniciar), y no lee ni escribe la memoria de los clientes.
- **Respuesta cerrada.** Solo devuelve `reply`, `ai_used` y `metadata` con `source`, `intent`, `conversation_state` y `tenant_slug`.
- **Sin datos de pago.** El modelo recibe la configuración con esos valores sustituidos y `reply` los muestra como `[dato de pago]`.
- **Configuración fija.** La petición solo admite `user_message`, `user_id` y `faq_results`; cualquier otro campo, como `yaml_config`, responde 422.

Límite conocido: `reply` es texto del modelo, igual que el que recibe un cliente. Puede mencionar precios y, ante un mensaje malicioso, repetir parte de sus instrucciones. Ningún otro campo lleva esa información.

## Panel De Administración Local

Permite administrar los negocios en este equipo, sin cuentas. Su API no usa las credenciales del `.env`: el área de pruebas carga el motor, pero responde solo con la clave de IA de cada negocio. Lo que publica es lo que responde el asistente: el motor no tiene otra fuente.

1. Desde la raíz del repositorio, ejecuta uno de los únicos lanzadores del sistema: `run_local.bat` en Windows o `./run_local.sh` en Linux y macOS. Encienden el motor con el `.env`, ngrok y la API del panel en `127.0.0.1:8010`.
2. Cuando esa API responde, arrancan la interfaz y se abre <http://127.0.0.1:5180>. Si no responde, la interfaz no se abre y el motor sigue arrancando.
3. Para detener todo: `bash run_local_stop.sh`, desde Git Bash en Windows.

Los lanzadores abren también el túnel de `ngrok`. Para administrar los negocios sin encender el motor ni exponer nada, basta con la API y la interfaz: ver `apps/admin-web/README.md`.

La primera vez se crean la base `project/data/business_config.sqlite3` y la clave que cifra los datos de pago, `.ai-sales-engine/business_config_secrets.key` en la carpeta del usuario, fuera del repositorio. La clave se reutiliza siempre: guarda una copia, porque sin ella esos datos no se pueden leer. Tienen prioridad `BUSINESS_CONFIG_SECRETS_KEY`, si está definida, y después `secrets.local.env`, el archivo para trabajar desde varios equipos. Si la clave falta y la base ya tiene datos cifrados, o si hay dos claves distintas, la API no arranca, en vez de crear otra o elegir una que dejaría esos datos ilegibles.

La API del panel **no tiene autenticación**. Por eso su host está fijo a `127.0.0.1`, sin opción para cambiarlo, y rechaza clientes, `Host` y `Origin` ajenos. No la publiques en otra red ni detrás de un túnel como `ngrok`. Detalle de la API: `docs/business-config.md`.

### Respaldo Y Recuperación De La Clave De Cifrado

La clave está en `%USERPROFILE%\.ai-sales-engine\business_config_secrets.key` (`~/.ai-sales-engine/business_config_secrets.key` en Linux y macOS). Es lo único que permite leer los datos de pago guardados. No va en un archivo versionado, en `.env`, ni en un correo o un chat sin cifrar. También viaja, ignorada por git, en `secrets.local.env`: ver «Trabajar Desde Windows Y macOS».

**Respaldar.** Guarda una copia fuera de este equipo, en un lugar protegido: una memoria USB cifrada (por ejemplo, con BitLocker To Go) o un gestor de contraseñas que admita adjuntar archivos. Con la memoria conectada, ejecuta esto en PowerShell, cambiando `E:` por su letra. No abre ni muestra la clave, no toca el original y la última línea imprime `True` si la copia es idéntica:

```powershell
$clave = "$env:USERPROFILE\.ai-sales-engine\business_config_secrets.key"
$copia = "E:\respaldo-ai-sales-engine\business_config_secrets.key"
New-Item -ItemType Directory -Force -Path (Split-Path $copia) | Out-Null
Copy-Item $clave $copia
(Get-FileHash $clave).Hash -eq (Get-FileHash $copia).Hash
```

Después retira la memoria y guárdala lejos del equipo. Con un gestor de contraseñas, adjunta el archivo `business_config_secrets.key`; para comprobarlo, descarga el adjunto a una carpeta temporal, compáralo con la última línea y borra esa descarga. En Linux y macOS, usa `cp` y `cmp`. No abras la clave en un editor ni la copies al repositorio, a una carpeta sincronizada sin cifrar o a un chat. Basta con una copia: la clave no cambia sola.

**Recuperar.**

1. Detén el sistema: `bash run_local_stop.sh`.
2. Devuelve la copia, sin editarla, a la ruta de arriba. También puedes definir su contenido en `BUSINESS_CONFIG_SECRETS_KEY`, solo para esa sesión; esa variable tiene prioridad y no crea ningún archivo.
3. Arranca con `run_local.bat` o `./run_local.sh`. Sin abrir el túnel, basta con la API y la interfaz: ver `apps/admin-web/README.md`.
4. Comprueba que `GET /api/businesses/{slug}/review` responda `"compiles": true` en cada negocio. La respuesta no muestra la clave ni los datos.

| Situación | Qué ocurre |
|---|---|
| Falta la clave y la base tiene datos cifrados | La API no arranca, lo explica y no crea otra. La interfaz no se abre |
| La clave no es la que cifró esos datos | La API arranca, la revisión avisa que falta un dato de pago y guardar responde 503 con `payment_key` |
| No queda ninguna copia | Los valores cifrados no se pueden recuperar. Aparta el archivo de la base sin borrarlo y arranca: se crea una base nueva con otra clave, y «Importar negocios de ejemplo» trae de nuevo los ejemplos. Se pierde lo que se haya editado en el panel de este equipo |

### Trabajar Desde Windows Y macOS

El código viaja por git. Lo demás se queda fuera de git a propósito y tiene su propio camino:

| Qué | Dónde está | Cómo llega al otro equipo |
|---|---|---|
| Clave de cifrado y variables del `.env` | `secrets.local.env`, en la raíz del repositorio | Copia protegida (ver «Trasladar») |
| Negocios, versiones y datos de pago cifrados | `project/data/business_config.sqlite3` | Copia, con el sistema apagado |
| `.venv` y `node_modules` | Cada equipo | No se copian: se instalan, porque dependen del sistema operativo |
| Memoria del motor | PostgreSQL de cada equipo | No viaja con este procedimiento |

Las rutas salen de la ubicación del repositorio y de la carpeta del usuario de cada sistema, y la base no guarda rutas: el mismo archivo SQLite sirve en los dos equipos. `secrets.local.env` no depende de la carpeta del usuario; `AI_SALES_ENGINE_SECRETS_FILE` permite guardarlo en otra ubicación.

**Secretos que usa el proyecto.** El panel solo necesita la primera fila:

| Secreto | Para qué | Cuándo hace falta |
|---|---|---|
| `BUSINESS_CONFIG_SECRETS_KEY` | Cifra los datos de pago. El motor la usa para leerlos de lo publicado en el panel (ver `docs/business-config.md`, «Conexión Con El Motor») | Siempre que la base tenga datos. Debe ser la misma en los dos equipos y en el motor |
| `OPENROUTER_API_KEY` | Pruebas en vivo (`pytest -m integration`) | Solo para esas pruebas. El motor no la usa: cada negocio guarda su clave en el panel |
| `DATABASE_URL` | PostgreSQL del motor | Motor. Si apunta al propio equipo, el otro necesita su PostgreSQL |
| `META_VERIFY_TOKEN` | Webhook de WhatsApp | Motor, si se usa WhatsApp |
| Token de ngrok | Túnel público del motor | `run_local.*`. Lo guarda ngrok en cada equipo, no este archivo: `ngrok config add-authtoken <token>` |

`.env` trae además ajustes que no son secretos (`LLM_PROVIDER`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`, `OPENROUTER_ADVANCED_MODEL`), y viajan igual. El archivo de ejemplo, sin valores reales, es `secrets.local.env.example`.

**Crear el archivo, en el equipo que ya tiene los datos.** Reúne la clave actual, sin cambiarla, y las variables del `.env`; nunca imprime valores ni genera una clave. Si cambias el `.env`, repítelo.

```bash
python scripts/local_secrets.py export
```

**Preparar el otro equipo.** Necesita el trabajo ya subido con `git push`. Si todavía no quieres publicarlo, después de tu commit local crea un paquete con `git bundle create ai-sales-engine.bundle HEAD main`, cópialo con `scp` y clónalo en el otro equipo con `git clone ai-sales-engine.bundle`, en lugar de la URL de GitHub. En macOS, con [Homebrew](https://brew.sh) instalado:

```bash
brew install python@3.13 node git
git clone https://github.com/JuanCrzP1/Ai-sales-engine.git ~/dev/ai-sales-engine
cd ~/dev/ai-sales-engine
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
npm --prefix apps/admin-web ci
mkdir -p project/data
```

En Windows, con Python 3.13, Node y Git instalados, desde PowerShell:

```powershell
git clone https://github.com/JuanCrzP1/Ai-sales-engine.git C:\dev\ai-sales-engine
cd C:\dev\ai-sales-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r project/requirements.txt
npm --prefix apps/admin-web ci
New-Item -ItemType Directory -Force project\data | Out-Null
```

**Trasladar.** Se recomienda `scp`: cifra la copia de punta a punta, no la deja en servicios de terceros y viene incluido en Windows y macOS. En el Mac, activa Ajustes del Sistema > General > Compartir > Inicio de sesión remoto, y apágalo al terminar. Con los dos equipos en la misma red y el sistema apagado (`bash run_local_stop.sh`), ejecuta esto en Windows desde la raíz del repositorio, cambiando `usuario` y el nombre del Mac (o usando su dirección IP):

```powershell
scp secrets.local.env usuario@nombre-del-mac.local:~/dev/ai-sales-engine/
scp project/data/business_config.sqlite3 usuario@nombre-del-mac.local:~/dev/ai-sales-engine/project/data/
```

También sirve una memoria USB cifrada o un gestor de contraseñas que admita archivos adjuntos. Nunca por correo, por chat, por GitHub ni por una carpeta sincronizada sin cifrar.

**Instalar y comprobar, en el equipo que lo recibe.** Con `.venv` activo, `install` deja el archivo legible solo por tu usuario y crea `.env` si falta; nunca sobrescribe uno existente. `check` termina con error si algo no cuadra:

```bash
python scripts/local_secrets.py install
python scripts/local_secrets.py check
```

Debe indicar que git ignora el archivo y que todos los datos de pago se descifran; hoy, `46 de 46`. No muestra ningún valor.

**Ejecutar.** El panel solo necesita esto, igual en los dos sistemas, con `.venv` activo y cada orden en su consola:

```bash
python scripts/run_admin_api.py
npm --prefix apps/admin-web run panel
```

Se abre en <http://127.0.0.1:5180> y se detiene con `bash run_local_stop.sh` (desde Git Bash en Windows). El sistema completo se arranca con `./run_local.sh` en macOS o `run_local.bat` en Windows. En macOS requiere además `brew install ngrok`, su token y el PostgreSQL de `DATABASE_URL`: `docker compose up -d db` levanta una base vacía con las credenciales de `docker-compose.yml`, y los datos del PostgreSQL del otro equipo no se copian.

**Cambiar de equipo.** Cada equipo tiene su propio archivo SQLite y nada los sincroniza: la última copia reemplaza a la otra. Edita en un solo equipo a la vez y, antes de cambiar, apaga el sistema y copia la base. Para traerla del Mac a Windows, también desde Windows:

```powershell
scp usuario@nombre-del-mac.local:~/dev/ai-sales-engine/project/data/business_config.sqlite3 project/data/
```

**Recuperar.**

| Situación | Qué hacer |
|---|---|
| Se perdió `secrets.local.env` en un equipo | Cópialo del otro, o repite `export` donde exista la clave |
| Se perdió `.env` | `install` lo crea desde `secrets.local.env` |
| Se perdió la clave de la carpeta del usuario | No hace falta restaurarla si está `secrets.local.env` |
| La API dice que hay dos claves distintas | `check` indica cuál descifra los datos. Conserva esa; la API no elige por ti |

## Autenticación

Las cuentas son de **Neon Auth** (correo y contraseña) y solo las usa el panel en la nube: cada petición lleva el JWT de la sesión y
cada usuario llega solo a sus negocios (`business_members`). Ver «Nube: Vercel Y Neon».

La API del panel en este equipo no tiene cuentas: solo atiende en `127.0.0.1` (ver «Panel De Administración Local»).

Lo que queda del sistema de cuentas anterior (`AuthService`, la tabla `admin_users` y los modelos de `app/models`) solo lo usa
`/simulate`, que está apagado. Sus rutas (`/auth/register`, `/auth/login`, `/bot-config`, `/clients`, `/connectors`,
`/conversations` y `/dashboard`) se retiraron el 11 de noviembre de 2026: ya no existen en ningún entorno. `python-jose` sigue sin
declararse en los requisitos, a propósito (una prueba lo vigila).

### Pendiente

1. Retirar el resto del sistema anterior: `AuthService`, `app/models` con ids enteros y las tablas `admin_users`,
   `tenant_secrets`, `tenant_settings` y `tenant_channels` (Fase 6 de `docs/plan-v1.md`; borrar tablas de Neon necesita la
   aprobación de la persona dueña).
2. Retirar el secreto por defecto (`jwt_secret`) de `app/config/settings/base.py` y de `project/config/system/secrets.yaml` junto con
   ese sistema.
3. Si `/simulate` se va a habilitar: pasarlo a las cuentas de Neon Auth, decidir si `reply` puede contener precios y añadir un
   límite de peticiones. Mientras tanto, «Probar asistente» del panel cubre ese uso.

## Nube: Vercel Y Neon

Vercel publica **el motor** (FastAPI, carpeta raíz `project`) como funciones de Python, y **el panel** como otro proyecto (ver el
paso 4); Neon es su PostgreSQL y sus cuentas (Neon Auth).

Lo que el motor ya resuelve para correr ahí:

- No escribe en disco al arrancar (Vercel solo permite leer).
- Acepta la cadena de conexión de Neon tal como viene (`postgres://` o `postgresql://`): la pasa a psycopg 3, tanto para su base
  (`DATABASE_URL`) como para el almacén del panel (`BUSINESS_CONFIG_DATABASE_URL`).
- En producción (`MODE=production`) y en Vercel solo publica `/health`, el webhook de WhatsApp de Meta y el de WhatsApp por código
  QR (`/api/v1/channels/whatsapp/{identificador}`).

Una sola base de Neon guarda las tablas del motor y el almacén del panel: sus tablas apuntan a `tenants`. Tiene dos ramas:

| Rama de Neon | Entorno de Vercel | Para qué |
|---|---|---|
| `production` | Production | Clientes reales: solo los negocios que crean las cuentas reales |
| `pruebas` | Preview | Todas las pruebas, con los negocios de ejemplo de este equipo |

**1. Preparar cada rama desde este equipo.** Pega la cadena de conexión de cada rama (Neon → la rama → Connect) en el `.env`
de la raíz, como `CLOUD_DATABASE_URL_PRODUCTION` y `CLOUD_DATABASE_URL_PRUEBAS`, y ejecuta:

```bash
python scripts/setup_cloud_database.py --branch pruebas            # informa qué falta, sin escribir
python scripts/setup_cloud_database.py --branch pruebas --apply    # tablas, negocios de ejemplo y comprobación
python scripts/setup_cloud_database.py --branch production --apply # solo las tablas
```

Las migraciones nuevas se aplican solas, como en Auream: después de cada despliegue, la API del panel en la nube aplica al
arrancar las de `project/db/migrations` que su base no tenga anotadas en `schema_migrations`, en orden, cada una en su transacción
(con su anotación) y con un candado para que dos arranques a la vez no choquen (`app/infrastructure/business_config/migrations.py`).
Toda migración debe poder repetirse: `IF NOT EXISTS` en tablas, índices y columnas, y cada restricción se quita antes de crearla (una
prueba lo exige). Si una falla, queda en los registros de Vercel
(`migraciones_fallaron`) y la API sigue con lo que ya había. El comando de arriba hace lo mismo desde este equipo.

En `pruebas` copia las versiones, los datos de pago (ya cifrados: la clave no viaja) y los ajustes técnicos de cada negocio, y
comprueba que lo publicado compila igual que aquí. Se puede repetir: lo que ya está no se toca.

**2. Variables del proyecto en Vercel** (Settings → Environment Variables). Ya está `MODE=production` en Production y
Preview. Las secretas las escribe la persona dueña de las cuentas (nunca en el chat ni en el repositorio):

| Variable | Production | Preview |
|---|---|---|
| `DATABASE_URL` y `BUSINESS_CONFIG_DATABASE_URL` | Cadena de `production` con *pooling* | Cadena de `pruebas` con *pooling* |
| `BUSINESS_CONFIG_SECRETS_KEY` | Una clave propia de producción | La de este equipo (`secrets.local.env`) |
| `UAZAPI_BASE_URL` y `UAZAPI_ADMIN_TOKEN` | El servidor de uazapi de la plataforma y su token de administrador (*Sensitive*) | Los mismos, u otro servidor de pruebas |

La IA no lleva variable: cada negocio guarda su clave de OpenRouter en el panel, y la plataforma no tiene clave propia.

**3. Volver a desplegar** y comprobar `/health`.

**4. El panel en la nube.** Es otro proyecto de Vercel, `ai-sales-engine-panel` (carpeta `apps/admin-web`, Vite), con
`VITE_NEON_AUTH_URL` = la dirección de Neon Auth de la rama `production` (Neon → la rama → Better Auth → Configure Auth →
*Auth URL*; es pública, no un secreto). Llama a la API por `/api`, que `apps/admin-web/vercel.json` reescribe hacia el motor
(`/panel/api`). El motor publica esa API solo si tiene `NEON_AUTH_URL` (la misma dirección) en sus variables.

Quien abre la dirección del motor (`ai-sales-engine-mocha.vercel.app`, por ejemplo desde Vercel) llega al panel: el motor no
tiene pantallas y su raíz redirige a `PANEL_URL`, o al panel publicado si no está. En este equipo los lanzadores ponen
`PANEL_URL` en el panel local. El enlace de GitHub («About») también apunta al panel.

- Cuentas: Neon Auth (Better Auth), con correo y contraseña; viven en `neon_auth.user` de la misma base. Cualquiera puede crear
  una cuenta: es una plataforma.
- Cada petición lleva el token de la sesión (JWT EdDSA de 15 minutos). La API lo comprueba con las claves públicas de Neon Auth
  y cada usuario solo llega a sus negocios (`business_members`, migración 0003); un negocio ajeno responde como inexistente.
- Al crear un negocio se elige cómo empezar: de cero (la primera opción) o con una plantilla de `project/config/business-templates/`
  (restaurante, tienda, agencia de viajes, escuela, servicios con cita, software). La plantilla trae productos, precios, textos y
  estrategia de ejemplo, nunca datos de pago, dirección ni testimonios, y queda en borrador hasta que el negocio la revise y publique.
- Al entrar, el panel abre directo el primer negocio del usuario (o la bienvenida para crearlo). El menú: Inicio, Conversaciones,
  Clientes, Ventas y Reportes; abajo, Asistente IA (un resumen con una tarjeta por sección y su estado; las pestañas de
  entrenamiento, organizadas en tarjetas: lo esencial primero y las opciones avanzadas plegadas; Probar y Publicar), Canales y Configuración.
- Conversaciones: cada hilo es un contacto en un canal y pertenece a un negocio (`conversations` y `conversation_entries`,
  migraciones 0004 y 0009). Llegan las de WhatsApp por QR, en vivo, y las de «Probar asistente» (canal `prueba`, que no cuenta en
  Clientes ni en Reportes). Los datos de pago se guardan ocultos.
- Clientes, Ventas y Reportes (migración 0010): la etapa de cada cliente avanza sola con lo que reconoce el asistente; las ventas
  se registran desde el panel y los reportes cuentan por día en la hora de Colombia.
- Canales: WhatsApp por código QR con uazapi. El negocio toca «Conectar WhatsApp» y escanea el QR; el servidor, los tokens y el
  webhook los pone la plataforma. La API oficial de Meta, Telegram y el chat web aparecen como «Próximamente».
- En la nube no se importan los negocios de ejemplo ni se eliminan negocios. El dominio del panel debe estar en Neon Auth →
  Configure Auth → *Domains*.

Pendiente: Telegram por negocio (con webhook: Vercel no mantiene procesos de *polling*) y la API oficial de Meta por negocio. El
*polling* de Telegram que corría `run_local`, para un solo negocio fijo, se retiró el 11 de noviembre de 2026.

## Secuencia De Prueba Recomendada

Para revisar el flujo comercial, enviar esta secuencia dentro de una misma conversación. Mientras `/simulate` no se pueda usar, se prueba con `tests/pipeline_harness.py`, que ejecuta el pipeline real con un modelo simulado:

1. `tengo muchos mensajes`
2. `como funciona`
3. `esta caro`
4. `quiero empezar`

Qué valida esa secuencia:

- dolor operativo
- explicación del servicio
- objeción de precio
- intención de avance o cierre

## Cómo Probar El Webhook

El webhook real está en:

- `GET /api/v1/whatsapp/webhook`
- `POST /api/v1/whatsapp/webhook`

Uso operativo:

- `GET` valida el token de verificación de Meta
- `POST` recibe el evento real del canal

Para operación local, el webhook requiere exponer el backend y tener la configuración correspondiente en Meta.

## Cómo Debuggear

## 1. Ver La Consola Del Servidor

La fuente principal de diagnóstico actual es stdout/stderr del proceso `uvicorn`.

El logger activo en `project/app/utils/logger.py` escribe a consola por defecto. Solo escribe a archivo si `ENABLE_FILE_LOGS=1`.

## 2. Eventos Útiles Que Ya Emite El Runtime

Durante operación y debugging, conviene observar eventos como:

- `env_check`
- `prompt_runtime_check`
- `runtime_tenant_profile`
- `tenant_resolved`
- `runtime_yaml_valid`
- `orchestrator_parser_audit`
- `tokens_usage`
- `ai_route_result`

Esos eventos ayudan a detectar:

- tenant incorrecto
- configuración publicada faltante o inconsistente
- salida del modelo mal parseada
- request al LLM sin credenciales
- fallback por excepción

## 3. Qué Revisar Si El Sistema No Responde Como Esperas

### Si no responde nada

Revisar:

- `/health`
- que el negocio tenga su clave de IA (panel → Inteligencia artificial)
- flags `ENABLE_AI_RESPONSES`, `ENABLE_SIMULATION_ENDPOINT`, `ENABLE_WEBHOOK_PROCESSING`
- que el tenant exista y esté activo

### Si responde genérico

Revisar:

- `runtime_yaml_valid`
- lo publicado del negocio (panel → Revisión y publicación)
- `memory_context`
- `orchestrator_parser_audit`

### Si responde fuera de contexto

Revisar:

- `prompting/composer.py` y `prompting/sections/` (el bloque que corresponda)
- `prompt_context.py`
- `structured_output.py`
- `response_guard.py`

### Si falla el canal

Revisar:

- `META_ACCESS_TOKEN`
- `META_PHONE_NUMBER_ID`
- sender activo en `project/app/connectors/whatsapp/meta/sender.py`

## Cómo Validar Respuestas

Al validar respuestas no basta con mirar si “respondió”. Hay que revisar cuatro cosas:

1. grounded: usa información real del tenant
2. natural: suena a chat y no a plantilla técnica
3. útil: responde exactamente al mensaje del turno
4. comercial: empuja el siguiente paso cuando corresponde

## Cómo Ejecutar Tests

La suite canónica está en `tests/`.

Validación principal:

- `pytest -q`

La suite cubre:

- comportamiento comercial
- estructura de respuesta
- el runtime del negocio (su versión publicada, compilada)
- continuidad conversacional
- aislamiento multi-tenant
- API del panel de administración

Panel de administración, desde `apps/admin-web`:

- `npm run typecheck` y `npm test`
- `npm run test:integration`: interfaz, API, contrato y SQLite reales, sobre una base temporal y sin servicios externos

## Runbook Mínimo De Validación Antes De Cambios

Antes de cerrar un cambio relevante en runtime:

1. correr `pytest -q`
2. levantar `uvicorn app.main:app --reload`
3. probar `/health`
4. comprobar que `/api/v1/simulate` responde 404, porque está apagado por defecto
5. revisar que no aparezcan errores en consola

## Scripts De Base De Datos

`scripts/setup_cloud_database.py` deja lista una rama de Neon (ver «Nube: Vercel Y Neon»). En la rama `pruebas` usa
`scripts/bootstrap_saas_data.py`, que garantiza por cada negocio de ejemplo (`project/config/tenants/`) una fila en `tenants`,
`admin_users` y `tenant_settings` (tablas del sistema anterior, que se retiran en la Fase 6). No sobrescribe filas existentes y
procesa cada negocio en su propia transacción.

### Precauciones

- **Escriben en la base de datos.** Comprueba antes a qué base apunta cada variable; nunca contra `production` sin copia de
  seguridad.
- Requieren el esquema UUID de `project/docs/postgresql_schema.sql`.

## Resumen Operativo

La operación actual del sistema es simple:

- entorno Python
- configuración por `.env`
- arranque con `uvicorn`
- validación por `/health` y las pruebas de `tests/`
- debugging por consola y eventos estructurados

Eso es suficiente para desarrollo, QA y simulaciones controladas.