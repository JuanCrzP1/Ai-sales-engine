"""El trato con el cliente (de tú o de usted) en los textos que escribe la plataforma, no la IA.

El negocio elige el trato en el panel (Asistente IA → Estilo, `response_style.formality`) y el motor lo compila en
`config.profile.formality`. La IA escribe con ese trato (`infrastructure/ai/prompting/sections/business.py`). Los textos fijos salen
sin la IA: los datos de pago y las ofertas de enviarlos, el paso a una persona, los avisos de espera y el respaldo cuando la IA no
responde. Deben sonar como ella, así que cada uno tiene su versión de tú y de usted (`Phrase`), junto a donde se usa.

Solo «formal» cambia el texto. Con «informal», «neutral» o sin elegir, sale el de siempre (de tú). Lo que el negocio escribió en el
panel (su plantilla de pago, sus mensajes) sale tal cual: esto es solo para los textos de la plataforma.

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
    config = compiled.get("config") if isinstance(compiled, dict) and isinstance(compiled.get("config"), dict) else {}
    profile = config.get("profile") if isinstance(config.get("profile"), dict) else {}
    return str(profile.get("formality") or "").strip().lower()
