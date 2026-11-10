"""«CÓMO SE PAGA Y SE CIERRA»: los medios de pago que tiene el negocio (solo sus nombres), cómo se cierra una venta, los datos que se
piden y por dónde atiende. Los datos de pago nunca están aquí: el motor los entrega cuando el cliente elige el medio."""
from __future__ import annotations

from app.infrastructure.ai.prompting.text import as_dict, as_list, as_text, dedupe, readable, section, sentence
from app.infrastructure.ai.prompting.view import PromptView

HEADER = "CÓMO SE PAGA Y SE CIERRA"
_TRANSFERS = {"nequi": "Nequi", "daviplata": "Daviplata", "breb": "Bre-B"}
_CLOSING = {"link_payment": "enviarle el link de pago", "data_collection": "pedirle sus datos", "human_handoff": "pasarlo con una persona del equipo"}


def _payment_blocks(pricing: dict) -> list[dict]:
    blocks = [as_dict(as_dict(plan).get("payment")) for plan in as_list(pricing.get("plans"))]
    return blocks + [as_dict(as_dict(pricing.get("catalog")).get("payment")), as_dict(pricing.get("payment"))]


def payment_methods(view: PromptView) -> list[str]:
    """Los medios de pago por su nombre: «Nequi», «transferencia a Bancolombia (ahorros)», «link de pago»."""
    names: list[str] = []
    blocks = _payment_blocks(view.pricing)
    for block in blocks:
        transfer = as_dict(block.get("transfer"))
        if not transfer.get("enabled"):
            continue
        for method in as_list(transfer.get("methods")):
            method = as_dict(method)
            kind = as_text(method.get("type")).lower()
            if kind == "bank":
                bank, account = as_text(method.get("bank")), as_text(method.get("account_type"))
                names.append(f"transferencia a {bank} ({account})" if bank and account else "transferencia bancaria")
            elif kind in _TRANSFERS:
                names.append(_TRANSFERS[kind])
    if any(as_text(block.get("link")) for block in blocks):
        names.append("link de pago")
    return dedupe(names)


def _enabled(raw: object) -> bool:
    return bool(as_dict(raw).get("enabled")) if isinstance(raw, dict) else raw is True


def _channels(raw: object) -> list[str]:
    raw = as_dict(raw).get("allowed", raw) if isinstance(raw, dict) else raw
    return dedupe(as_text(item) for item in ([raw] if isinstance(raw, str) else as_list(raw)))


def render(view: PromptView) -> str:
    capabilities = view.capabilities
    methods = payment_methods(view)
    closing = as_dict(capabilities.get("closing_methods"))
    # El link solo se ofrece si el negocio tiene uno: el motor no puede enviar lo que no existe.
    enabled = [text for key, text in _CLOSING.items() if _enabled(closing.get(key)) and (key != "link_payment" or "link de pago" in methods)]
    data = as_dict(capabilities.get("data_collection"))
    fields = dedupe(readable(as_text(item)) for item in as_list(data.get("fields"))) if data.get("enabled") or data.get("fields") else []
    actions = as_dict(capabilities.get("actions"))
    action_names = dedupe(readable(as_text(item)) for key in ("primary", "support") for item in as_list(actions.get(key)))
    attention, product = _channels(capabilities.get("business_channels")), _channels(capabilities.get("system_channels"))
    # Una configuración que solo trae `channels` los usa como canales de atención.
    if not attention and not product:
        attention = _channels(capabilities.get("channels"))
    lines = [
        sentence(f"Medios de pago: {', '.join(methods)}") if methods else "No hay medios de pago configurados: si el cliente quiere pagar, dile que el equipo le confirma cómo.",
        sentence(f"Para cerrar puedes {', '.join(enabled)}") if enabled else "",
        sentence(f"Datos que pides para cerrar: {', '.join(fields)}") if fields else "",
        sentence(f"Puedes ayudarle a: {', '.join(action_names)}") if action_names else "",
        sentence(f"Atiendes por: {', '.join(attention)}") if attention else "",
        sentence(f"Lo que vende funciona en: {', '.join(product)}") if product else "",
    ]
    return section(HEADER, lines)
