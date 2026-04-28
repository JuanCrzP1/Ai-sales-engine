# Contributing

## Objetivo

Este repositorio prioriza estabilidad operativa, configuración explícita y pruebas que validan comportamiento real del sistema de ventas. Si vas a contribuir, mantén ese criterio en código, configuración y tests.

## Setup Local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r project/requirements.txt
Copy-Item project/.env.example project/.env
Set-Location project
```

## Como Probar Tus Cambios

```powershell
pytest tests/unit -q
pytest tests/integration -q
pytest tests/e2e -q
pytest -q
```

## Reglas De Contribucion

1. Haz cambios pequeños y enfocados.
2. Si tocas comportamiento conversacional, actualiza o agrega pruebas por capa.
3. Si tocas configuración global, modifica primero la base en `config/`.
4. Usa overrides en `config/tenants/` solo cuando el cambio sea exclusivo de un cliente.
5. No subas secretos reales ni archivos `.env`.
6. Evita asserts frágiles sobre texto exacto si el comportamiento puede validarse semánticamente.
7. Reutiliza fixtures y helpers compartidos desde `tests/conftest.py` y `tests/behavior_assertions.py`.

## Convenciones De Testing

- `tests/unit/`: lógica pura y determinista
- `tests/integration/`: conexión entre capas, endpoints y runtime policies
- `tests/e2e/`: pocos flujos completos y representativos

Cada test debe validar una sola cosa. Si una prueba mezcla intencion, contenido, formato y negocio al mismo tiempo, esta demasiado acoplada y debe dividirse.

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