from __future__ import annotations


def _section(runtime_yaml: dict, key: str) -> dict:
    value = runtime_yaml.get(key)
    return value if isinstance(value, dict) else {}


class SalesFlow:
    """Prepara el contexto comercial del mensaje. Todo sale del runtime del negocio: su configuración publicada y su memoria."""

    def build(self, *, tenant_slug: str, user_message: str, runtime_yaml: dict) -> tuple[dict, dict]:
        del tenant_slug
        sales_cfg = _section(runtime_yaml, "sales")
        pricing_cfg = _section(runtime_yaml, "pricing")
        memory_context = _section(runtime_yaml, "memory_context")
        runtime_context = {
            "mode": str(runtime_yaml.get("mode") or memory_context.get("mode") or "").strip().lower(),
            "stage": str(runtime_yaml.get("conversation_stage") or runtime_yaml.get("lead_stage") or memory_context.get("stage") or "").strip().lower(),
            "last_intent": str(memory_context.get("last_intent") or runtime_yaml.get("last_intent") or "").strip().lower(),
            "last_pain": str(memory_context.get("last_pain") or runtime_yaml.get("active_pain") or "").strip(),
            "last_cta": str(memory_context.get("last_cta") or "").strip(),
            "history_summary": str(memory_context.get("history_summary") or "").strip(),
            "previous_user_message": str(runtime_yaml.get("previous_user_message") or "").strip(),
        }

        runtime_yaml["sales"] = sales_cfg
        runtime_yaml["business"] = _section(runtime_yaml, "business")
        runtime_yaml["pricing"] = pricing_cfg
        runtime_yaml["features"] = _section(runtime_yaml, "features")
        runtime_yaml["inventory"] = _section(runtime_yaml, "inventory")
        runtime_yaml["sales_context"] = dict(runtime_context)
        runtime_yaml["last_user_message"] = str(user_message or "")

        return sales_cfg, pricing_cfg
