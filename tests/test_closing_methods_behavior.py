from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.application.runtime import load_tenant_runtime_yaml
from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService
from app.services.ai_service import AIService
from semantic_guard import has_forward_intent

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def _tenant(slug: str) -> SimpleNamespace:
    return SimpleNamespace(name=slug, slug=slug, id=slug)


def _runtime_with_closing_methods(tenant_slug: str, method_flags: dict[str, bool]) -> dict:
    runtime_yaml = load_tenant_runtime_yaml(tenant_slug, channel="whatsapp")
    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    runtime_yaml["capabilities"] = capabilities

    closing_methods = capabilities.get("closing_methods") if isinstance(capabilities.get("closing_methods"), dict) else {}
    capabilities["closing_methods"] = closing_methods

    for method_name in ("link_payment", "human_handoff", "data_collection"):
        current_entry = closing_methods.get(method_name) if isinstance(closing_methods.get(method_name), dict) else {}
        enabled = bool(method_flags.get(method_name, current_entry.get("enabled", False) if isinstance(current_entry, dict) else False))
        closing_methods[method_name] = {
            **(current_entry if isinstance(current_entry, dict) else {}),
            "enabled": enabled,
        }

    return runtime_yaml


def _set_payment_link(runtime_yaml: dict, *, link: str) -> dict:
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    runtime_yaml["pricing"] = pricing

    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for index, plan in enumerate(plans):
        if not isinstance(plan, dict):
            continue
        payment_cfg = plan.get("payment") if isinstance(plan.get("payment"), dict) else {}
        plan["payment"] = payment_cfg
        payment_cfg["link"] = link if index == 0 else ""

    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    if catalog:
        catalog_payment = catalog.get("payment") if isinstance(catalog.get("payment"), dict) else {}
        catalog["payment"] = catalog_payment
        catalog_payment["link"] = link

    root_payment = pricing.get("payment") if isinstance(pricing.get("payment"), dict) else {}
    pricing["payment"] = root_payment
    if not plans and not catalog:
        root_payment["link"] = link

    return runtime_yaml


def _sample_transfer_methods() -> list[dict[str, str]]:
    return [
        {"type": "nequi", "number": "3001234567"},
        {"type": "daviplata", "number": "3009876543"},
        {"type": "bank", "bank": "Bancolombia", "account_type": "ahorros", "account_number": "1234567890"},
        {"type": "breb", "reference": "usuario@correo.com"},
    ]


def _set_transfer_methods(runtime_yaml: dict, *, enabled: bool, methods: list[dict[str, str]]) -> dict:
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    runtime_yaml["pricing"] = pricing

    transfer_payload = {
        "enabled": bool(enabled),
        "methods": [dict(method) for method in methods],
    }

    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []
    for plan in plans:
        if not isinstance(plan, dict):
            continue
        payment_cfg = plan.get("payment") if isinstance(plan.get("payment"), dict) else {}
        plan["payment"] = payment_cfg
        payment_cfg["transfer"] = {
            "enabled": transfer_payload["enabled"],
            "methods": [dict(method) for method in transfer_payload["methods"]],
        }

    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    if catalog:
        catalog_payment = catalog.get("payment") if isinstance(catalog.get("payment"), dict) else {}
        catalog["payment"] = catalog_payment
        catalog_payment["transfer"] = {
            "enabled": transfer_payload["enabled"],
            "methods": [dict(method) for method in transfer_payload["methods"]],
        }

    root_payment = pricing.get("payment") if isinstance(pricing.get("payment"), dict) else {}
    pricing["payment"] = root_payment
    root_payment["transfer"] = {
        "enabled": transfer_payload["enabled"],
        "methods": [dict(method) for method in transfer_payload["methods"]],
    }
    return runtime_yaml


def _set_data_collection_fields(runtime_yaml: dict, *, enabled: bool, fields: list[str]) -> dict:
    capabilities = runtime_yaml.get("capabilities") if isinstance(runtime_yaml.get("capabilities"), dict) else {}
    runtime_yaml["capabilities"] = capabilities

    capabilities["data_collection"] = {
        "enabled": bool(enabled),
        "fields": list(fields),
    }

    closing_methods = capabilities.get("closing_methods") if isinstance(capabilities.get("closing_methods"), dict) else {}
    capabilities["closing_methods"] = closing_methods
    current_data_collection = closing_methods.get("data_collection") if isinstance(closing_methods.get("data_collection"), dict) else {}
    closing_methods["data_collection"] = {
        **current_data_collection,
        "enabled": bool(enabled),
    }
    return runtime_yaml


