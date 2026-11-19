"""La evaluación del lector de pagos (`experiments/quality_lab/run_reader_eval.py`): sus casos y cómo se califica cada lectura. Aquí no
se llama a ninguna IA: se prueba que los casos usan los medios reales del negocio de ejemplo y que la calificación es la correcta.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1] / "experiments" / "quality_lab"
sys.path.insert(0, str(LAB))

from reader_cases import CASES, OFFERS_DETAILS, ReaderCase  # noqa: E402
from run_reader_eval import SLUG, mistakes  # noqa: E402

from app.application.pipeline.payment_reading import PaymentReading  # noqa: E402
from app.application.runtime import load_tenant_runtime_yaml  # noqa: E402
from app.domain.business_config.payment_accounts import options  # noqa: E402
from app.infrastructure.ai.prompting.payment_reader import PAYMENT_READER, reader_prompt  # noqa: E402

LINK = ReaderCase("prefiere el link", "prefiero el link", True, method="link")


def test_the_cases_are_unique_and_use_the_methods_of_the_business():
    assert len({case.name for case in CASES}) == len(CASES)
    offered = {option.split(":")[0] for option in options(load_tenant_runtime_yaml(SLUG))}
    assert {case.method for case in CASES if case.method} <= offered
    assert {case.sent for case in CASES if case.sent} <= offered


def test_wanting_to_buy_and_accepting_the_details_are_both_measured():
    """El error del 19 nov 2026 («lo quiero» leído como «pide los datos») y su contrario (aceptar cuando el asesor ofreció enviarlos)."""
    buys = [case for case in CASES if "lo quiero" in case.message.lower() or "lo compro" in case.message.lower()]
    assert any(not case.wants_details for case in buys) and any(case.wants_details and case.last_reply == OFFERS_DETAILS for case in buys)


def test_a_right_reading_has_no_mistakes():
    assert mistakes(LINK, PaymentReading(wants_details=True, method="link")) == []
    # Sin un medio esperado, el motor puede completar el que venían usando: no se califica.
    assert mistakes(ReaderCase("pide", "pásame el número", True), PaymentReading(wants_details=True, method="nequi")) == []


def test_each_kind_of_mistake_is_named():
    assert mistakes(LINK, None) == ["no hubo lectura"]
    assert mistakes(LINK, PaymentReading(wants_details=False)) == ["dijo que no recibe los datos", "medio «ninguno» en vez de «link»"]
    assert mistakes(LINK, PaymentReading(wants_details=True, method="bank:bancolombia")) == ["medio «bank:bancolombia» en vez de «link»"]
    paid = ReaderCase("ya consignó", "ya te consigné", False, says_paid=True)
    assert mistakes(paid, PaymentReading()) == ["no vio que ya pagó"]
    assert mistakes(ReaderCase("lo quiere", "lo quiero", False), PaymentReading(wants_details=True)) == ["dijo que recibe los datos"]


def test_the_reader_prompt_lives_with_the_reader_and_keeps_its_methods():
    prompt = reader_prompt(load_tenant_runtime_yaml(SLUG))
    assert prompt.startswith("Lees el último mensaje de un cliente") and "Medios de pago del negocio: " in prompt
    assert "Querer comprar no es pedir los datos" in PAYMENT_READER
