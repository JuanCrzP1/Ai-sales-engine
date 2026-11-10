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

Permite administrar los negocios sin editar YAML. Su API no usa las credenciales del `.env`: el área de pruebas carga el motor, pero responde solo con la clave de IA de cada negocio. Lo que publica es lo que responde el asistente: el motor no tiene otra fuente.

1. Desde la raíz del repositorio, ejecuta uno de los únicos lanzadores del sistema: `run_local.bat` en Windows o `./run_local.sh` en Linux y macOS. Encienden el motor con el `.env`, ngrok, Telegram y la API del panel en `127.0.0.1:8010`.
2. Cuando esa API responde, arrancan la interfaz y se abre <http://127.0.0.1:5180>. Si no responde, la interfaz no se abre y el motor sigue arrancando.
3. Para detener todo: `bash run_local_stop.sh`, desde Git Bash en Windows.

Los lanzadores abren también el túnel de `ngrok` y Telegram. Para administrar los negocios sin encender el motor ni exponer nada, basta con la API y la interfaz: ver `apps/admin-web/README.md`.

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
3. Arranca con `run_local.bat` o `./run_local.sh`. Sin abrir el túnel ni Telegram, basta con la API y la interfaz: ver `apps/admin-web/README.md`.
4. Comprueba que `GET /api/businesses/{slug}/review` responda `"compiles": true` en cada negocio. La respuesta no muestra la clave ni los datos.

| Situación | Qué ocurre |
|---|---|
| Falta la clave y la base tiene datos cifrados | La API no arranca, lo explica y no crea otra. La interfaz no se abre |
| La clave no es la que cifró esos datos | La API arranca, la revisión avisa que falta un dato de pago y guardar responde 503 con `payment_key` |
| No queda ninguna copia | Los valores cifrados no se pueden recuperar. Mientras existan los YAML (hasta la Fase 4), aparta el archivo de la base sin borrarlo y arranca: se crea una base nueva con otra clave, y "Importar negocios existentes" los trae de los YAML. Se pierde lo que se haya editado en el panel |

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
| `TELEGRAM_TOKEN`, `TELEGRAM_ADMIN_ID` | Canal de Telegram | Motor, si se usa Telegram |
| `META_VERIFY_TOKEN` | Webhook de WhatsApp | Motor, si se usa WhatsApp |
| Token de ngrok | Túnel público del motor | `run_local.*`. Lo guarda ngrok en cada equipo, no este archivo: `ngrok config add-authtoken <token>` |