def _set_post_payment_messages(
    runtime_yaml: dict,
    *,
    on_user_report_message: str,
    on_payment_confirmed_message: str,
) -> dict:
    config_section = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    runtime_yaml["config"] = config_section
    config_section["post_payment"] = {
        "on_user_report": {"message": on_user_report_message},
        "on_payment_confirmed": {"message": on_payment_confirmed_message},
    }
    return runtime_yaml


def _disable_initial_message(runtime_yaml: dict) -> dict:
    config_section = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    runtime_yaml["config"] = config_section
    initial_message = config_section.get("initial_message") if isinstance(config_section.get("initial_message"), dict) else {}
    config_section["initial_message"] = initial_message
    initial_message["enabled"] = False
    return runtime_yaml


def _build_prompt(*, tenant_slug: str, runtime_yaml: dict, user_message: str) -> str:
    prompt, _metadata, _context = PromptBuilderService().build(
        client_config_id=tenant_slug,
        user_message=user_message,
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )
    return str(prompt or "")


def _ask_with_prime(*, tenant_slug: str, runtime_yaml: dict, user_message: str, user_id: str) -> str:
    service = AIService()

    service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message="hola",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )

    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message=user_message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )

    return str(response or "").lower()


def _ask_direct_raw(*, tenant_slug: str, runtime_yaml: dict, user_message: str, user_id: str) -> str:
    service = AIService()
    response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message=user_message,
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )
    return str(response or "")


def _ask_sequence_with_prime(*, tenant_slug: str, runtime_yaml: dict, user_messages: list[str], user_id: str) -> list[str]:
    service = AIService()
    history: list[dict[str, str]] = []

    prime_response, _ai_used, _metadata = service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message="hola",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )
    history.extend(
        [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": str(prime_response or "")},
        ]
    )

    replies: list[str] = []
    for message in user_messages:
        response, _ai_used, _metadata = service.generate_business_reply(
            tenant=_tenant(tenant_slug),
            bot_config=None,
            user_message=message,
            conversation_history=list(history),
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        reply = str(response or "").lower()
        replies.append(reply)
        history.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": str(response or "")},
            ]
        )

    return replies


