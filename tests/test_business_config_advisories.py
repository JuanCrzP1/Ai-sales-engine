"""Los avisos que el panel calcula en vivo también salen del diagnóstico del servidor, con el mismo campo y el mismo texto.

Así el agente que trabaja por MCP (`review_business_config`) ve lo mismo que la persona en la pantalla. Los casos están en
`project/config/contracts/v1/advisory-cases.json`; el panel prueba los mismos en `src/domain/validation/advisoryParity.test.ts`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.business_config_application.templates import BusinessTemplateCatalog
from app.domain.business_config.agent_edits import merged
from app.domain.business_config.diagnostics import LIVE_ADVISORY_CODES, review
from app.domain.business_config.validation import validate_document

CASES_PATH = Path(__file__).resolve().parents[1] / "project" / "config" / "contracts" / "v1" / "advisory-cases.json"
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]


def _base() -> dict:
    """Un documento válido y completo: la plantilla de restaurante con su dirección, su motivo de compra y un medio de pago."""
    template = next(item for item in BusinessTemplateCatalog.from_directory().list() if item.id == "restaurante")
    document = template.instantiate("avisos", "Negocio de avisos")
    return merged(document, {
        "identity": {"location": {"type": "fisico", "address": "Calle 10 # 20-30"}},
        "sales": {"buying_motivation": {"primary": "tiempo"}},
        "messages": {"payment_reported": "Gracias, ya lo reviso."},
        "payments": [{"id": "principal", "transfer_enabled": True, "transfer_methods": [{"type": "nequi", "number": {"secret_ref": "secret_store:principal.nequi.number.x"}}]}],
        "offer": {"catalog": {"payment_profile": "principal"}},
    })


def _codes(document: dict) -> set[str]:
    return {item.code for item in review(validate_document("avisos", document))}


def test_the_cases_cover_every_live_advisory():
    assert sorted(case["code"] for case in CASES) == sorted(LIVE_ADVISORY_CODES)


def test_a_complete_document_has_none_of_them():
    assert _codes(_base()) & set(LIVE_ADVISORY_CODES) == set()


@pytest.mark.parametrize("case", CASES, ids=[case["code"] for case in CASES])
def test_each_case_gives_the_same_advisory_as_the_panel(case):
    found = [item for item in review(validate_document("avisos", merged(_base(), case["changes"]))) if item.code == case["code"]]
    assert [(item.path, item.message) for item in found] == [(case["field"], case["message"])]
