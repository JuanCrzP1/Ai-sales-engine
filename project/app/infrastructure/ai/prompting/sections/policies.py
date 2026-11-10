"""«POLÍTICAS DEL NEGOCIO»: garantía, cambios y devoluciones, y cancelaciones, tal como las escribió el negocio. La IA las dice sin
cambiarlas ni completarlas; si una no está, la regla de la plataforma la obliga a no inventarla."""
from __future__ import annotations

from app.infrastructure.ai.prompting.text import as_dict, one_line, section, sentence
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "POLÍTICAS DEL NEGOCIO (si te preguntan, dilas tal como están, sin cambiarlas ni completarlas)"
_POLICIES = (("warranty", "Garantía"), ("returns", "Cambios y devoluciones"), ("cancellation", "Cancelaciones y reembolsos"))


def render(view: PromptView) -> str:
    policies = as_dict(as_dict(view.config.get("profile")).get("policies"))
    return section(HEADER, [sentence(f"{label}: {text}") for key, label in _POLICIES if (text := one_line(policies.get(key)))])