def _ask_with_memory_only(*, tenant_slug: str, runtime_yaml: dict, user_messages: list[str], user_id: str) -> tuple[list[str], AIService]:
    service = AIService()

    service.generate_business_reply(
        tenant=_tenant(tenant_slug),
        bot_config=None,
        user_message="hola",
        conversation_history=[],
        faq_results=[],
        yaml_config=runtime_yaml,
        user_id=user_id,
        include_metadata=True,
    )

    replies: list[str] = []
    for message in user_messages:
        response, _ai_used, _metadata = service.generate_business_reply(
            tenant=_tenant(tenant_slug),
            bot_config=None,
            user_message=message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        replies.append(str(response or "").lower())

    return replies, service


def _detect_closing_methods(text: str) -> set[str]:
    normalized = str(text or "").lower()
    patterns = {
        "link_payment": [r"\blink\b", r"\benlace\b", r"\bpago\b", r"\bpagar\b", r"\bcheckout\b"],
        "human_handoff": [
            r"persona real",
            r"equipo humano",
            r"te paso con",
            r"te comunico con",
            r"te contacta",
            r"te contactará",
            r"te contactara",
            r"te escribe",
            r"te escribirá",
            r"te escribira",
        ],
        "data_collection": [r"\bnombre\b", r"\bcorreo\b", r"\bemail\b", r"\bdirecci[oó]n\b", r"\bdatos?\b"],
    }

    detected: set[str] = set()
    for method_name, method_patterns in patterns.items():
        if any(re.search(pattern, normalized) for pattern in method_patterns):
            detected.add(method_name)
    return detected


def _extract_urls(text: str) -> set[str]:
    return set(re.findall(r"https?://\S+", str(text or ""), flags=re.IGNORECASE))


def _offers_payment_execution(text: str, expected_link: str | None = None) -> bool:
    normalized = str(text or "").lower()
    if expected_link and expected_link in str(text or ""):
        return True
    if _extract_urls(text):
        return True
    execution_patterns = [
        r"puedes pagar al\s+\d{7,}",
        r"puedes transferir a\s+.+\scuenta\s+de\s+(ahorros|corriente)\s+\d{6,}",
        r"puedes pagar por bre-b con la referencia\s+[a-z0-9@._-]{4,}",
        r"puedes hacerlo por aqu[ií]",
    ]
    return any(re.search(pattern, normalized) for pattern in execution_patterns)


def _payment_secrets(runtime_yaml: dict) -> set[str]:
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    secrets: set[str] = set()

    def _collect(raw_payment: object) -> None:
        payment = raw_payment if isinstance(raw_payment, dict) else {}
        link = str(payment.get("link") or "").strip()
        if link:
            secrets.add(link)
        transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
        methods = transfer.get("methods") if isinstance(transfer.get("methods"), list) else []
        for method in methods:
            if not isinstance(method, dict):
                continue
            for key in ("number", "account_number", "reference"):
                value = str(method.get(key) or "").strip()
                if value:
                    secrets.add(value)

    _collect(pricing.get("payment"))
    catalog = pricing.get("catalog") if isinstance(pricing.get("catalog"), dict) else {}
    _collect(catalog.get("payment"))
    for plan in pricing.get("plans") if isinstance(pricing.get("plans"), list) else []:
        if isinstance(plan, dict):
            _collect(plan.get("payment"))

    return secrets


def _contains_any_secret(text: str, secrets: set[str]) -> bool:
    payload = str(text or "")
    return any(secret and secret in payload for secret in secrets)


def _asks_payment_choice(text: str) -> bool:
    normalized = str(text or "").lower()
    has_modes = bool(re.search(r"(enlace|link).*(transfer(?:encia)?)|transfer(?:encia)?.*(enlace|link)", normalized))
    has_choice = any(token in normalized for token in ("prefier", "cuál", "cual", "elige", "te sirve", "?") )
    return has_modes and has_choice


def _is_only_payment_question(text: str) -> bool:
    normalized = " ".join(str(text or "").lower().split())
    return bool(
        re.fullmatch(
            r"(?:puedes\s+)?pagar\s+por\s+(?:enlace|link)\s+o\s+transferencia,?\s*[¿?]?cu[aá]l\s+prefieres\??",
            normalized,
        )
    )


def _has_context_before_payment_choice(text: str) -> bool:
    normalized = " ".join(str(text or "").lower().split())
    match = re.search(r"(enlace|link).*(transfer(?:encia)?)|transfer(?:encia)?.*(enlace|link)", normalized)
    if not match:
        return False

    prefix = normalized[: match.start()].strip(" ,;:.!?¿")
    if len(prefix.split()) < 2:
        return False

    return bool(re.search(r"\b(genial|perfecto|bien|dale|de una|listo|super|avanz|seguir|siguiente|servir|ayudar|resolver|activar|cierre|pedido|proceso|pago)\b", prefix))


def _asks_for_next_payment_step(text: str) -> bool:
    normalized = str(text or "").lower()
    asks_choice = any(token in normalized for token in ("prefier", "cuál", "cual", "elige", "te sirve", "?"))
    mentions_real_method = bool(re.search(r"\benlace\b|\blink\b|\btransfer(?:encia)?\b|\bnequi\b|\bdaviplata\b|\bbancolombia\b|\bbank\b|\bbre-?b\b", normalized))
    return asks_choice and mentions_real_method


def _mentions_payment_topic(text: str) -> bool:
    normalized = str(text or "").lower()
    return bool(re.search(r"\bpago\b|\bpagar\b|\benlace\b|\blink\b|\btransfer", normalized))


def _promises_fake_link(text: str) -> bool:
    normalized = str(text or "").lower()
    fake_link_patterns = [
        r"te env[ií]o el enlace",
        r"te env[ií]o el link",
        r"te comparto el enlace",
        r"te comparto el link",
        r"te mando el enlace",
        r"te mando el link",
        r"te pasar[eé] el enlace",
        r"te pasar[eé] el link",
    ]
    return any(re.search(pattern, normalized) for pattern in fake_link_patterns)


def _detect_requested_data_fields(text: str) -> set[str]:
    normalized = str(text or "").lower()
    patterns = {
        "nombre": [r"\bnombre\b"],
        "telefono": [r"\btel[eé]fono\b", r"\btelefono\b", r"\bcelular\b"],
        "direccion": [r"\bdirecci[oó]n\b", r"\bdireccion\b"],
        "detalles": [r"\bdetalle\b", r"\bdetalles\b"],
        "correo": [r"\bcorreo\b", r"\bemail\b"],
    }
    detected = set()
    for field_name, field_patterns in patterns.items():
        if any(re.search(pattern, normalized) for pattern in field_patterns):
            detected.add(field_name)
    return detected


def _shows_buy_progression(text: str) -> bool:
    normalized = str(text or "").lower()
    progression_patterns = [
        r"\bcontinuar\b",
        r"\bavanzar\b",
        r"\benlace de pago\b",
        r"\bproceder con el pago\b",
        r"\bc[oó]mo te gustar[ií]a proceder\b",
        r"\bte gustar[ií]a proceder\b",
        r"\bproceder\b",
        r"\bactivar el servicio\b",
        r"\bconfirmar tu pedido\b",
        r"\bconfirmar el pedido\b",
        r"\bqué te gustaría pedir\b",
        r"\bque te gustaria pedir\b",
        r"\bqué te gustaría ordenar\b",
        r"\bque te gustaria ordenar\b",
        r"\bordenar\b",
        r"\bpedido\b",
    ]
    return any(re.search(pattern, normalized) for pattern in progression_patterns)


def _shows_post_payment_validation(text: str) -> bool:
    normalized = str(text or "").lower()
    validation_patterns = [
        r"\breviso\b",
        r"\bvalid",
        r"\brecib",
        r"\bte confirmo en un momento\b",
        r"\ben un momento\b",
    ]
    return any(re.search(pattern, normalized) for pattern in validation_patterns)


def _has_false_payment_confirmation(text: str) -> bool:
    normalized = str(text or "").lower()
    forbidden_patterns = [
        r"\bconfirmado\b",
        r"\bya qued[oó]\b",
        r"\bactivad",
    ]
    return any(re.search(pattern, normalized) for pattern in forbidden_patterns)


def _extract_active_methods(prompt_text: str) -> set[str]:
    match = re.search(r"Métodos activos en este negocio:\s*\n([^\n]+)", str(prompt_text or ""))
    if not match:
        return set()

    return {
        item.strip()
        for item in match.group(1).split(",")
        if item.strip() and item.strip() != "sin métodos de cierre activos"
    }


def _paragraph_blocks(text: str) -> list[str]:
    normalized = str(text or "").strip()
    if not normalized:
        return []
    return [block.strip() for block in re.split(r"\n\s*\n+", normalized) if block.strip()]


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def _average_line_length(text: str) -> float:
    lines = _non_empty_lines(text)
    if not lines:
        return 0.0
    return sum(len(line) for line in lines) / len(lines)


def test_single_closing_method_used() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )

    prompt, _metadata, _context = PromptBuilderService().build(
        client_config_id="asesor_ai_prod",
        user_message="quiero comprar ya",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    prompt_text = str(prompt or "")
    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero comprar ya",
        user_id=f"closing-single-{uuid4().hex[:8]}",
    )
    detected = _detect_closing_methods(reply)

    assert "MÉTODOS DE CIERRE DISPONIBLES:" in prompt_text
    assert _extract_active_methods(prompt_text) == {"link_payment", "human_handoff", "data_collection"}
    assert has_forward_intent(reply) or bool(detected)
    assert len(detected) <= 1