`.env` trae además ajustes que no son secretos (`LLM_PROVIDER`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`, `OPENROUTER_ADVANCED_MODEL`, `TENANT_SLUG`), y viajan igual. El archivo de ejemplo, sin valores reales, es `secrets.local.env.example`.

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

**La autenticación definitiva está pendiente de la fase de infraestructura e integración en la nube.** El sistema propio actual (`AuthService`, `/auth/login`, `/auth/register` y las tablas `admin_users` y `tenants` del ORM) no se desarrollará ni se mantendrá como solución definitiva, y no debe considerarse listo para producción.

Hoy no funciona, y se deja así a propósito: usa `python-jose`, que no está en los requisitos, y sus modelos no coinciden con `project/docs/postgresql_schema.sql`. No se añaden dependencias ni se cambia el esquema para mantenerlo.

Qué depende de él y cómo responde hoy:

| Componente | Estado medido |
|---|---|
| `POST /api/v1/auth/register` | Registrado fuera de producción; en producción y en Vercel no se publica (ver «Nube: Vercel Y Neon»). Responde 500 y no emite token. Con las tablas del ORM guarda el negocio y el administrador antes de fallar; con las de `postgresql_schema.sql` no guarda nada |
| `POST /api/v1/auth/login` | Con las tablas del ORM: clave incorrecta 401, clave correcta 500. Con `postgresql_schema.sql`: siempre 500 |
| `/bot-config`, `/clients`, `/connectors`, `/conversations` y `/dashboard` (10 rutas) | Sin token 401; con cualquier token 500 |
| `/simulate` | Ver «Endpoint De Simulación» |

El panel `apps/admin-web` y su API local, `/health` y el webhook de WhatsApp no dependen de este sistema.

### `/auth/register` no está listo para producción

Quien alcance el servidor puede llamarlo. `uvicorn` escucha solo en `127.0.0.1` por defecto, pero `docker-compose.yml` publica el puerto 8000. Hoy no entrega acceso a nadie, porque no puede emitir tokens. Sus riesgos conocidos son:

- Con las tablas del ORM, cualquiera puede crear negocios y administradores en la base.
- No valida el identificador del negocio: admite textos como `../tenants/otro`.
- Responde 409 si el identificador o el correo ya existen, lo que permite comprobar si existen.
- **Si se instalara `python-jose`, empezaría a emitir tokens a cualquiera**, y con el secreto por defecto también se podrían falsificar. No la instales antes de integrar la autenticación definitiva.

### Antes De Desplegar

Pendiente de la fase de nube. Nada de esto está implementado:

1. Integrar la autenticación definitiva y conectar a ella las rutas de administración y `/simulate`.
2. Retirar `/auth/register` y `/auth/login`. Hecho a medias: en producción y en Vercel ya no se publican, junto con el resto de rutas
   de administración del sistema anterior (`ENABLE_LEGACY_ADMIN_API=1` las publica igual).
3. Retirar el secreto por defecto de `app/config/settings/base.py` y de `project/config/system/secrets.yaml`.
4. Resolver la incompatibilidad entre los modelos del ORM y `postgresql_schema.sql`, según lo que exija la solución elegida.
5. Si `/simulate` se va a habilitar: decidir si `reply` puede contener precios, añadir un límite de peticiones y volver a comprobar sus protecciones con la autenticación real.
6. ~~Sacar los datos de pago del prompt y de `conversation_trace`~~: hecho (ver `docs/business-config.md`, «Lo Que El Motor Usa Del Contrato»).
7. Incorporar la autenticación y la autorización multiusuario a la API del panel. Hoy no tiene ninguna y solo es segura porque atiende únicamente en este equipo: no se puede desplegar en la nube así.

## Nube: Vercel Y Neon

Vercel publica **el motor** (FastAPI, carpeta raíz `project`) como funciones de Python; Neon es su PostgreSQL. El panel todavía
no se publica: necesita la autenticación de la fase de nube.

Lo que el motor ya resuelve para correr ahí:

- No escribe en disco al arrancar (Vercel solo permite leer).
- Acepta la cadena de conexión de Neon tal como viene (`postgres://` o `postgresql://`): la pasa a psycopg 3, tanto para su base
  (`DATABASE_URL`) como para el almacén del panel (`BUSINESS_CONFIG_DATABASE_URL`).
- En producción (`MODE=production`) y en Vercel solo publica `/health` y el webhook de WhatsApp.

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

En `pruebas` copia las versiones, los datos de pago (ya cifrados: la clave no viaja) y los ajustes técnicos de cada negocio, y
comprueba que lo publicado compila igual que aquí. Se puede repetir: lo que ya está no se toca.

**2. Variables del proyecto en Vercel** (Settings → Environment Variables). Ya está `MODE=production` en Production y
Preview. Las secretas las escribe la persona dueña de las cuentas (nunca en el chat ni en el repositorio):

| Variable | Production | Preview |
|---|---|---|
| `DATABASE_URL` y `BUSINESS_CONFIG_DATABASE_URL` | Cadena de `production` con *pooling* | Cadena de `pruebas` con *pooling* |
| `BUSINESS_CONFIG_SECRETS_KEY` | Una clave propia de producción | La de este equipo (`secrets.local.env`) |

La IA no lleva variable: cada negocio guarda su clave de OpenRouter en el panel, y la plataforma no tiene clave propia.

**3. Volver a desplegar** y comprobar `/health`.

**4. El panel en la nube.** Es otro proyecto de Vercel, `ai-sales-engine-panel` (carpeta `apps/admin-web`, Vite), con
`VITE_NEON_AUTH_URL` = la dirección de Neon Auth de la rama `production` (Neon → la rama → Better Auth → Configure Auth →
*Auth URL*; es pública, no un secreto). Llama a la API por `/api`, que `apps/admin-web/vercel.json` reescribe hacia el motor
(`/panel/api`). El motor publica esa API solo si tiene `NEON_AUTH_URL` (la misma dirección) en sus variables.

- Cuentas: Neon Auth (Better Auth), con correo y contraseña; viven en `neon_auth.user` de la misma base. Cualquiera puede crear
  una cuenta: es una plataforma.
- Cada petición lleva el token de la sesión (JWT EdDSA de 15 minutos). La API lo comprueba con las claves públicas de Neon Auth
  y cada usuario solo llega a sus negocios (`business_members`, migración 0003); un negocio ajeno responde como inexistente.
- Al entrar, el panel abre directo el primer negocio del usuario (o la bienvenida para crearlo). El menú: Inicio, Conversaciones,
  Clientes, Ventas y Reportes; abajo, Asistente IA (pestañas de entrenamiento, Probar y Publicar), Canales y Ajustes.
- Conversaciones: cada hilo es un contacto en un canal y pertenece a un negocio (`conversations` y `conversation_entries`,
  migración 0004). Hoy llegan las de «Probar asistente», con el canal `prueba`; los canales reales escribirán en las mismas
  tablas. Los datos de pago se guardan ocultos.
- En la nube no se importan YAML ni se eliminan negocios. El dominio del panel debe estar en Neon Auth → Configure Auth →
  *Domains*.

Pendiente: Telegram necesita webhook (Vercel no mantiene procesos de *polling*) y el canal de WhatsApp necesita su configuración
por negocio. Mientras tanto, el bot sigue atendiendo desde `run_local`.

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
- datos YAML faltantes o inconsistentes
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
- contenido real del tenant en YAML
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
- runtime YAML
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

Ambos scripts leen la lista de tenants de las carpetas de `project/config/tenants/` y escriben en
la base que indique `DATABASE_URL` (variable de entorno o `.env` de la raíz). Se ejecutan desde la
raíz del repositorio:

```bash
python scripts/sync_tenants_to_db.py
python scripts/bootstrap_saas_data.py
```

### `sync_tenants_to_db.py`

Crea en la tabla `tenants` una fila (`name=slug`, `status='active'`) por cada carpeta de tenant
que todavía no exista. No modifica filas existentes y es idempotente. Informa `[created]`,
`[existing]` o `[error]` por tenant.

### `bootstrap_saas_data.py`

Garantiza por cada tenant una fila en `tenants`, `admin_users` (`name=slug`) y `tenant_settings`
(`settings='{}'`). No sobrescribe filas existentes, procesa cada tenant en su propia transacción y
termina con código 1 si algún tenant falla. No crea suscripciones, planes ni límites de uso: eso
lo administra la plataforma externa.

### Precauciones

- **Escriben en la base de datos.** Comprueba antes a qué base apunta `DATABASE_URL`; el `.env`
  local puede apuntar a una base compartida. No los ejecutes contra producción sin copia de seguridad.
- Requieren el esquema UUID de `project/docs/postgresql_schema.sql` (tablas `tenants`,
  `admin_users`, `tenant_settings`).
- Cada carpeta de `project/config/tenants/` se trata como un tenant, incluidos los de ejemplo.

## Resumen Operativo

La operación actual del sistema es simple:

- entorno Python
- configuración por `.env`
- arranque con `uvicorn`
- validación por `/health` y las pruebas de `tests/`
- debugging por consola y eventos estructurados

Eso es suficiente para desarrollo, QA y simulaciones controladas.