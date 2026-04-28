##### 🚨 CRITICAL FILE — PARSER ONLY #####
# Este archivo NO toma decisiones.
#
# ❌ PROHIBIDO:
# - inferir intent
# - heurísticas
# - clasificar mensajes
#
# ❌ NUNCA agregar:
# - infer_intent_fallback
# - if por texto del usuario
#
# SOLO:
# - parsear salida del modelo
# - normalizar metadata
#
# Si el intent viene vacío:
# → NO se corrige aquí
########################################

##### 🚨 DO NOT PATCH BEHAVIOR #####
# Este sistema es AI-FIRST.
#
# ❌ NO:
# - modificar respuestas manualmente
# - agregar lógica condicional de venta
# - parchear outputs
#
# ✅ SI:
# - mejorar contexto
# - mejorar instrucciones a la IA
#
# Si un test falla:
# -> corregir contexto o prompt
# -> NO tocar respuesta final
################################

##### 🧠 SYSTEM OVERVIEW #####
# Sistema SaaS multi-tenant AI-first de ventas conversacionales.
#
# Flujo:
# usuario -> prompt_builder -> IA -> structured_output -> respuesta
#
# La IA es responsable de:
# - entender intención
# - generar respuesta
# - ejecutar venta
#
# El código SOLO:
# - pasa contexto
# - orquesta flujo
#
################################

##### 🚨 AI-FIRST RULE #####
# ❌ PROHIBIDO:
# - lógica comercial en código
# - heurísticas por palabras
# - forzar respuestas
# - if/else por intent
#
# ✅ PERMITIDO:
# - pasar datos
# - estructurar contexto
#
################################

##### 🧠 SINGLE SOURCE OF TRUTH #####
# Único lugar donde se define el intent.
#
# ❌ NADIE MÁS puede modificar intent
################################

##### 🚨 INTENT CONTRACT #####
# Este archivo es la única fuente de verdad del intent.
#
# ❌ PROHIBIDO:
# - inferir intent por texto
# - usar heurísticas
# - re-clasificar intent
#
# Si no hay intent claro:
# -> dejarlo vacío
# -> NO inventar
################################

##### ⚠️ ANTI-PATTERNS #####
# NO hacer:
# - if intent == "buy"
# - detectar "quiero"
# - agregar textos manuales de cierre
# - concatenar respuestas
#
# Si haces esto:
# 👉 rompes AI-first
################################

##### ⚠️ MULTI-TENANT #####
# Esto es MULTI-TENANT.
#
# NO escribir nada específico de un negocio.
# NO mencionar productos.
# NO hardcodear comportamiento.
#
# Esto debe funcionar para cualquier YAML.
################################

##### 🧠 AI-FIRST ENFORCEMENT #####
# La IA es la única que decide:
#
# - intent
# - respuesta
# - flujo de conversación
#
# ❌ PROHIBIDO en código:
# - clasificar intent
# - usar heurísticas
# - usar if/else por intención
# - modificar respuestas manualmente
#
# ✅ El código SOLO:
# - pasa contexto
# - orquesta flujo
# - valida estado
#
# Si algo falla:
# → se corrige el prompt
# → NO el código
################################
from __future__ import annotations

import json

from app.utils.logger import logger


VALID_INTENTS = {"pain", "info", "objection", "buy"}


class StructuredOutputResult(dict):
    def __iter__(self):
        yield self.get("_legacy_response", self.get("response"))
        legacy_metadata = self.get("_legacy_metadata")
        if isinstance(legacy_metadata, dict):
            yield legacy_metadata
            return
        metadata = self.get("ai_metadata")
        yield metadata if isinstance(metadata, dict) else {}


def _build_result(
    *,
    valid: bool,
    raw_text: str,
    error: str | None,
    intent: str | None,
    response: str | None,
    ai_metadata: dict,
    legacy_response: str | None = None,
    legacy_metadata: dict | None = None,
) -> StructuredOutputResult:
    payload = StructuredOutputResult({
        "valid": bool(valid),
        "error": str(error or "").strip().lower() or None,
        "intent": str(intent or "").strip().lower(),
        "raw_text": str(raw_text or "").strip(),
        "response": response,
        "ai_metadata": ai_metadata if isinstance(ai_metadata, dict) else {},
    })
    if legacy_response is not None:
        payload["_legacy_response"] = legacy_response
    if isinstance(legacy_metadata, dict):
        payload["_legacy_metadata"] = legacy_metadata
    return payload