def test_respects_enabled_closing_methods() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "restaurant",
        {
            "link_payment": False,
            "human_handoff": True,
            "data_collection": False,
        },
    )

    prompt, _metadata, _context = PromptBuilderService().build(
        client_config_id="restaurant",
        user_message="necesito ayuda con esto",
        yaml_config=runtime_yaml,
        faq_results=[],
        progression_rules=None,
    )

    reply = _ask_with_prime(
        tenant_slug="restaurant",
        runtime_yaml=runtime_yaml,
        user_message="necesito ayuda con esto",
        user_id=f"closing-enabled-{uuid4().hex[:8]}",
    )

    assert _extract_active_methods(str(prompt or "")) == {"human_handoff"}
    assert _detect_closing_methods(reply).issubset({"human_handoff"})


def test_closing_triggered_on_buy_intent() -> None:
    for tenant_slug in ("asesor_ai_prod", "restaurant"):
        runtime_yaml = _runtime_with_closing_methods(
            tenant_slug,
            {
                "link_payment": True,
                "human_handoff": True,
                "data_collection": True,
            },
        )

        reply = _ask_with_prime(
            tenant_slug=tenant_slug,
            runtime_yaml=runtime_yaml,
            user_message="quiero comprar",
            user_id=f"closing-buy-{tenant_slug}-{uuid4().hex[:8]}",
        )

        assert reply.strip()
        assert _shows_buy_progression(reply) or bool(_detect_closing_methods(reply)) or has_forward_intent(reply) or "?" in reply


