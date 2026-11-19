"""La respuesta que reciben los canales: con los espacios en orden y con las palabras que eligió la IA, ni una más ni una menos.

Antes lo hacía `application/response_guard.py`, que también borraba palabras «prohibidas» según el tipo de negocio; esa parte
estaba apagada desde abril (AI-first: lo que dice el asesor lo decide la IA) y se retiró el 18 de noviembre de 2026. Queda solo el
orden de los espacios (`response_postprocessor.tidy_spacing`), en el mismo lugar del camino (`application/assistant_service.py`).
"""
from __future__ import annotations

import pytest

from app.application.pipeline.response_postprocessor import tidy_spacing
from app.application import assistant_service as ai_service


@pytest.mark.parametrize(
    "raw, tidy",
    [
        ("Hola ,  ¿cómo estás ?", "Hola, ¿cómo estás?"),
        ("  Precio:\t$ 50.000  ", "Precio: $ 50.000"),
        ("Primero.\n\n\n\nDespués.", "Primero.\n\nDespués."),
        ("Línea uno\nLínea dos", "Línea uno\nLínea dos"),
        ("   ", ""),
        (None, ""),
    ],
)
def test_only_the_spacing_changes(raw, tidy):
    assert tidy_spacing(raw) == tidy


@pytest.mark.parametrize(
    "reply",
    ["Actualmente tenemos plan premium y te sirve para empezar rápido.", "No manejamos nequi por ahora.", "Vendemos hamburguesa y bebida, con implementación rápida."],
)
def test_the_words_the_ai_chose_are_never_changed(reply):
    assert tidy_spacing(reply) == reply


class _Pipeline:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def run(self, **_kwargs):
        return self.reply, True, {"intent": "info"}


def test_every_channel_receives_the_tidy_reply(monkeypatch):
    service = ai_service.AIService.__new__(ai_service.AIService)
    service.pipeline = _Pipeline("Te cuento ,  el plan básico   cuesta $ 50.000 .\n\n\n¿Lo quieres ?")
    reply, ai_used, metadata = service.generate_business_reply(
        tenant=None, bot_config=None, user_message="¿Cuánto vale?", conversation_history=[], faq_results=[], include_metadata=True,
    )
    assert reply == "Te cuento, el plan básico cuesta $ 50.000.\n\n¿Lo quieres?"
    assert ai_used is True and metadata == {"intent": "info", "memory_context": {}}
