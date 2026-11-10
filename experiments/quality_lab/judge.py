"""El juez: otra IA califica cada conversación con una rúbrica fija, sin saber qué versión del prompt la produjo.

Dos miradas:
- Rúbrica absoluta por turno (0 a 2 en cinco criterios), sobre la conversación de una sola versión.
- Comparación a ciegas de las dos versiones de la misma conversación, en orden aleatorio.
"""
from __future__ import annotations

import json
import random
import time

import httpx

API = "https://openrouter.ai/api/v1/chat/completions"
CRITERIA = ("resuelve", "veraz", "avanza", "tono", "claridad")

RUBRIC = """
Eres un evaluador exigente de vendedores por chat en Colombia, como un jefe de ventas que revisa conversaciones reales. Calificas
las respuestas del asistente de un negocio. La FICHA es lo único verdadero sobre el negocio. Sé estricto: 2 solo si es impecable.

Califica CADA respuesta del asistente de 0 a 2 en:
- resuelve: responde exactamente lo que el cliente preguntó o pidió en ese turno (2 completo, 1 a medias, 0 no).
- veraz: 0 si afirma algo que NO está en la ficha: productos, ingredientes, características, precios, cobertura o envíos,
  horarios, políticas, canales, tiempos de entrega o descuentos. 0 también si usa un argumento que no aplica a este cliente (por
  ejemplo, hablarle a quien compra una hamburguesa de "ventas al mes" o del "costo del servicio"). 1 si exagera o es vago donde la
  ficha es precisa. 2 si todo está respaldado o, cuando no sabe, lo dice y ofrece confirmarlo.
- avanza: lleva al siguiente paso adecuado (elegir, pedir, pagar) sin presionar, sin repetir lo ya dicho y sin volver atrás.
- tono: suena a una persona del negocio, natural, en español correcto, con el tono de la ficha; 1 si es genérico o acartonado.
- claridad: breve, un tema por mensaje, sin listas largas ni relleno; respeta el máximo de palabras de la ficha.
Las respuestas que entregan datos de pago con «[dato entregado por el motor]» y la respuesta al pago reportado las arma el sistema
con textos del negocio: califícalas solo por si encajan en la conversación.
Devuelve SOLO JSON: {"turnos": [{"turno": n, "resuelve": 0-2, "veraz": 0-2, "avanza": 0-2, "tono": 0-2, "claridad": 0-2,
"nota": "solo si algo falló: qué, en máximo 12 palabras; si no, vacío"}], "general": "máximo 20 palabras"}
""".strip()

PAIRWISE = """
Eres un evaluador experto de vendedores por chat. Tienes la FICHA del negocio y DOS versiones (A y B) de la misma conversación:
el cliente dijo lo mismo; solo cambian las respuestas del asistente. ¿Cuál vende mejor sin inventar nada? Considera, en este
orden: no inventa nada fuera de la ficha ni usa argumentos que no aplican al cliente; responde lo que preguntan; avanza la venta sin
presionar; suena humano y es claro. Si son equivalentes, di empate.
Devuelve SOLO JSON: {"mejor": "A" | "B" | "empate", "razon": "máximo 20 palabras"}
""".strip()


def _transcript(turns: list[dict]) -> str:
    return "\n".join(f"[{t['turn']}] Cliente: {t['message']}\n[{t['turn']}] Asistente: {t['reply']}" for t in turns)


def _call(api_key: str, model: str, system: str, user: str) -> tuple[dict, dict]:
    # Con tope de salida (el proveedor reserva el costo máximo de cada llamada) y sin razonamiento oculto, que se cobra como salida.
    payload = {"model": model, "temperature": 0, "max_tokens": 1500, "response_format": {"type": "json_object"}, "reasoning": {"enabled": False},
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    for attempt in range(3):
        try:
            response = httpx.post(API, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=120)
            if response.status_code == 400 and "reasoning" in payload:
                payload.pop("reasoning")  # un modelo que no admite apagar el razonamiento: se pide sin ese ajuste
                continue
            response.raise_for_status()
            body = response.json()
            return json.loads(body["choices"][0]["message"]["content"]), body.get("usage") or {}
        except (httpx.HTTPError, ValueError, KeyError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("inalcanzable")


def score_conversation(api_key: str, model: str, facts: dict, turns: list[dict]) -> tuple[dict, dict]:
    user = f"FICHA:\n{json.dumps(facts, ensure_ascii=False)}\n\nCONVERSACIÓN:\n{_transcript(turns)}"
    return _call(api_key, model, RUBRIC, user)


def compare(api_key: str, model: str, facts: dict, baseline: list[dict], candidate: list[dict], *, seed: int) -> tuple[str, str, dict]:
    """'baseline', 'candidate' o 'empate', con la razón del juez. El orden A/B se sortea."""
    flipped = random.Random(seed).random() < 0.5
    first, second = (candidate, baseline) if flipped else (baseline, candidate)
    user = f"FICHA:\n{json.dumps(facts, ensure_ascii=False)}\n\nVERSIÓN A:\n{_transcript(first)}\n\nVERSIÓN B:\n{_transcript(second)}"
    verdict, usage = _call(api_key, model, PAIRWISE, user)
    choice = str(verdict.get("mejor") or "empate").strip().upper()
    winner = "empate" if choice not in {"A", "B"} else ("candidate" if (choice == "A") == flipped else "baseline")
    return winner, str(verdict.get("razon") or ""), usage