def test_no_forced_data_collection() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )

    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero comprar ya",
        user_id=f"closing-no-data-{uuid4().hex[:8]}",
    )

    assert has_forward_intent(reply) or bool(_detect_closing_methods(reply))
    assert "nombre" not in reply
    assert "correo" not in reply
    assert "email" not in reply
    assert "direccion" not in reply
    assert "dirección" not in reply
    assert "datos" not in reply


def test_link_only_if_exists() -> None:
    with_link_runtime = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(with_link_runtime, link=expected_link)
    _set_transfer_methods(with_link_runtime, enabled=False, methods=[])

    without_link_runtime = _runtime_with_closing_methods(
        "restaurant",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_payment_link(without_link_runtime, link="")
    _set_transfer_methods(without_link_runtime, enabled=False, methods=[])

    with_link_prompt = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=with_link_runtime,
        user_message="ya quiero pagar",
    )
    without_link_prompt = _build_prompt(
        tenant_slug="restaurant",
        runtime_yaml=without_link_runtime,
        user_message="ya quiero pagar",
    )

    with_link_reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=with_link_runtime,
        user_message="ya quiero pagar",
        user_id=f"closing-link-on-{uuid4().hex[:8]}",
    )
    without_link_reply = _ask_with_prime(
        tenant_slug="restaurant",
        runtime_yaml=without_link_runtime,
        user_message="ya quiero pagar",
        user_id=f"closing-link-off-{uuid4().hex[:8]}",
    )

    assert expected_link in with_link_prompt
    assert "LINK_AVAILABLE: true" in with_link_prompt
    assert "TRANSFER_AVAILABLE: false" in with_link_prompt
    assert "sin links de pago definidos" in without_link_prompt
    assert "LINK_AVAILABLE: false" in without_link_prompt
    assert "TRANSFER_AVAILABLE: false" in without_link_prompt
    assert expected_link not in with_link_reply
    assert not _extract_urls(with_link_reply)
    assert not _offers_payment_execution(without_link_reply)


def test_data_collection_uses_defined_fields() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "restaurant",
        {
            "link_payment": False,
            "human_handoff": False,
            "data_collection": True,
        },
    )
    _set_payment_link(runtime_yaml, link="")
    _set_data_collection_fields(runtime_yaml, enabled=True, fields=["direccion", "detalles"])

    prompt_text = _build_prompt(
        tenant_slug="restaurant",
        runtime_yaml=runtime_yaml,
        user_message="quiero avanzar con domicilio",
    )
    reply = _ask_with_prime(
        tenant_slug="restaurant",
        runtime_yaml=runtime_yaml,
        user_message="quiero avanzar con domicilio",
        user_id=f"closing-fields-{uuid4().hex[:8]}",
    )

    detected_fields = _detect_requested_data_fields(reply)

    assert "Campos definidos para pedir al cliente:" in prompt_text
    assert "direccion, detalles" in prompt_text
    assert "telefono" not in prompt_text
    assert detected_fields.issubset({"direccion", "detalles"})


def test_no_fake_payment_promises() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_payment_link(runtime_yaml, link="")
    _set_transfer_methods(runtime_yaml, enabled=False, methods=[])

    prompt_text = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="ya quiero pagar",
    )
    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="ya quiero pagar",
        user_id=f"closing-no-fake-{uuid4().hex[:8]}",
    )

    assert "sin links de pago definidos" in prompt_text
    assert not _promises_fake_link(reply)
    assert not _extract_urls(reply)


