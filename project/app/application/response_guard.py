from __future__ import annotations

import re


CATALOG_FORBIDDEN_TERMS = (
    "sistema",
    "implementación",
    "software",
    "automatización",
)

SAAS_FORBIDDEN_TERMS = (
    "hamburguesa",
    "producto físico",
    "comida",
    "bebida",
)

SERVICE_FORBIDDEN_TERMS = (
    "hamburguesa",
    "comida",
    "bebida",
)

PLAN_MENTION_RE = re.compile(
    r"\bplan\s+[a-záéíóúñ0-9_-]+(?:\s+[a-záéíóúñ0-9_-]+){0,3}",
    re.IGNORECASE,
)


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _normalize_spaces(text: str) -> str:
    text = str(text or "")

    # Mantener saltos de línea, solo limpiar espacios internos
    text = re.sub(r"[ \t]+", " ", text)

    # Limpiar espacios antes de puntuación
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    # Normalizar saltos de línea (máximo 2 seguidos)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _detect_business_model(yaml_config: dict) -> str:
    pricing = _as_dict(_as_dict(yaml_config).get("pricing"))
    catalog = pricing.get("catalog")

    if isinstance(catalog, dict) and any(bool(value) for value in catalog.values()):
        return "catalog"

    plans = pricing.get("plans")
    if plans:
        return "saas"

    return "service"


def _allowed_plan_names(pricing: dict) -> tuple[list[str], list[str]]:
    original_names: list[str] = []
    normalized_names: list[str] = []

    for plan in _as_list(pricing.get("plans")):
        if not isinstance(plan, dict):
            continue
        name = str(plan.get("name") or "").strip()
        if not name:
            continue
        original_names.append(name)
        normalized_names.append(name.lower())

    return original_names, normalized_names


def _clean_invalid_plan_mentions(response: str, pricing: dict) -> str:
    original_names, allowed_names = _allowed_plan_names(pricing)
    if "plan" not in response.lower():
        return response

    replacement = original_names[0] if len(original_names) == 1 else "los planes disponibles"

    def _replace(match: re.Match[str]) -> str:
        mention = str(match.group(0) or "").strip()
        mention_lower = mention.lower()
        if not allowed_names:
            return "las opciones disponibles"
        if mention_lower in allowed_names:
            return mention
        return replacement

    return PLAN_MENTION_RE.sub(_replace, response)


def _remove_forbidden_terms(response: str, forbidden_terms: tuple[str, ...]) -> str:
    updated = response
    for term in forbidden_terms:
        pattern = rf"\b{re.escape(term)}\w*\b"
        updated = re.sub(pattern, "", updated, flags=re.IGNORECASE)
    return updated


def validate_response_against_yaml(response: str, yaml_config: dict) -> str:
    text = str(response or "")
    if not text.strip():
        return ""

    # DESACTIVADO: las mutaciones de texto interfieren con la decisión de la IA.
    # Se mantiene solo la validación técnica (respuesta vacía).
    #
    # payload = _as_dict(yaml_config)
    # pricing = _as_dict(payload.get("pricing"))
    # model = _detect_business_model(payload)
    #
    # cleaned = _clean_invalid_plan_mentions(text, pricing)
    # cleaned = _fix_payment_negations(cleaned, pricing)
    #
    # if model == "catalog":
    #     cleaned = _remove_forbidden_terms(cleaned, CATALOG_FORBIDDEN_TERMS)
    # elif model == "saas":
    #     cleaned = _remove_forbidden_terms(cleaned, SAAS_FORBIDDEN_TERMS)
    # else:
    #     cleaned = _remove_forbidden_terms(cleaned, SERVICE_FORBIDDEN_TERMS)
    #     original_names, allowed_names = _allowed_plan_names(pricing)
    #     if not allowed_names:
    #         cleaned = PLAN_MENTION_RE.sub("las opciones disponibles", cleaned)

    return _normalize_spaces(text)
