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

La memoria del motor se prueba contra un PostgreSQL de verdad (`tests/test_memory_postgres.py`). Sin `TEST_POSTGRES_URL` esas
pruebas se saltan; el CI levanta un PostgreSQL y las corre siempre. En tu equipo, con una base **vacía y solo para esto** (las pruebas
vacían sus tablas):

```bash
createdb ai_sales_engine_pruebas_memoria
TEST_POSTGRES_URL=postgresql+psycopg:///ai_sales_engine_pruebas_memoria pytest tests/test_memory_postgres.py
```

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

Si el cambio toca cómo responde el asesor (las instrucciones, lo que se le cuenta de la conversación o los pagos), además debe pasar
la puerta de calidad con la IA real: `python experiments/quality_lab/run_standard_gate.py --experiment <id>`. Hazlo en una rama y
pásalo a `main` solo cuando diga PASA. Ver [Calidad del asesor](docs/calidad-del-asesor.md).

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

Una línea en español que diga qué cambia para el negocio, sin prefijos en inglés; si hace falta, el porqué en el cuerpo. Ejemplos:

```text
Eliminar chats y clientes de verdad, borrar de una vez las pruebas y diálogos que cubren toda la página

El asistente también olvida al cliente: si vuelve a escribir, empieza de cero. Las ventas se conservan.
```

Un commit por cambio lógico. Si el cambio toca el motor, el cuerpo dice el resultado del laboratorio de regresión.

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