def test_runtime_loader_preserves_payment_link_from_pricing_yaml() -> None:
    runtime_yaml = load_tenant_runtime_yaml("asesor_ai_prod", channel="whatsapp")
    pricing = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}
    plans = pricing.get("plans") if isinstance(pricing.get("plans"), list) else []

    links = []
    root_link = str(((pricing.get("payment") or {}).get("link")) or "").strip()
    if root_link:
        links.append(root_link)

    catalog_link = str((((pricing.get("catalog") or {}).get("payment") or {}).get("link")) or "").strip()
    if catalog_link:
        links.append(catalog_link)

    for plan in plans:
        if not isinstance(plan, dict):
            continue
        plan_link = str(((plan.get("payment") or {}).get("link")) or "").strip()
        if plan_link:
            links.append(plan_link)

    assert "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico" in links
    assert isinstance(((plans[0].get("payment") or {}).get("transfer") or {}).get("methods"), list)
    assert ((plans[0].get("payment") or {}).get("transfer") or {}).get("enabled") is True
    assert any(
        isinstance(item, dict) and str(item.get("type") or "").strip().lower() == "nequi"
        for item in (((plans[0].get("payment") or {}).get("transfer") or {}).get("methods") or [])
    )


def test_no_payment_data_without_selection() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(runtime_yaml, link=expected_link)
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())
    secrets = _payment_secrets(runtime_yaml)

    prompt_text = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="que venden",
    )
    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="que venden",
        user_id=f"payment-no-selection-{uuid4().hex[:8]}",
    )

    assert "LINK_AVAILABLE: true" in prompt_text
    assert "TRANSFER_AVAILABLE: true" in prompt_text
    assert not _contains_any_secret(reply, secrets)


def test_payment_flow_requires_selection() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(runtime_yaml, link=expected_link)
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())

    prompt_text = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
    )
    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
        user_id=f"payment-choice-{uuid4().hex[:8]}",
    )

    assert "NO muestres links, números, cuentas ni referencias sin elección explícita del usuario." in prompt_text
    assert _asks_for_next_payment_step(reply)
    assert not _extract_urls(reply)
    assert "3001234567" not in reply
    assert "3009876543" not in reply
    assert "1234567890" not in reply


def test_payment_executes_after_selection() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(runtime_yaml, link=expected_link)
    transfer_methods = _sample_transfer_methods()
    _set_transfer_methods(runtime_yaml, enabled=True, methods=transfer_methods)
    nequi_number = transfer_methods[0]["number"]
    all_secrets = _payment_secrets(runtime_yaml)

    prompt_text = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
    )
    first_reply, second_reply = _ask_sequence_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_messages=["quiero pagar", "nequi"],
        user_id=f"payment-exec-{uuid4().hex[:8]}",
    )

    assert "SOLO ejecuta el pago cuando el usuario elige explícitamente link, nequi, daviplata, bank o breb." in prompt_text
    assert _asks_for_next_payment_step(first_reply)
    assert nequi_number in second_reply
    assert expected_link not in second_reply
    assert all(secret not in second_reply for secret in all_secrets if secret not in {nequi_number})


def test_payment_respects_yaml() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_payment_link(runtime_yaml, link="")
    bank_only_methods = [
        {"type": "bank", "bank": "Bancolombia", "account_type": "ahorros", "account_number": "1234567890"},
    ]
    _set_transfer_methods(runtime_yaml, enabled=True, methods=bank_only_methods)
    secrets = _payment_secrets(runtime_yaml)

    prompt_text = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
    )
    first_reply, second_reply = _ask_sequence_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_messages=["quiero pagar", "pásame el nequi"],
        user_id=f"payment-yaml-{uuid4().hex[:8]}",
    )

    assert "LINK_AVAILABLE: false" in prompt_text
    assert "TRANSFER_AVAILABLE: true" in prompt_text
    assert "- bank: bancolombia / ahorros / 1234567890" in prompt_text.lower()
    assert "- nequi:" not in prompt_text.lower()
    assert "- daviplata:" not in prompt_text.lower()
    assert "- breb:" not in prompt_text.lower()
    assert "enlace" not in first_reply and "link" not in first_reply
    assert not _contains_any_secret(second_reply, secrets - {"1234567890"})
    assert "3001234567" not in second_reply
    assert not _extract_urls(second_reply)


