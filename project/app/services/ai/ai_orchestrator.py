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

from app.services.ai.structured_output import parse_structured_output
from app.utils.logger import logger


RETRY_OUTPUT_CONTRACT = """
Devuelve SOLO un JSON valido con esta estructura:
{"response":"texto para el usuario","intent":"pain|info|objection|buy","metadata":{}}
No agregues texto fuera del JSON.
Mantén una respuesta natural, útil y orientada al siguiente paso.
Si aplica, incluye en metadata payment_method y payment_status.
""".strip()


class AIOrchestrator:
    """Orquestador delgado: construye prompt, invoca runtime LLM y retorna texto."""

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
    ) -> tuple[str, bool, dict]:
        del conversation_history
        prompt, _prompt_metadata, _minimal_context = service._build_prompt(
            tenant=tenant,
            user_message=user_message,
            yaml_config=yaml_config,
            faq_results=faq_results,
        )
        raw_text = service.generate(prompt, user_message=user_message, bot_config=bot_config)
        result = parse_structured_output(str(raw_text or ""))
        if not bool(result.get("valid")):
            retry_prompt = f"{str(prompt or '').strip()}\n\n{RETRY_OUTPUT_CONTRACT}".strip()
            raw_text = service.generate(retry_prompt, user_message=user_message, bot_config=bot_config)
            result = parse_structured_output(str(raw_text or ""))

        if not bool(result.get("valid")):
            response_text = "Hubo un problema procesando el mensaje. Intenta de nuevo."
            metadata = {
                "intent": None,
                "response": response_text,
                "error": "invalid_llm_output",
            }
            logger.info(
                "orchestrator_parser_audit",
                extra={
                    "raw_text": str(raw_text or "").strip(),
                    "response_text": response_text,
                    "error": str(result.get("error") or "invalid_llm_output").strip().lower(),
                },
            )
            return response_text, False, metadata

        response_text = str(result.get("response") or "")
        metadata = result.get("ai_metadata") if isinstance(result.get("ai_metadata"), dict) else {}
        logger.info(
            "orchestrator_parser_audit",
            extra={
                "raw_text": str(raw_text or "").strip(),
                "response_text": str(response_text or "").strip(),
            },
        )
        return str(response_text or ""), True, metadata if isinstance(metadata, dict) else {}
