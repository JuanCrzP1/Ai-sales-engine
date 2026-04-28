from __future__ import annotations


# ⚠️ AI-FIRST RULE:
# Nunca reescribir respuestas de la IA.
# Este sistema no usa validacion por palabras.
# La IA es la que decide el contenido.
class IntentDomainService:
    """Intent facade kept for compatibility in AI-first mode."""

    INTENTS = (
        "greeting",
        "open_question",
        "info",
        "pain",
        "objection",
        "buy",
    )

    @staticmethod
    def detect(user_message: str) -> str:
        del user_message
        return "open_question"
