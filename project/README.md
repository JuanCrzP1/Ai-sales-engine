# AI Sales Engine Backend

Backend multi-tenant para ventas conversacionales por WhatsApp. Esta carpeta contiene la API operativa, el runtime AI-first y la carga de configuración por tenant que usa el sistema principal.

## Rol De Este Backend

Este backend no documenta una automatización genérica.
Documenta el motor conversacional y comercial que:

- recibe mensajes reales o simulados
- resuelve el tenant activo
- carga configuración de negocio por YAML
- ejecuta el flujo AI-first
- devuelve o envía una respuesta comercial contextual

## Ejecución Local

Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r project/requirements.txt
Copy-Item project/.env.example project/.env
Set-Location project
uvicorn app.main:app --reload
```

Superficie operativa principal:

- `GET /health`
- `GET /docs`
- `GET /api/v1/whatsapp/webhook`
- `POST /api/v1/whatsapp/webhook`

## Simulación Operativa

`POST /api/v1/simulate` está apagado por defecto y responde 404. No se puede usar hasta que exista la autenticación definitiva, pendiente de la fase de nube: ver `docs/operations.md`.

## Configuración Multi-Tenant

El comportamiento del sistema no se define en el código.
Se controla por tenant desde:

- `config/tenants/<tenant_slug>/business.yaml`
- `config/tenants/<tenant_slug>/config.yaml`
- `config/tenants/<tenant_slug>/inventory.yaml`
- `config/tenants/<tenant_slug>/pricing.yaml`
- `config/tenants/<tenant_slug>/sales.yaml`

Adicionalmente, el runtime usa configuración compartida desde:

- `config/system/`
- `config/core/`
- `config/channels/channels.yaml`
- `config/assets/media.yaml`

## Flujo Operativo

1. Entra un mensaje por webhook o simulación.
2. El backend resuelve el tenant con `X-Tenant-Slug` o datos del canal.
3. Se carga el runtime YAML efectivo del tenant.
4. Se combina memoria, contexto comercial y reglas activas.
5. El motor AI-first genera la respuesta.
6. La salida se valida y se devuelve al endpoint o al canal.

## Variables Clave

Las variables más relevantes del entorno son:

```env
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=HS256
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct
OPENROUTER_ADVANCED_MODEL=openai/gpt-4.1-mini
LLM_TIMEOUT_SECONDS=15
PUBLIC_BASE_URL=http://localhost:8000
ENABLE_MULTI_TENANT=true
SEMANTIC_THRESHOLD=0.22
CONVERSATION_CONTEXT_LIMIT=8
```

Reglas operativas:

- en desarrollo se puede usar fallback global desde `.env`
- en entornos reales, los secretos por tenant deben salir de almacenamiento seguro
- `config/secrets.yaml` no debe contener valores productivos versionados

## Testing

Ejecutar desde la raíz del repositorio:

```powershell
pytest -q
```

La suite protege:

- contratos del runtime
- aislamiento multi-tenant
- comportamiento comercial
- estructura de respuesta

## Scripts Útiles

Desde la raíz del repositorio (`scripts/`):

| Script | Para qué |
|---|---|
| `run_admin_api.py` | API local del panel, solo en `127.0.0.1:8010` |
| `init_local_business_config.py` | Crea el almacén de BusinessConfig; con `--import-tenants`, migración inicial desde los YAML |
| `local_secrets.py` | Instala y comprueba los secretos locales (`secrets.local.env`) sin mostrarlos |
| `export_business_config_schema.py`, `generate_business_config_types.py`, `migrate_tenants_to_contract.py`, `generate_traceability_matrix.py` | Regeneran lo derivado del contrato (ver `docs/business-config.md`) |
| `sync_tenants_to_db.py`, `bootstrap_saas_data.py` | Registran los negocios en la base del motor |
| `reset_conversation_state.py` | Borra la memoria conversacional en PostgreSQL |

## Documentación Complementaria

- `../README.md`
- `../docs/architecture.md`
- `../docs/operations.md`
- `../docs/tenants.md`
- `../config/README.md`
