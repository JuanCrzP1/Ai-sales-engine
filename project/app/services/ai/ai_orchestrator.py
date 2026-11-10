##### 🚨 ORCHESTRATION ONLY #####
# Este módulo NO piensa.
#
# ❌ PROHIBIDO:
# - alterar intent
# - modificar respuesta
#
# SOLO:
# - construir prompt
# - llamar modelo
# - devolver resultado
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

##### 💬 HUMAN SALES STYLE #####
# Las respuestas DEBEN sonar como una persona real vendiendo por chat.
#
# NO usar:
# - "este sistema..."
# - "esto te permite..."
# - "nuestra solución..."
# - lenguaje técnico o estructurado
#
# SÍ usar:
# - lenguaje natural
# - frases conversacionales
# - conectores humanos (mira, vea, es que, la idea es)
# - enfoque en problema antes que solución
#
# La respuesta debe sentirse como un chat real,
# no como una descripción.
################################
from __future__ import annotations

import json
import re

from app.services.ai.output_contract import system_prompt
from app.services.ai.structured_output import parse_structured_output
from app.utils.logger import logger

# Cuando el modelo no devuelve una respuesta utilizable. No se repite la llamada: repetirla duplicaba el gasto de tokens del
# negocio por un formato, y el cliente recibe este mensaje en lugar de un JSON o un texto vacío.
FAILED_REPLY = "Hubo un problema procesando el mensaje. Intenta de nuevo."
# El valor de `response` en un JSON incompleto (por ejemplo, cortado por el límite de tokens).
_RESPONSE_FIELD = re.compile(r'"response"\s*:\s*("(?:[^"\\]|\\.)*")')


def _usable_reply(result) -> str:
    """La respuesta del modelo aunque no haya cumplido todo el formato, sin inventar nada: el texto que escribió para el cliente.

    - JSON con respuesta pero sin una intención válida: la respuesta, sin intención.
    - Texto sin JSON: ese texto (el modelo ignoró el formato y escribió el mensaje).
    - JSON roto: el valor completo de `response`, si está; si no, nada.
    """
    error = str(result.get("error") or "")
    raw = str(result.get("raw_text") or "").strip()
    if error == "invalid_intent":
        reply = str(result.get("_legacy_response") or "").strip()
        return "" if reply == raw and raw.startswith("{") else reply
    if error != "invalid_json":
        return ""
    if "{" not in raw:
        return raw
    match = _RESPONSE_FIELD.search(raw)
    if match is None:
        return ""
    try:
        return str(json.loads(match.group(1))).strip()
    except ValueError:
        return ""


class AIOrchestrator:
    """Orquestador delgado: arma las instrucciones, hace una sola llamada al modelo y devuelve su respuesta."""

    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs

    def generate_business_reply(
        self,
        service,
        *,
        tenant,
        bot_config,
        user_message: str,
        conversation_history: list,
        faq_results: list[dict],
        yaml_config: dict | None = None,
        preamble: str = "",
    ) -> tuple[str, bool, dict]:
        del conversation_history
        prompt, _prompt_metadata, _minimal_context = service._build_prompt(
            tenant=tenant,
            user_message=user_message,
            yaml_config=yaml_config,
            faq_results=faq_results,
        )
        raw_text = service.generate(system_prompt(prompt, preamble=preamble), user_message=user_message, bot_config=bot_config)
        result = parse_structured_output(str(raw_text or ""))
        tenant_slug = str(getattr(tenant, "slug", "") or "")

        if bool(result.get("valid")):
            metadata = result.get("ai_metadata") if isinstance(result.get("ai_metadata"), dict) else {}
            logger.info("ai_reply", extra={"tenant": tenant_slug, "intent": result.get("intent"), "format": "ok"})
            return str(result.get("response") or ""), True, dict(metadata)

        # Sin datos del cliente en los registros: solo qué falló del formato.
        error = str(result.get("error") or "invalid_llm_output")
        reply = _usable_reply(result)
        if reply:
            legacy = result.get("_legacy_metadata") if isinstance(result.get("_legacy_metadata"), dict) else {}
            metadata = {**legacy, "intent": "", "intent_missing": True, "format_error": error}
            logger.warning("ai_reply", extra={"tenant": tenant_slug, "intent": "", "format": error})
            return reply, True, metadata

        logger.warning("ai_reply_unusable", extra={"tenant": tenant_slug, "format": error})
        return FAILED_REPLY, False, {"intent": None, "response": FAILED_REPLY, "error": "invalid_llm_output"}