def test_no_mixed_payment_execution() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    transfer_methods = _sample_transfer_methods()
    _set_payment_link(runtime_yaml, link=expected_link)
    _set_transfer_methods(runtime_yaml, enabled=True, methods=transfer_methods)

    first_reply, second_reply = _ask_sequence_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_messages=["quiero pagar", "dame el link"],
        user_id=f"payment-no-mix-{uuid4().hex[:8]}",
    )

    assert _asks_for_next_payment_step(first_reply)
    assert expected_link in second_reply
    assert "3001234567" not in second_reply
    assert "3009876543" not in second_reply
    assert "1234567890" not in second_reply
    assert "usuario@correo.com" not in second_reply


def test_no_legacy_payment_methods() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_payment_link(runtime_yaml, link="")
    bank_only_methods = [
        {"type": "bank", "bank": "Bancolombia", "account_type": "ahorros", "account_number": "1234567890"},
    ]
    _set_transfer_methods(runtime_yaml, enabled=True, methods=bank_only_methods)

    prompt_text = _build_prompt(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
    )
    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="transferencia",
        user_id=f"payment-no-legacy-{uuid4().hex[:8]}",
    )

    assert "payment_methods" not in prompt_text
    assert "- nequi:" not in prompt_text.lower()
    assert "- daviplata:" not in prompt_text.lower()
    assert "3001234567" not in reply
    assert "3009876543" not in reply
    assert "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico" not in reply


def test_payment_message_has_progress_context() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )

    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(runtime_yaml, link=expected_link)
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())

    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
        user_id=f"payment-progress-{uuid4().hex[:8]}",
    )

    assert _asks_for_next_payment_step(reply)
    assert not _is_only_payment_question(reply)
    assert has_forward_intent(reply) or _shows_buy_progression(reply)


def test_payment_message_is_not_passive_or_empty() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )

    _set_payment_link(runtime_yaml, link="")
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())

    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
        user_id=f"payment-natural-{uuid4().hex[:8]}",
    )

    assert reply.strip()
    assert len(reply.split()) >= 8
    assert _asks_for_next_payment_step(reply)
    assert not _is_only_payment_question(reply)
    assert has_forward_intent(reply) or _shows_buy_progression(reply) or _asks_for_next_payment_step(reply)


def test_user_reports_payment_flow() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_post_payment_messages(
        runtime_yaml,
        on_user_report_message="Perfecto, ya lo reviso y te confirmo en un momento para continuar.",
        on_payment_confirmed_message="Listo, ya quedó confirmado. Ahora seguimos con el siguiente paso.",
    )

    reply = _ask_with_prime(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="te mandé el comprobante",
        user_id=f"payment-report-{uuid4().hex[:8]}",
    )

    assert reply.strip()
    assert _shows_post_payment_validation(reply)
    assert "confirmado" not in reply
    assert "listo" not in reply
    assert "activado" not in reply


def test_no_false_payment_confirmation() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "restaurant",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_post_payment_messages(
        runtime_yaml,
        on_user_report_message="Perfecto, ya lo reviso y te confirmo en un momento para continuar.",
        on_payment_confirmed_message="Listo, ya quedó confirmado. Ahora seguimos con el siguiente paso.",
    )
    secrets = _payment_secrets(runtime_yaml)

    reply = _ask_with_prime(
        tenant_slug="restaurant",
        runtime_yaml=runtime_yaml,
        user_message="ya pagué",
        user_id=f"payment-no-confirm-{uuid4().hex[:8]}",
    )

    assert reply.strip()
    assert _shows_post_payment_validation(reply)
    assert not _has_false_payment_confirmation(reply)
    assert not _offers_payment_execution(reply)
    assert not _contains_any_secret(reply, secrets)