def _invalid_result(
    *,
    raw_text: str,
    error: str,
    intent: str | None = None,
    legacy_response: str | None = None,
    legacy_metadata: dict | None = None,
) -> StructuredOutputResult:
    return _build_result(
        valid=False,
        raw_text=raw_text,
        error=error,
        intent=intent,
        response=None,
        ai_metadata={},
        legacy_response=legacy_response,
        legacy_metadata=legacy_metadata,
    )


def _strip_code_fence(raw: str) -> str:
    text = str(raw or "").strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _extract_json_candidate(raw: str) -> str:
    text = _strip_code_fence(raw)
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "si"}


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_metadata(raw_metadata: dict | None) -> dict:
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    return {
        "intent": str(metadata.get("intent") or "").strip().lower(),
        "stage": str(metadata.get("stage") or "").strip().lower(),
        "pain_detected": _as_bool(metadata.get("pain_detected")),
        "pain": str(metadata.get("pain") or "").strip(),
        "next_step": str(metadata.get("next_step") or "").strip(),
        "urgency": str(metadata.get("urgency") or "").strip().lower(),
        "last_cta": str(metadata.get("last_cta") or "").strip(),
        "objection_count": max(0, _as_int(metadata.get("objection_count"), 0)),
        "mode": str(metadata.get("mode") or "").strip().lower(),
        "payment_method": str(metadata.get("payment_method") or "").strip().lower(),
        "payment_status": str(metadata.get("payment_status") or "").strip().lower(),
    }


def parse_structured_output(raw_text: str) -> StructuredOutputResult:
    text = str(raw_text or "").strip()
    if not text:
        logger.info("structured_output_audit", extra={"raw_text": text, "response_text": "", "error": "empty_output"})
        return _invalid_result(
            raw_text=text,
            error="empty_output",
            legacy_response="",
            legacy_metadata={"intent": "", "intent_missing": True},
        )

    candidate = _extract_json_candidate(text)
    parsed = None
    try:
        parsed = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = None

    if not isinstance(parsed, dict):
        logger.info("structured_output_audit", extra={"raw_text": text, "response_text": "", "error": "invalid_json"})
        return _invalid_result(
            raw_text=text,
            error="invalid_json",
            legacy_response=text,
            legacy_metadata={"intent": "", "intent_missing": True},
        )

    response = str(
        parsed.get("response")
        or parsed.get("reply")
        or parsed.get("text")
        or parsed.get("message")
        or parsed.get("content")
        or ""
    ).strip()

    top_level_metadata = {
        "intent": parsed.get("intent"),
        "stage": parsed.get("stage"),
        "pain_detected": parsed.get("pain_detected"),
        "pain": parsed.get("pain"),
        "next_step": parsed.get("next_step"),
        "urgency": parsed.get("urgency"),
        "last_cta": parsed.get("last_cta"),
        "objection_count": parsed.get("objection_count"),
        "mode": parsed.get("mode"),
        "payment_method": parsed.get("payment_method"),
        "payment_status": parsed.get("payment_status"),
    }
    metadata_payload = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
    metadata = normalize_metadata({**top_level_metadata, **metadata_payload})
    intent = str(metadata.get("intent") or "").strip().lower()

    if intent not in VALID_INTENTS:
        logger.info(
            "structured_output_audit",
            extra={"raw_text": text, "response_text": "", "error": "invalid_intent", "intent": intent},
        )
        legacy_metadata = dict(metadata)
        if not str(intent or "").strip():
            legacy_metadata["intent_missing"] = True
        return _invalid_result(
            raw_text=text,
            error="invalid_intent",
            intent=intent,
            legacy_response=response or text,
            legacy_metadata=legacy_metadata,
        )

    if not response:
        logger.info(
            "structured_output_audit",
            extra={"raw_text": text, "response_text": "", "error": "missing_response", "intent": intent},
        )
        return _invalid_result(
            raw_text=text,
            error="missing_response",
            intent=intent,
            legacy_response=text,
            legacy_metadata=dict(metadata),
        )

    metadata["intent"] = intent

    logger.info("structured_output_audit", extra={"raw_text": text, "response_text": response, "intent": intent})
    return _build_result(
        valid=True,
        raw_text=text,
        error=None,
        intent=intent,
        response=response,
        ai_metadata=metadata,
    )