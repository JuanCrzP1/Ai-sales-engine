"""El lector del saludo (`application/pipeline/greeting_reading.py`) y su evaluación (`experiments/quality_lab/run_greeting_eval.py`).

Aquí no se llama a ninguna IA: se prueba qué hace el motor con cada respuesta del lector, que no hay reglas de palabras y que la
evaluación califica bien. Que la IA real acierte se mide con la evaluación (26 nov 2026: 178 de 180, ningún error grave).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1] / "experiments" / "quality_lab"
sys.path.insert(0, str(LAB))

from greeting_cases import CASES, GreetingCase  # noqa: E402
from run_greeting_eval import verdict  # noqa: E402

from app.application.pipeline import conversation_flow  # noqa: E402
from app.application.pipeline.greeting_reading import MAX_TOKENS, reads_as_greeting  # noqa: E402
from app.infrastructure.ai.prompting.greeting_reader import GREETING_READER, greeting_turn  # noqa: E402


class _Reader:
    def __init__(self, answer) -> None:
        self.answer, self.calls = answer, []

    def classify(self, prompt, *, user_message, bot_config=None, max_tokens=120):
        self.calls.append((prompt, user_message, max_tokens))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


@pytest.mark.parametrize(("answer", "expected"), [
    ('{"solo_saluda": true}', True),
    ('{"solo_saluda": false}', False),
    ('Claro: {"solo_saluda": true}', True),
    ("no es json", None),
    ('{"solo_saluda": "sí"}', None),
    ("{}", None),
    (RuntimeError("business_ai_key_missing"), None),
])
def test_what_the_engine_does_with_each_answer_of_the_reader(answer, expected):
    reader = _Reader(answer)
    assert reads_as_greeting(reader, bot_config=None, user_message="qué onda") is expected
    assert reader.calls == [(GREETING_READER, greeting_turn("qué onda"), MAX_TOKENS)]


def test_an_empty_message_or_an_engine_without_reader_is_not_read():
    reader = _Reader('{"solo_saluda": true}')
    assert reads_as_greeting(reader, bot_config=None, user_message="  ") is None and reader.calls == []
    assert reads_as_greeting(object(), bot_config=None, user_message="hola") is None


def test_the_word_list_is_gone():
    """Hasta el 26 nov 2026 una lista de saludos colombianos decidía; no debe volver."""
    source = Path(conversation_flow.__file__).read_text(encoding="utf-8")
    assert not hasattr(conversation_flow, "is_greeting_only") and "parcero" not in source and "qlq" not in source


def test_the_cases_measure_both_sides_and_are_unique():
    assert len({case.message for case in CASES}) == len(CASES)
    assert sum(case.greets_only for case in CASES) >= 15 and sum(not case.greets_only for case in CASES) >= 15


def test_the_grave_mistake_is_named_apart():
    greeting, question = GreetingCase("hola", True), GreetingCase("hola, ¿precio?", False)
    assert [verdict(greeting, True), verdict(question, False)] == ["bien", "bien"]
    assert verdict(question, True) == "saludo fijo a quien preguntó"
    assert verdict(greeting, False) == "respondió la IA a un saludo"
    assert verdict(greeting, None) == "sin lectura"
