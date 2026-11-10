"""Por qué compra el cliente de este negocio: sus motivaciones y los casos típicos (problemas o usos)."""
from __future__ import annotations

from app.domain.business_config.engine_policy import MAX_CUSTOMER_PROBLEMS
from app.infrastructure.ai.prompting.text import as_dict, as_list, as_text
from app.infrastructure.ai.prompting.view import PromptView


def _impact_samples(sales: dict) -> list[str]:
    """El primer impacto de cada problema del cliente, hasta el máximo del contrato."""
    samples: list[str] = []
    for cluster in as_dict(as_dict(sales.get("pain")).get("clusters")).values():
        if not isinstance(cluster, dict):
            continue
        first = next((text for impact in as_list(cluster.get("impacts")) if (text := as_text(impact))), "")
        if first:
            samples.append(first)
        if len(samples) >= MAX_CUSTOMER_PROBLEMS:
            break
    return samples


def render(view: PromptView) -> str:
    sales, business = view.sales, view.business
    motivations = as_dict(sales.get("buying_motivation")) or as_dict(business.get("buying_motivation"))
    use_cases = as_list(sales.get("use_cases")) or as_list(business.get("use_cases"))
    primary, secondary = as_text(motivations.get("primary", "")), as_text(motivations.get("secondary", ""))
    impact_text = ", ".join(_impact_samples(sales))
    use_cases_text = ", ".join(
        name for item in use_cases[:MAX_CUSTOMER_PROBLEMS] if isinstance(item, dict) and (name := as_text(item.get("nombre", "") or item.get("name", "")))
    )

    lines = []
    if primary or secondary:
        lines.append(f"Motores de compra: {primary or 'no definido'} y {secondary or 'no definido'}.")
    if impact_text or use_cases_text:
        lines.append(f"Casos típicos: {impact_text or use_cases_text}.")
    return "\n".join(lines).strip()
