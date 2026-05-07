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
python -m venv .venv
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
OPENROUTER_API_KEY=
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
ENABLE_SIMULATION_ENDPOINT=true
ENABLE_WEBHOOK_PROCESSING=true
```

## Qué Hace Cada Grupo De Variables

### Base De Datos

- `DATABASE_URL`: conexión principal a la base de datos.

### Runtime AI

- `LLM_PROVIDER`: proveedor activo; hoy el runtime espera OpenRouter.
- `OPENROUTER_API_KEY`: credencial obligatoria para generación real.
- `OPENROUTER_BASE_URL`: endpoint base del proveedor.
- `OPENROUTER_MODEL`: modelo por defecto del runtime.
- `OPENROUTER_ADVANCED_MODEL`: modelo adicional para casos que lo requieran.
- `LLM_TIMEOUT_SECONDS`: timeout de request al modelo.

### Canal Meta WhatsApp

- `META_ACCESS_TOKEN`: token de envío hacia Meta.
- `META_PHONE_NUMBER_ID`: identificador del número activo.
- `META_VERIFY_TOKEN`: token de verificación del webhook.
- `META_APP_SECRET`: secreto de aplicación de Meta.

### Flags De Operación

- `ENABLE_AI_RESPONSES`: habilita respuesta por IA.
- `ENABLE_SIMULATION_ENDPOINT`: habilita `/api/v1/simulate`.
- `ENABLE_WEBHOOK_PROCESSING`: habilita `/api/v1/whatsapp/webhook`.

## Cómo Probar El Sistema

## Endpoint De Simulación

El endpoint de prueba controlada es:

- `POST /api/v1/simulate`

Requiere:

- header `X-Tenant-Slug`
- `Content-Type: application/json`
- payload con `user_message` y `user_id`

Estructura base:

```json
{"user_message":"tengo muchos mensajes","user_id":"ops-sim-1"}
```

## Secuencia De Prueba Recomendada

Para revisar el flujo comercial real, usar el mismo `user_id` y enviar esta secuencia:

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
- `OPENROUTER_API_KEY`
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

- `prompt_builder.py`
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

## Runbook Mínimo De Validación Antes De Cambios

Antes de cerrar un cambio relevante en runtime:

1. correr `pytest -q`
2. levantar `uvicorn app.main:app --reload`
3. probar `/health`
4. probar `/api/v1/simulate` con la secuencia comercial base
5. revisar que no aparezcan errores en consola

## Resumen Operativo

La operación actual del sistema es simple:

- entorno Python
- configuración por `.env`
- arranque con `uvicorn`
- validación por `/health` y `/simulate`
- debugging por consola y eventos estructurados

Eso es suficiente para desarrollo, QA y simulaciones controladas, y es la base correcta para endurecer la operación SaaS más adelante.