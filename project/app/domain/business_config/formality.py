"""El estilo del negocio en los textos que escribe la plataforma, no la IA: el trato (de tú o de usted) y los emojis.

El negocio elige el trato en el panel (Asistente IA → Estilo, `response_style.formality`) y el motor lo compila en
`config.profile.formality`. La IA escribe con ese trato (`infrastructure/ai/prompting/sections/business.py`). Los textos fijos salen
sin la IA: los datos de pago y las ofertas de enviarlos, el paso a una persona, los avisos de espera y el respaldo cuando la IA no
responde. Deben sonar como ella, así que cada uno tiene su versión de tú y de usted (`Phrase`), junto a donde se usa.

Solo «formal» cambia el texto. Con «informal», «neutral» o sin elegir, sale el de siempre (de tú). Lo que el negocio escribió en el
panel (su plantilla de pago, sus mensajes) sale tal cual: esto es solo para los textos de la plataforma.

Los emojis: si el negocio eligió no usarlos (`response_style.emojis`, compilado en `config.profile.emojis`), los textos de la
plataforma tampoco los llevan (`allows_emojis`). Hasta el 25 nov 2026 el mensaje con los datos de pago salía con 💳 y ✅ igual.

Hasta el 19 nov 2026 todos estaban de tú: un negocio que trataba de usted recibía «Cuando pagues, envíame aquí la captura…» justo
debajo de una respuesta de usted.
"""
from __future__ import annotations

from dataclasses import dataclass

FORMAL = "formal"


@dataclass(frozen=True)
class Phrase:
    """Un texto fijo para el cliente, de tú y de usted. Con marcadores (`{method}`), se llenan después de elegir."""

    tu: str
    usted: str

    def to(self, formality: str | None) -> str:
        return self.usted if formality == FORMAL else self.tu


def formality_of(compiled: dict | None) -> str:
    """El trato del negocio («informal», «neutral», «formal»), o "" si no eligió. Sirve con el runtime de un mensaje y con lo
    publicado (`compile_business_config`): los dos lo traen en `config.profile.formality`."""
    return str(_profile(compiled).get("formality") or "").strip().lower()


def allows_emojis(compiled: dict | None) -> bool:
    """Si los textos de la plataforma pueden llevar emojis: sí, salvo que el negocio haya elegido no usarlos."""
    return _profile(compiled).get("emojis") is not False


def _profile(compiled: dict | None) -> dict:
    config = compiled.get("config") if isinstance(compiled, dict) and isinstance(compiled.get("config"), dict) else {}
    return config.get("profile") if isinstance(config.get("profile"), dict) else {}
