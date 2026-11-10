# Contributing

## Objetivo

Este repositorio prioriza estabilidad operativa, configuración explícita y pruebas que validan comportamiento real del sistema de ventas. Si vas a contribuir, mantén ese criterio en código, configuración y tests.

## Setup Local

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r project/requirements-dev.txt
Copy-Item project/.env.example project/.env
cd project
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r project/requirements-dev.txt
cp project/.env.example project/.env
cd project
```

## Como Probar Tus Cambios

Desde la raíz del repositorio. Nada de esto consume API ni toca la base del `.env`:

```bash
pytest                                   # suite completa del motor y de BusinessConfig (la misma del CI)
npm --prefix apps/admin-web run typecheck
npm --prefix apps/admin-web test         # panel con un backend en memoria
npm --prefix apps/admin-web run test:integration   # panel contra la API real y un SQLite temporal
```

`pytest -m integration` habla con el modelo real y consume API: solo con `OPENROUTER_API_KEY` y cuando haga falta.

Si cambias el contrato de BusinessConfig, regenera lo derivado en este orden (cada script acepta `--check`):

```bash
python scripts/export_business_config_schema.py
python scripts/generate_business_config_types.py
python scripts/migrate_tenants_to_contract.py
python scripts/generate_traceability_matrix.py
```

## Reglas De Contribucion

1. Haz cambios pequeños y enfocados: un commit por cambio lógico, nunca "todo lo de la fase" en uno.
2. Si tocas comportamiento conversacional, actualiza o agrega pruebas.
3. Si tocas configuración global, modifica primero la base en `project/config/`.
4. Usa overrides en `project/config/tenants/` solo cuando el cambio sea exclusivo de un cliente.
5. No subas secretos reales, archivos `.env` ni `secrets.local.env`.
6. Evita asserts frágiles sobre texto exacto si el comportamiento puede validarse semánticamente (`tests/semantic_guard.py`).
7. Reutiliza fixtures y helpers compartidos: `tests/conftest.py`, `tests/pipeline_harness.py`.
8. Respeta las capas de BusinessConfig (dominio → aplicación → persistencia / API → panel). El motor solo entra al almacén por
   `project/app/infrastructure/business_config/runtime_access.py`. Lo vigila `tests/test_business_config_architecture.py`.

## Convenciones De Testing

- Las pruebas viven en `tests/`, un archivo por tema (`test_<tema>.py`).
- `pytest.ini` usa una **lista cerrada** (`python_files`): una prueba nueva que no se añada allí no corre ni en local ni en el CI.
- Marcadores: `integration` (modelo real) y `engine_pending` (xfail estricto). Este último es para conectar un campo `pendiente`
  del contrato: su prueba se escribe antes que el cambio del motor y pasa a prueba normal cuando el motor lo usa. Hoy no lo
  usa ninguna prueba (`pytest -m engine_pending --runxfail` muestra el detalle cuando las haya).
- El panel tiene sus pruebas junto al código (`apps/admin-web/src/**/*.test.ts(x)`) y su comprobación de arquitectura en
  `apps/admin-web/src/test/architecture.test.ts`.

Cada test debe validar una sola cosa. Si una prueba mezcla intencion, contenido, formato y negocio al mismo tiempo, esta demasiado acoplada y debe dividirse.

## Mensajes De Commit

Formato `tipo(ámbito): qué cambia`, en presente y en una línea; en el cuerpo, el porqué. Tipos: `feat`, `fix`, `refactor`,
`test`, `docs`, `ci`, `chore`. Ejemplo:

```text
fix(business-config): el motor lee el almacén que escribe el panel

Con BUSINESS_CONFIG_STORE=database el cargador abría la base del motor (DATABASE_URL),
no la del panel: lo publicado nunca llegaba a los clientes.
```

## Pull Requests

Incluye en la descripcion:

- que cambiaste
- por que era necesario
- que pruebas ejecutaste
- si hubo cambios en configuracion o documentacion

## Cambios Que Requieren Documentacion

Actualiza `README.md`, `project/README.md` o `docs/` cuando cambies:

- flujo de instalacion
- comandos reales de ejecucion
- estrategia de testing
- endpoints publicos
- manejo de conectores o secretos