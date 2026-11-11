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
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r project/requirements-dev.txt
cp project/.env.example project/.env
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
python scripts/generate_traceability_matrix.py
```

Si cambias a propósito un negocio de ejemplo (`project/config/tenants/<negocio>/business-config.json`), regenera su referencia
congelada: `python tests/golden/regenerate.py <negocio>`.

Si tocas el motor (pipeline, prompt, compilador o carga de lo publicado), corre antes y después el laboratorio de regresión contra
el último commit; no gasta nada:

```bash
python experiments/pricing_lab/run_regression_experiment.py --experiment exp_<fecha>_<tema> --baseline <commit>
```

El objetivo es «motor sin diferencias», o que las únicas diferencias sean las que buscabas.

## Reglas De Contribucion

1. Haz cambios pequeños y enfocados: un commit por cambio lógico, nunca "todo lo de la fase" en uno.
2. Si tocas comportamiento conversacional, actualiza o agrega pruebas.
3. La configuración de un negocio se cambia en el panel, nunca en el código ni en archivos. Los ajustes de la plataforma están en
   `project/config/system/`.
4. `project/config/tenants/` son solo los negocios de ejemplo: nunca datos de un cliente real.
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