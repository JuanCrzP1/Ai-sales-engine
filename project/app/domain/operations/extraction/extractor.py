from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from app.domain.operations.contracts import OperationalContinuityState
from app.domain.operations.rendering.renderer import render_operational_anchor

_PAYMENT_OPTIONS = {
    "nequi": "nequi",
    "daviplata": "daviplata",
    "link": "link",
    "enlace": "link",
    "transferencia": "transferencia",
    "bank": "bank",
    "bancolombia": "bank",
    "breb": "breb",
    "bre-b": "breb",
}


def _expiry(*, now: datetime, hours: int = 6) -> datetime:
    return now + timedelta(hours=hours)


def _state(*, active_process: str = "", active_option: str = "", pending_action: str = "", expires_at: datetime | None = None) -> OperationalContinuityState:
    candidate = OperationalContinuityState(
        active_process=str(active_process or "").strip().lower(),
        active_option=str(active_option or "").strip().lower(),
        pending_action=str(pending_action or "").strip().lower(),
        expires_at=expires_at,
    )
    if candidate.active_process:
        candidate.natural_anchor = render_operational_anchor(candidate)
    return candidate


def _detect_payment_option(text: str) -> str:
    normalized = str(text or "").strip().lower()
    for token, normalized_option in _PAYMENT_OPTIONS.items():
        if token in normalized:
            return normalized_option
    return ""


def extract_operational_state_from_metadata(metadata: dict | None, *, now: datetime | None = None) -> OperationalContinuityState:
    payload = metadata if isinstance(metadata, dict) else {}
    effective_now = now or datetime.now(timezone.utc)

    payment_status = str(payload.get("payment_status") or "").strip().lower()
    payment_method = str(payload.get("payment_method") or "").strip().lower()
    mode = str(payload.get("mode") or "").strip().lower()
    stage = str(payload.get("stage") or "").strip().lower()

    if payment_status == "reportado":
        return _state(
            active_process="payment",
            active_option=payment_method,
            pending_action="payment_review",
            expires_at=_expiry(now=effective_now),
        )
    if payment_method:
        return _state(
            active_process="payment",
            active_option=payment_method,
            pending_action="report_payment",
            expires_at=_expiry(now=effective_now),
        )
    if mode == "demo":
        return _state(
            active_process="demo",
            pending_action="continue_demo",
            expires_at=_expiry(now=effective_now, hours=2),
        )
    if stage in {"activation", "onboarding", "closing"}:
        pending_action = "share_startup_data" if stage in {"activation", "onboarding"} else "continue_close"
        return _state(
            active_process="activation" if stage != "closing" else "activation",
            pending_action=pending_action,
            expires_at=_expiry(now=effective_now),
        )
    return OperationalContinuityState()


def extract_operational_state_from_response(
    *,
    response_text: str,
    runtime_yaml: dict | None,
    route_source: str = "",
    now: datetime | None = None,
) -> OperationalContinuityState:
    del runtime_yaml
    effective_now = now or datetime.now(timezone.utc)
    raw_text = str(response_text or "").strip()
    normalized = raw_text.lower()
    source = str(route_source or "").strip().lower()

    if not normalized:
        return OperationalContinuityState()

    if source == "demo" or normalized.startswith("perfecto, mira, esto sería respondiendo a tu cliente:") or normalized.startswith("perfecto, mira, esto seria respondiendo a tu cliente:"):
        return _state(
            active_process="demo",
            pending_action="continue_demo",
            expires_at=_expiry(now=effective_now, hours=2),
        )

    for explicit_option, pattern in (
        ("nequi", r"prefieres que te env[ií]e el n[uú]mero de nequi|quieres que te env[ií]e los datos de nequi|te mando los datos de nequi|te gustar[ií]a proceder con el pago por nequi|proced(?:er|amos|emos|e)? con el pago por nequi|pagar por nequi"),
        ("daviplata", r"prefieres que te env[ií]e el n[uú]mero de daviplata|quieres que te env[ií]e los datos de daviplata|te mando los datos de daviplata|te gustar[ií]a proceder con el pago por daviplata|proced(?:er|amos|emos|e)? con el pago por daviplata|pagar por daviplata"),
        ("link", r"prefieres que te env[ií]e el link|prefieres que te env[ií]e el enlace|quieres que te env[ií]e el link|quieres que te env[ií]e el enlace|te gustar[ií]a proceder con el pago por link|te gustar[ií]a proceder con el link de pago|proced(?:er|amos|emos|e)? con el link de pago|pagar por link|pagar por enlace"),
    ):
        if re.search(pattern, normalized):
            return _state(
                active_process="payment",
                active_option=explicit_option,
                pending_action="confirm_method",
                expires_at=_expiry(now=effective_now),
            )

    singular_send_match = re.search(r"(?:quieres|prefieres|te mando|te envío|te envio|te paso).{0,40}(nequi|daviplata|link|enlace|breb|bre-b)", normalized)
    if singular_send_match and " o " not in normalized[: singular_send_match.end() + 25]:
        return _state(
            active_process="payment",
            active_option=_detect_payment_option(singular_send_match.group(1)),
            pending_action="confirm_method",
            expires_at=_expiry(now=effective_now),
        )

    if "cuando lo hagas, avísame para continuar" in normalized or "cuando lo hagas, avisame para continuar" in normalized:
        return _state(
            active_process="payment",
            active_option=_detect_payment_option(normalized),
            pending_action="report_payment",
            expires_at=_expiry(now=effective_now),
        )

    if ("prefieres" in normalized or "elige" in normalized) and ("link" in normalized or "enlace" in normalized) and "transfer" in normalized:
        return _state(
            active_process="payment",
            pending_action="choose_payment_channel",
            expires_at=_expiry(now=effective_now),
        )

    if ("prefieres" in normalized or "elige" in normalized or "cuál" in normalized or "cual" in normalized) and any(option in normalized for option in ("nequi", "daviplata", "bancolombia", "breb", "bre-b")):
        return _state(
            active_process="payment",
            pending_action="choose_payment_option",
            expires_at=_expiry(now=effective_now),
        )

    if "para activar" in normalized and any(token in normalized for token in ("nombre", "teléfono", "telefono", "número", "numero", "datos", "correo")):
        return _state(
            active_process="activation",
            pending_action="share_startup_data",
            expires_at=_expiry(now=effective_now),
        )

    if any(token in normalized for token in ("configuración inicial", "configuracion inicial", "guía de integración", "guia de integracion", "empezamos con la configuración", "empezamos con la configuracion")):
        return _state(
            active_process="onboarding",
            pending_action="share_startup_data",
            expires_at=_expiry(now=effective_now),
        )

    if any(token in normalized for token in ("te paso con", "te pongo con", "te conecto con", "te comunica", "te comunicamos con")):
        return _state(
            active_process="handoff",
            pending_action="wait_handoff",
            expires_at=_expiry(now=effective_now, hours=2),
        )

    return OperationalContinuityState()