def test_memory_payment_progression() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _set_post_payment_messages(
        runtime_yaml,
        on_user_report_message="Perfecto, ya lo reviso y te confirmo en un momento para continuar.",
        on_payment_confirmed_message="Listo, ya quedó confirmado. Ahora seguimos con el siguiente paso.",
    )
    _set_payment_link(runtime_yaml, link="https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico")
    transfer_methods = _sample_transfer_methods()
    _set_transfer_methods(runtime_yaml, enabled=True, methods=transfer_methods)
    user_id = f"payment-memory-{uuid4().hex[:8]}"

    replies, service = _ask_with_memory_only(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_messages=["quiero pagar", "nequi", "ya pagué"],
        user_id=user_id,
    )
    first_reply, second_reply, third_reply = replies

    assert _asks_for_next_payment_step(first_reply)
    assert transfer_methods[0]["number"] in second_reply
    assert _shows_post_payment_validation(third_reply)
    assert not _has_false_payment_confirmation(third_reply)
    assert not _asks_for_next_payment_step(third_reply)

    memory = service.pipeline.memory_repository.get_memory("asesor_ai_prod", user_id)
    assert memory.get("intent_detectado") == "buy"
    assert memory.get("metodo_pago_elegido") == "nequi"
    assert memory.get("estado_pago") == "reportado"


def test_payment_always_requires_selection() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _disable_initial_message(runtime_yaml)
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(runtime_yaml, link=expected_link)
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())

    reply = _ask_direct_raw(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
        user_id=f"payment-strict-{uuid4().hex[:8]}",
    ).lower()

    assert _asks_for_next_payment_step(reply)
    assert expected_link not in reply
    assert "3001234567" not in reply
    assert "3009876543" not in reply
    assert "1234567890" not in reply


def test_payment_consistent_after_reset() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _disable_initial_message(runtime_yaml)
    expected_link = "https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico"
    _set_payment_link(runtime_yaml, link=expected_link)
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())

    reply = _ask_direct_raw(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="quiero pagar",
        user_id=f"payment-reset-{uuid4().hex[:8]}",
    ).lower()

    assert _asks_for_next_payment_step(reply)
    assert expected_link not in reply
    assert "3001234567" not in reply
    assert "3009876543" not in reply
    assert "1234567890" not in reply


def test_post_payment_exact_message() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _disable_initial_message(runtime_yaml)
    expected_message = "Perfecto, ya lo reviso y te confirmo en un momento para continuar."
    _set_post_payment_messages(
        runtime_yaml,
        on_user_report_message=expected_message,
        on_payment_confirmed_message="Listo, ya quedó confirmado. Ahora seguimos con el siguiente paso.",
    )

    reply = _ask_direct_raw(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="ya pagué",
        user_id=f"payment-post-exact-{uuid4().hex[:8]}",
    ).strip()

    assert reply == expected_message


def test_post_payment_not_modified() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _disable_initial_message(runtime_yaml)
    _set_post_payment_messages(
        runtime_yaml,
        on_user_report_message="Perfecto, ya lo reviso y te confirmo en un momento para continuar.",
        on_payment_confirmed_message="Listo, ya quedó confirmado. Ahora seguimos con el siguiente paso.",
    )

    reply = _ask_direct_raw(
        tenant_slug="asesor_ai_prod",
        runtime_yaml=runtime_yaml,
        user_message="ya pagué",
        user_id=f"payment-post-intact-{uuid4().hex[:8]}",
    ).strip()

    assert not reply.startswith("Hola")


def test_response_format_professional() -> None:
    runtime_yaml = _runtime_with_closing_methods(
        "asesor_ai_prod",
        {
            "link_payment": True,
            "human_handoff": True,
            "data_collection": True,
        },
    )
    _disable_initial_message(runtime_yaml)
    _set_payment_link(runtime_yaml, link="https://checkout.aisalesengine.com/asesor-ai-prod/plan-basico")
    _set_transfer_methods(runtime_yaml, enabled=True, methods=_sample_transfer_methods())

    replies = [
        _ask_direct_raw(
            tenant_slug="asesor_ai_prod",
            runtime_yaml=runtime_yaml,
            user_message=message,
            user_id=f"format-professional-{index}-{uuid4().hex[:8]}",
        )
        for index, message in enumerate(["que vendes", "como funciona", "quiero pagar"], start=1)
    ]

    for reply in replies:
        assert reply.strip()
        assert "\n\n\n" not in reply
        assert len(_paragraph_blocks(reply)) <= 2
        assert _average_line_length(reply) > 40
