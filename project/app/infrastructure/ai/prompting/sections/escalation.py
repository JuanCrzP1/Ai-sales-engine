"""«CUÁNDO PASAS EL CHAT A UNA PERSONA DEL EQUIPO»: las reglas que el negocio configuró (Asistente IA → Cómo atiende → «Cuándo pasar
a una persona», `contract/escalation.py`).

Son instrucciones para la IA, que decide con ellas y marca su decisión en `metadata.handoff` (con el motivo: «persona», «reclamo»,
«tema», «estancado»). Sin reglas del negocio no hay sección: vale la regla general de la plataforma (`instructions.PLATFORM`, «CUANDO
PIDE UNA PERSONA O RECLAMA»).
"""
from __future__ import annotations

from app.infrastructure.ai.prompting.text import as_dict, as_text, section, texts
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "CUÁNDO PASAS EL CHAT A UNA PERSONA DEL EQUIPO (reglas del negocio)"
OFFER_HELP_FIRST = (
    "El negocio pide ofrecer ayuda antes de pasar el chat. La primera vez que el cliente pida hablar con una persona, todavía no lo "
    "pases: pon metadata.handoff en \"\" (aunque el formato de respuesta diga «persona» para ese caso) y dile que con gusto lo "
    "ayudas tú, preguntándole qué necesita, en una frase y sin insistir. Si lo vuelve a pedir, pásalo con metadata.handoff «persona». "
    "Esto reemplaza la regla general de pasarlo apenas lo pida."
)
ALWAYS = (
    "Estos temas los atiende siempre el equipo: {topics}. Si el cliente pregunta o pide algo de uno de ellos, no le respondas sobre "
    "ese tema ni le digas si se puede o no: dile que lo pasas con el equipo para que lo ayuden y pon «tema» en metadata.handoff."
)
NEVER = "Estos temas los resuelves tú con la información del negocio, sin pasar el chat (salvo que el cliente pida una persona): {topics}."
STUCK = (
    "Si la conversación se estanca (el cliente repite lo mismo o está frustrado y no logras ayudarlo), pásalo con el equipo y pon "
    "«estancado» en metadata.handoff."
)
INSTRUCTIONS = "Indicaciones del negocio: «{instructions}»"
# El mensaje del negocio para cuando pasa el chat (Mensajes y canales). Con reglas propias va aquí y no en el cierre (`payments.py`):
# allí, «si lo pasas, usa este mensaje», hacía que la IA lo usara apenas el cliente pedía una persona (14 nov 2026).
HANDOFF_MESSAGE = "Solo en el mensaje en que de verdad pasas el chat al equipo (con metadata.handoff marcado), usa este mensaje del negocio: «{message}»"


def _join(topics: list[str]) -> str:
    return "; ".join(topic.strip() for topic in topics if topic.strip())


def render(view: PromptView) -> str:
    rules = as_dict(view.config.get("escalation"))
    if not rules:
        return ""
    always, never = texts(rules.get("always_topics")), texts(rules.get("never_topics"))
    instructions = " ".join(as_text(rules.get("instructions")).split())
    message = " ".join(as_text(as_dict(view.config.get("messages")).get("human_handoff")).split())
    lines = [
        OFFER_HELP_FIRST if as_text(rules.get("on_request")) == "offer_help_first" else "",
        ALWAYS.format(topics=_join(always)) if always else "",
        NEVER.format(topics=_join(never)) if never else "",
        STUCK if rules.get("when_stuck") is True else "",
        INSTRUCTIONS.format(instructions=instructions) if instructions else "",
        HANDOFF_MESSAGE.format(message=message) if message else "",
    ]
    return section(HEADER, [f"- {line}" for line in lines if line])
