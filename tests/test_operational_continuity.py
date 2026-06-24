"""Validación de continuidad operacional multi-tenant.

Cubre:
1. Aislamiento de métodos por tenant (solo métodos configurados son reconocidos)
2. Listing vs opción activa (>1 método mencionado = no se captura ninguno)
3. Proceso genérico fallback (sin métodos configurados)
4. Procesos no-pago (demo, activation, onboarding, handoff) siguen funcionando
5. Helper _get_configured_payment_methods desde runtime_yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pytest

from app.domain.operations.operational_extractor import extract_op_state
from app.application.pipeline.ai_execution import _get_configured_payment_methods


# ---------------------------------------------------------------------------
# Fixtures — runtime_yaml mocks for different tenant configurations
# ---------------------------------------------------------------------------

def _runtime_nequi_only() -> dict:
    return {
        "pricing": {
            "plans": [
                {
                    "payment": {
                        "transfer": {
                            "methods": [
                                {"type": "nequi", "number": "3001234567"},
                            ]
                        }
                    }
                }
            ]
        }
    }


def _runtime_bank_only() -> dict:
    return {
        "pricing": {
            "plans": [
                {
                    "payment": {
                        "transfer": {
                            "methods": [
                                {"type": "bank", "bank": "Bancolombia"},
                            ]
                        }
                    }
                }
            ]
        }
    }


def _runtime_link_only() -> dict:
    return {
        "pricing": {
            "plans": [
                {
                    "payment": {
                        "link": "https://checkout.example.com/plan",
                        "transfer": {
                            "methods": [
                                {"type": "link"},
                            ]
                        }
                    }
                }
            ]
        }
    }


def _runtime_nequi_breb() -> dict:
    return {
        "pricing": {
            "plans": [
                {
                    "payment": {
                        "transfer": {
                            "methods": [
                                {"type": "nequi", "number": "3001234567"},
                                {"type": "breb", "reference": "user@mail.com"},
                            ]
                        }
                    }
                }
            ]
        }
    }


def _runtime_catalog_nequi() -> dict:
    return {
        "pricing": {
            "model": "catalog",
            "catalog": {
                "payment": {
                    "transfer": {
                        "methods": [
                            {"type": "nequi", "number": "3009876543"},
                        ]
                    }
                }
            }
        }
    }


def _runtime_no_methods() -> dict:
    return {"pricing": {}}


# ---------------------------------------------------------------------------
# 1. _get_configured_payment_methods
# ---------------------------------------------------------------------------

class TestGetConfiguredPaymentMethods:
    def test_plans_single_method(self):
        result = _get_configured_payment_methods(_runtime_nequi_only())
        assert result == ["nequi"]

    def test_plans_multiple_methods(self):
        result = _get_configured_payment_methods(_runtime_nequi_breb())
        assert result == ["nequi", "breb"]

    def test_catalog_structure(self):
        result = _get_configured_payment_methods(_runtime_catalog_nequi())
        assert result == ["nequi"]

    def test_empty_pricing(self):
        result = _get_configured_payment_methods(_runtime_no_methods())
        assert result == []

    def test_no_pricing_key(self):
        result = _get_configured_payment_methods({})
        assert result == []

    def test_deduplication_across_plans(self):
        runtime = {
            "pricing": {
                "plans": [
                    {"payment": {"transfer": {"methods": [{"type": "nequi"}]}}},
                    {"payment": {"transfer": {"methods": [{"type": "nequi"}, {"type": "bank"}]}}},
                ]
            }
        }
        result = _get_configured_payment_methods(runtime)
        assert result == ["nequi", "bank"]


# ---------------------------------------------------------------------------
# 2. Multi-tenant isolation — Tenant A: solo nequi
# ---------------------------------------------------------------------------

class TestTenantNequiOnly:
    METHODS = ["nequi"]

    def test_nequi_response_captured(self):
        text = "Perfecto, te envío el número de nequi para que hagas la transferencia."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_process == "payment"
        assert state.active_option == "nequi"

    def test_daviplata_response_ignored(self):
        """Tenant no tiene daviplata → no debe capturarse aunque la IA lo mencione."""
        text = "Te envío los datos de daviplata para proceder."
        state = extract_op_state(text, payment_methods=self.METHODS)
        # Should NOT capture daviplata as active option
        assert state.active_option != "daviplata"

    def test_bank_response_ignored(self):
        text = "Te comparto los datos de Bancolombia para la transferencia."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option != "bank"

    def test_listing_nequi_alone_is_active(self):
        """Si solo hay nequi configurado y la IA lo menciona, es activo."""
        text = "Puedes pagar por nequi usando el número que te envío."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option == "nequi"


# ---------------------------------------------------------------------------
# 3. Multi-tenant isolation — Tenant B: solo bank
# ---------------------------------------------------------------------------

class TestTenantBankOnly:
    METHODS = ["bank"]

    def test_bank_response_captured(self):
        text = "Te comparto los datos de Bancolombia para que hagas la transferencia bancaria."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_process == "payment"
        assert state.active_option == "bank"

    def test_nequi_response_ignored(self):
        """Tenant no tiene nequi → texto con nequi no debe capturarse."""
        text = "Puedes pagar por nequi, es más rápido."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option != "nequi"


# ---------------------------------------------------------------------------
# 4. Multi-tenant isolation — Tenant C: solo link
# ---------------------------------------------------------------------------

class TestTenantLinkOnly:
    METHODS = ["link"]

    def test_link_response_captured(self):
        text = "Te envío el link de pago para que completes la compra."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_process == "payment"
        assert state.active_option == "link"

    def test_enlace_signal_captured(self):
        text = "Aquí tienes el enlace de pago para proceder."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option == "link"

    def test_nequi_ignored_for_link_tenant(self):
        text = "Puedes pagar con nequi si prefieres."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option != "nequi"


# ---------------------------------------------------------------------------
# 5. Multi-tenant isolation — Tenant D: nequi + breb
# ---------------------------------------------------------------------------

class TestTenantNequiBreb:
    METHODS = ["nequi", "breb"]

    def test_nequi_captured(self):
        text = "Te doy el número de nequi para que hagas el pago."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option == "nequi"

    def test_breb_captured(self):
        text = "Puedes pagar por Bre-B usando la referencia que te doy."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option == "breb"

    def test_listing_both_no_specific_option(self):
        """Cuando la IA lista ambos métodos, no se captura ninguno específico."""
        text = "Puedes pagar por nequi o por Bre-B, el que prefieras."
        state = extract_op_state(text, payment_methods=self.METHODS)
        # Both matched → listing, not specific
        assert state.active_option == ""
        # But it's still a payment process
        assert state.active_process in ("payment", "")

    def test_daviplata_ignored(self):
        text = "Te envío los datos de daviplata."
        state = extract_op_state(text, payment_methods=self.METHODS)
        assert state.active_option != "daviplata"


# ---------------------------------------------------------------------------
# 6. Generic payment fallback (no configured methods)
# ---------------------------------------------------------------------------

class TestGenericPaymentFallback:
    def test_no_methods_no_specific_option(self):
        text = "Te envío el número de nequi para que hagas la transferencia."
        state = extract_op_state(text, payment_methods=[])
        # Without configured methods, can't capture specific option
        assert state.active_option == ""

    def test_generic_signal_still_captured(self):
        text = "Avancemos con el pago para completar tu compra."
        state = extract_op_state(text, payment_methods=[])
        assert state.active_process == "payment"
        assert state.pending_action == "choose_payment_option"

    def test_none_methods_same_as_empty(self):
        text = "Avancemos con el pago."
        state_none = extract_op_state(text, payment_methods=None)
        state_empty = extract_op_state(text, payment_methods=[])
        assert state_none.active_process == state_empty.active_process
        assert state_none.active_option == state_empty.active_option


# ---------------------------------------------------------------------------
# 7. Non-payment processes unchanged
# ---------------------------------------------------------------------------

class TestNonPaymentProcesses:
    def test_activation_detected(self):
        text = "Para activar el sistema, necesito algunos datos de arranque."
        state = extract_op_state(text, payment_methods=["nequi"])
        assert state.active_process == "activation"

    def test_onboarding_detected(self):
        text = "Vamos a dejarlo listo para que puedas empezar."
        state = extract_op_state(text, payment_methods=["nequi"])
        assert state.active_process == "onboarding"

    def test_handoff_detected(self):
        text = "Te paso con el equipo de implementación para que te guíen."
        state = extract_op_state(text, payment_methods=["nequi"])
        assert state.active_process == "handoff"

    def test_empty_response(self):
        state = extract_op_state("", payment_methods=["nequi"])
        assert state.active_process == ""
        assert not state.is_active()
