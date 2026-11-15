"""Cuánto cuesta una corrida del laboratorio: el cálculo antes de correr (para no pasarse del tope) y lo gastado de verdad."""
from __future__ import annotations

import httpx

# Promedios medidos en el laboratorio (exp_20261110_calidad_prompt_v2), por llamada.
ASSISTANT_TOKENS = (1_300, 80)
RUBRIC_TOKENS = (5_000, 900)
PAIRWISE_TOKENS = (8_000, 60)

# La puerta de calidad (`run_standard_gate.py`), medido en `nota_equipo_pagos_20261114_e` (gpt-4o-mini, 81 mensajes): cada mensaje del
# cliente cuesta unos 3.740 tokens de entrada y 103 de salida, repartidos en 2,1 llamadas (el asesor, el lector de pagos y a veces una
# segunda respuesta, la nota para el equipo o el resumen). Con `ASSISTANT_TOKENS` el cálculo daba diez veces menos de lo gastado.
GATE_MESSAGE_TOKENS = (3_800, 110)
# El juez y el segundo revisor, por conversación (medido: USD 0,00036 con gemini-2.5-flash; esto da un poco más).
GATE_JUDGE_TOKENS = (1_500, 60)
# Un modelo que razona antes de responder cobra ese razonamiento como salida, y cuánto razona no se sabe antes: se calcula con este
# máximo de tokens de salida extra por mensaje (el motor limita cada respuesta a 500).
REASONING_TOKENS_PER_MESSAGE = 900


def catalog(models: set[str]) -> dict[str, dict]:
    """De cada modelo, según la lista pública de OpenRouter: dólares por token (`prices`: entrada, salida) y si puede razonar antes
    de responder (`reasons`)."""
    found = {}
    for item in httpx.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]:
        if item["id"] in models:
            found[item["id"]] = {
                "prices": (float(item["pricing"]["prompt"]), float(item["pricing"]["completion"])),
                "reasons": "reasoning" in (item.get("supported_parameters") or []),
            }
    missing = models - set(found)
    if missing:
        raise SystemExit(f"OpenRouter no tiene estos modelos: {sorted(missing)}")
    return found


def prices(models: set[str]) -> dict[str, tuple[float, float]]:
    """Dólares por token (entrada, salida) de cada modelo, según la lista pública de OpenRouter."""
    return {model: item["prices"] for model, item in catalog(models).items()}


def estimate_gate(*, messages: int, conversations: int, model: str, judge: str, models: dict[str, dict], with_capture: bool = True) -> float:
    """Dólares que costaría una corrida de la puerta: los mensajes del asesor (con el máximo de razonamiento, si el modelo razona)
    y el juez de cada conversación. `models` es lo que devuelve `catalog`."""
    tokens = GATE_MESSAGE_TOKENS
    if models[model]["reasons"]:
        tokens = (tokens[0], tokens[1] + REASONING_TOKENS_PER_MESSAGE)
    capture = messages * _cost(tokens, models[model]["prices"]) if with_capture else 0.0
    return round(capture + conversations * _cost(GATE_JUDGE_TOKENS, models[judge]["prices"]), 4)


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
