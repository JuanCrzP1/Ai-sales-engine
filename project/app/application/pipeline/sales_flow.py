from __future__ import annotations

from app.infrastructure.config.config_service import ConfigService


class SalesFlow:
    def __init__(self, *, config_service: ConfigService | None = None) -> None:
        self.config = config_service or ConfigService()

    def _resolve_tenant_config(self, *, tenant_slug: str, runtime_yaml: dict) -> tuple[dict, dict]:
        sales_cfg = runtime_yaml.get("sales") if isinstance(runtime_yaml.get("sales"), dict) else {}
        pricing_cfg = runtime_yaml.get("pricing") if isinstance(runtime_yaml.get("pricing"), dict) else {}

        if not sales_cfg:
            sales_payload = self.config.load_sales(client_id=tenant_slug) if tenant_slug else {}
            sales_cfg = sales_payload.get("sales") if isinstance(sales_payload.get("sales"), dict) else sales_payload
            sales_cfg = sales_cfg if isinstance(sales_cfg, dict) else {}

        if not pricing_cfg:
            pricing_payload = self.config.load_pricing(client_id=tenant_slug) if tenant_slug else {}
            pricing_cfg = pricing_payload if isinstance(pricing_payload, dict) else {}

        return sales_cfg, pricing_cfg

    def _resolve_tenant_features(self, *, tenant_slug: str, runtime_yaml: dict) -> dict:
        features_cfg = runtime_yaml.get("features") if isinstance(runtime_yaml.get("features"), dict) else {}
        if not features_cfg:
            features_payload = self.config.load_features(client_id=tenant_slug) if tenant_slug else {}
            features_cfg = features_payload if isinstance(features_payload, dict) else {}
        return features_cfg if isinstance(features_cfg, dict) else {}

    def _resolve_tenant_business(self, *, tenant_slug: str, runtime_yaml: dict) -> dict:
        business_cfg = runtime_yaml.get("business") if isinstance(runtime_yaml.get("business"), dict) else {}
        if not business_cfg:
            business_payload = self.config.load_business(client_id=tenant_slug) if tenant_slug else {}
            business_cfg = business_payload.get("business") if isinstance(business_payload.get("business"), dict) else {}
        return business_cfg if isinstance(business_cfg, dict) else {}

    def _resolve_tenant_inventory(self, *, tenant_slug: str, runtime_yaml: dict) -> dict:
        inventory_cfg = runtime_yaml.get("inventory") if isinstance(runtime_yaml.get("inventory"), dict) else {}
        if not inventory_cfg:
            inventory_payload = self.config.load_inventory(client_id=tenant_slug) if tenant_slug else {}
            inventory_cfg = inventory_payload if isinstance(inventory_payload, dict) else {}
        return inventory_cfg if isinstance(inventory_cfg, dict) else {}

    def build(self, *, tenant_slug: str, user_message: str, runtime_yaml: dict) -> tuple[dict, dict]:
        sales_cfg, pricing_cfg = self._resolve_tenant_config(tenant_slug=tenant_slug, runtime_yaml=runtime_yaml)
        business_cfg = self._resolve_tenant_business(tenant_slug=tenant_slug, runtime_yaml=runtime_yaml)
        features_cfg = self._resolve_tenant_features(tenant_slug=tenant_slug, runtime_yaml=runtime_yaml)
        inventory_cfg = self._resolve_tenant_inventory(tenant_slug=tenant_slug, runtime_yaml=runtime_yaml)
        memory_context = runtime_yaml.get("memory_context") if isinstance(runtime_yaml.get("memory_context"), dict) else {}
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
        runtime_yaml["business"] = business_cfg
        runtime_yaml["pricing"] = pricing_cfg
        runtime_yaml["features"] = features_cfg
        runtime_yaml["inventory"] = inventory_cfg
        runtime_yaml["sales_context"] = dict(runtime_context)
        runtime_yaml["last_user_message"] = str(user_message or "")

        return sales_cfg, pricing_cfg
