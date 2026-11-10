"""Cuánto cuesta una corrida del laboratorio: el cálculo antes de correr (para no pasarse del tope) y lo gastado de verdad."""
from __future__ import annotations

import httpx

# Promedios medidos en el laboratorio (exp_20261110_calidad_prompt_v2), por llamada.
ASSISTANT_TOKENS = (1_300, 80)
RUBRIC_TOKENS = (5_000, 900)
PAIRWISE_TOKENS = (8_000, 60)


def prices(models: set[str]) -> dict[str, tuple[float, float]]:
    """Dólares por token (entrada, salida) de cada modelo, según la lista pública de OpenRouter."""
    found = {}
    for item in httpx.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]:
        if item["id"] in models:
            found[item["id"]] = (float(item["pricing"]["prompt"]), float(item["pricing"]["completion"]))
    missing = models - set(found)
    if missing:
        raise SystemExit(f"OpenRouter no tiene estos modelos: {sorted(missing)}")
    return found


def _cost(tokens: tuple[int, int], price: tuple[float, float]) -> float:
    return tokens[0] * price[0] + tokens[1] * price[1]


def estimate(*, conversations: int, turns: int, model: str, judge: str, table: dict[str, tuple[float, float]], with_capture: bool = True) -> float:
    """Dólares que costaría: las conversaciones de los dos lados (si se capturan) y el juez (rúbrica de cada lado y comparación)."""
    capture = 2 * turns * _cost(ASSISTANT_TOKENS, table[model]) if with_capture else 0.0
    judging = 2 * conversations * _cost(RUBRIC_TOKENS, table[judge]) + conversations * _cost(PAIRWISE_TOKENS, table[judge])
    return round(capture + judging, 4)


def spent(usages: list[dict], price: tuple[float, float]) -> float:
    """Lo gastado de verdad: el costo que informa OpenRouter o, si no lo informa, los tokens por el precio."""
    total = 0.0
    for usage in usages:
        if isinstance(usage.get("cost"), (int, float)):
            total += float(usage["cost"])
        else:
            total += usage.get("prompt_tokens", 0) * price[0] + usage.get("completion_tokens", 0) * price[1]
    return round(total, 4)
