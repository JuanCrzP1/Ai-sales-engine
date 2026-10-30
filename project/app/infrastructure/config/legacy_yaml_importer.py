"""Importa las cinco secciones YAML antiguas de un negocio al contrato BusinessConfig v1.

- Los campos con lugar propio en el contrato se convierten a su forma tipada (ver la matriz de
  trazabilidad en docs/business-config-traceability.md).
- Lo demás (plantillas del motor, duplicados, datos inconsistentes) se conserva en `compatibility`
  con su ruta original, sin pérdida.
- Los datos de pago sensibles se sustituyen por `SecretRef` con origen `legacy_yaml`, que apuntan
  a su posición en las secciones antiguas; nunca se copian al contrato.

Cualquier clave inesperada en estructuras que se tipan por completo (pagos, catálogo) detiene la
importación en lugar de perderse.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from app.domain.business_config.contract import BusinessConfig

LEGACY_SECRET_SOURCE = "legacy_yaml"
SECTIONS = ("business", "sales", "pricing", "inventory", "config")
SENSITIVE_PAYMENT_FIELDS = ("number", "account_number", "reference")
PLAN_TYPED_KEYS = ("id", "name", "description", "pricing", "includes", "not_included", "payment", "target")


@dataclass
class ImportResult:
    config: BusinessConfig
    typed_fields: int
    compatibility_fields: int
    secret_refs: int


def count_leaves(value: Any) -> int:
    if isinstance(value, dict):
        return sum(count_leaves(child) for child in value.values()) if value else 1
    if isinstance(value, list):
        return sum(count_leaves(child) for child in value) if value else 1
    return 1


def _ensure_keys(value: dict, allowed: set[str], path: str) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ValueError(f"claves no soportadas en {path}: {unexpected}")


class _Remainder:
    """Copia de las secciones de la que se retiran los campos tipados; el resto es compatibilidad."""

    def __init__(self, sections: dict[str, dict]) -> None:
        self.data = copy.deepcopy(sections)
        self._touched: list[dict] = []
        self.secret_refs = 0

    def child(self, container: dict | None, key: str) -> dict | None:
        value = container.get(key) if isinstance(container, dict) else None
        return value if isinstance(value, dict) else None

    def take(self, container: dict | None, key: str, default: Any = None) -> Any:
        if not isinstance(container, dict) or key not in container:
            return default
        self._touched.append(container)
        return container.pop(key)

    def secret(self, path: str) -> dict:
        self.secret_refs += 1
        return {"secret_ref": f"{LEGACY_SECRET_SOURCE}:{path}"}

    def prune(self) -> dict:
        """Elimina solo los contenedores que quedaron vacíos al retirar campos tipados."""
        touched = {id(container) for container in self._touched}

        def _emptied(node: Any) -> bool:
            return isinstance(node, dict) and not node and id(node) in touched

        def _prune(node: Any) -> None:
            if isinstance(node, dict):
                for key in list(node):
                    child = node[key]
                    _prune(child)
                    if _emptied(child) or (isinstance(child, list) and child and all(_emptied(item) for item in child)):
                        self._touched.append(node)
                        touched.add(id(node))
                        del node[key]
            elif isinstance(node, list):
                for item in node:
                    _prune(item)

        _prune(self.data)
        return {name: section for name, section in self.data.items() if not _emptied(section)}


def _payment_profile(rest: _Remainder, payment: dict, profile_id: str, path: str) -> dict:
    _ensure_keys(payment, {"link", "transfer"}, path)
    transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
    _ensure_keys(transfer, {"enabled", "methods"}, f"{path}.transfer")
    methods = []
    for index, method in enumerate(transfer.get("methods") or []):
        method_path = f"{path}.transfer.methods.{index}"
        _ensure_keys(method, {"type", "bank", "account_type", *SENSITIVE_PAYMENT_FIELDS}, method_path)
        entry: dict[str, Any] = {"type": method.get("type")}
        for field in ("bank", "account_type"):
            if field in method:
                entry[field] = method[field]
        for field in SENSITIVE_PAYMENT_FIELDS:
            if field in method:
                entry[field] = rest.secret(f"{method_path}.{field}")
        methods.append(entry)
    return {
        "id": profile_id,
        "link": rest.secret(f"{path}.link") if str(payment.get("link") or "").strip() else None,
        "transfer_enabled": bool(transfer.get("enabled", False)),
        "transfer_methods": methods,
    }


def _import_plans(rest: _Remainder, pricing: dict, payments: list[dict]) -> dict:
    plans = []
    leftovers = []
    for index, original in enumerate(rest.take(pricing, "plans") or []):
        payment = original.get("payment")
        entry: dict[str, Any] = {
            "id": original.get("id"),
            "name": original.get("name"),
            "description": original.get("description"),
            "prices": [{"currency": currency, **values} for currency, values in (original.get("pricing") or {}).items()],
            "includes": original.get("includes"),
            "not_included": original.get("not_included"),
            "target": original.get("target"),
        }
        if isinstance(payment, dict):
            profile_id = str(entry["id"])
            payments.append(_payment_profile(rest, payment, profile_id, f"pricing.plans.{index}.payment"))
            entry["payment_profile"] = profile_id
        plans.append(entry)
        leftover = {key: value for key, value in original.items() if key not in PLAN_TYPED_KEYS}
        rest._touched.append(leftover)
        leftovers.append(leftover)
    # Los restos de cada plan (p. ej. `target`) se conservan en su misma posición.
    pricing["plans"] = leftovers
    return {"model": "plans", "plans": plans}


def _import_catalog(rest: _Remainder, pricing: dict, payments: list[dict]) -> dict:
    rest.take(pricing, "model")
    catalog = rest.take(pricing, "catalog") or {}
    _ensure_keys(catalog, {"categories", "items", "payment"}, "pricing.catalog")
    for index, category in enumerate(catalog.get("categories") or []):
        _ensure_keys(category, {"id", "name"}, f"pricing.catalog.categories.{index}")
    for index, item in enumerate(catalog.get("items") or []):
        _ensure_keys(item, {"id", "name", "category", "description", "price"}, f"pricing.catalog.items.{index}")
    entry: dict[str, Any] = {
        "categories": [{"id": category.get("id"), "name": category.get("name")} for category in catalog.get("categories") or []],
        "items": [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "description": item.get("description"),
                "prices": [{"currency": currency, "amount": amount} for currency, amount in (item.get("price") or {}).items()],
            }
            for item in catalog.get("items") or []
        ],
    }
    if isinstance(catalog.get("payment"), dict):
        payments.append(_payment_profile(rest, catalog["payment"], "catalog", "pricing.catalog.payment"))
        entry["payment_profile"] = "catalog"
    return {"model": "catalog", "catalog": entry}


def _compact(values: dict[str, Any]) -> dict[str, Any] | None:
    """El diccionario sin valores nulos, o None si no queda nada (la estructura no existía)."""
    present = {key: value for key, value in values.items() if value is not None}
    return present or None


def _identity(rest: _Remainder, business: dict) -> dict:
    take, child = rest.take, rest.child
    location = take(business, "location")
    if isinstance(location, dict):
        _ensure_keys(location, {"type", "address", "city", "coverage"}, "business.location")
    profile = child(business, "customer_profile")
    target_customer = None
    if profile is not None:
        target_customer = _compact({key: take(profile, key) for key in ("segment", "company_size", "maturity", "roles")})
    return {
        "name": take(business, "name"),
        "industry": take(business, "industry"),
        "description": take(business, "description"),
        "value_proposition": take(business, "promise"),
        "positioning": take(business, "positioning"),
        "differentiators": take(business, "differentiators"),
        "location": location,
        "service_modes": take(business, "service_modes"),
        "target_customer": target_customer,
        "credibility": take(business, "credibility"),
    }


def _customer_problems(rest: _Remainder, sales: dict) -> list[dict] | None:
    clusters = rest.child(rest.child(sales, "pain"), "clusters")
    if clusters is None:
        return None
    fields = ("impacts", "signals", "monetization", "urgency_levels", "recommended_angles")
    return [
        {"id": cluster_id, **{field: rest.take(cluster, field) for field in fields}} if isinstance(cluster, dict) else {"id": cluster_id}
        for cluster_id, cluster in clusters.items()
    ]


def _keyed_list(mapping: Any, key_name: str, fields: dict[str, str], path: str) -> list[dict] | None:
    """Convierte `{clave: {campo antiguo: valor}}` en `[{key_name: clave, campo nuevo: valor}]`."""
    if not isinstance(mapping, dict):
        return None
    result = []
    for key, entry in mapping.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{path}.{key} no es un objeto")
        _ensure_keys(entry, set(fields), f"{path}.{key}")
        result.append({key_name: key, **{new: entry.get(old) for old, new in fields.items()}})
    return result


def _sales(rest: _Remainder, business: dict, sales: dict, pricing: dict) -> dict:
    take, child = rest.take, rest.child
    solution = child(sales, "solution")
    mapping = take(solution, "mapping")
    discovery = child(sales, "discovery")
    qualification = child(sales, "qualification")
    support = child(sales, "support")
    flow = child(sales, "conversation_flow")
    closing = child(sales, "closing")
    offers = child(pricing, "business_offers")

    use_cases = take(business, "use_cases")
    if isinstance(use_cases, list):
        for index, case in enumerate(use_cases):
            _ensure_keys(case, {"nombre", "senales", "enfoque"}, f"business.use_cases.{index}")
        use_cases = [{"name": case.get("nombre"), "signals": case.get("senales"), "approach": case.get("enfoque")} for case in use_cases]

    objections = None
    raw_objections = child(sales, "objection")
    if raw_objections is not None:
        objections = []
        for topic, objection in raw_objections.items():
            layers = child(objection, "layers")
            objections.append(
                {
                    "topic": topic,
                    **{layer: take(layers, layer) for layer in ("acknowledge", "reframe", "proof", "redirect")},
                    "rules": take(objection, "hard_rules"),
                }
            )

    flow_rules = child(flow, "rules")
    strategy = take(child(sales, "offer"), "strategy")
    if isinstance(strategy, dict):
        _ensure_keys(strategy, {"single", "multi"}, "sales.offer.strategy")
    return {
        "buying_motivation": take(business, "buying_motivation"),
        "motivation_drivers": _keyed_list(take(business, "value_drivers"), "motivation", {"description": "description", "triggers": "signals"}, "business.value_drivers"),
        "customer_problems": _customer_problems(rest, sales),
        "pain_points": take(business, "pain_points"),
        "use_cases": use_cases,
        "benefits": take(business, "desired_outcomes"),
        "arguments": take(solution, "framing"),
        "solution": _compact(
            {
                "mapping": [{"problem": problem, "solutions": solutions} for problem, solutions in mapping.items()] if isinstance(mapping, dict) else None,
                "process_steps": take(solution, "process_steps"),
                "requirements": take(solution, "requirements"),
            }
        ),
        "angles": _keyed_list(take(sales, "angles"), "motivation", {"when": "signals", "execution": "messages"}, "sales.angles"),
        "offer_mix": None if offers is None else _compact({key: take(offers, key) for key in ("core", "upsell", "cross_sell")}),
        "offer_presentation": None if not isinstance(strategy, dict) else {"single_offer": strategy.get("single"), "multiple_offers": strategy.get("multi")},
        "discovery": None if discovery is None else _compact({"questions": take(discovery, "questions"), "objectives": take(discovery, "objectives")}),
        "qualification": None if qualification is None else _compact({"detect_offer_fit": take(qualification, "detect_offer_fit")}),
        "support": None
        if support is None
        else _compact(
            {
                "explain_first": take(child(support, "info_handling"), "explain_first"),
                "sell_after": take(child(support, "info_handling"), "sell_after"),
                "rules": take(support, "hard_rules"),
            }
        ),
        "conversation_flow": None
        if flow is None
        else _compact(
            {
                "steps": take(flow, "steps"),
                "no_skip_steps": take(flow_rules, "no_skip_steps"),
                "guided_process": take(flow_rules, "guided_process"),
            }
        ),
        "objections": objections,
        # Quedan en compatibilidad `behavior` y `next_step`: plantillas idénticas en todos los negocios.
        "closing": None
        if closing is None
        else _compact(
            {
                "strategy": take(closing, "strategy"),
                "required_data": take(closing, "required_data"),
                "purchase_signals": take(closing, "triggers"),
                "high_intent_actions": take(child(closing, "actions"), "high_intent"),
                "next_steps": take(closing, "next_steps"),
                "micro_commitments": take(closing, "micro_commitments"),
                "rules": take(closing, "hard_rules"),
            }
        ),
    }


def import_legacy_sections(tenant_slug: str, sections: dict[str, dict]) -> ImportResult:
    missing = [name for name in SECTIONS if not isinstance(sections.get(name), dict)]
    if missing:
        raise ValueError(f"{tenant_slug}: faltan secciones {missing}")

    rest = _Remainder({name: sections[name] for name in SECTIONS})
    business, sales, pricing, inventory, config = (rest.data[name] for name in SECTIONS)
    take, child = rest.take, rest.child

    payments: list[dict] = []
    offer = _import_plans(rest, pricing, payments) if "plans" in pricing else _import_catalog(rest, pricing, payments)
    roi = child(pricing, "roi")
    terms = {
        "conditions": take(pricing, "conditions"),
        "price_framing": take(child(pricing, "price_framing"), "type"),
        "roi_break_even_sales": take(roi, "break_even_sales"),
        "roi_break_even_bookings": take(roi, "break_even_reservas"),
        "roi_hints": take(pricing, "roi_hints"),
        "price_note": take(pricing, "note"),
        "financing": take(child(pricing, "business_offers"), "financing"),
    }

    capabilities = child(config, "capabilities")
    closing = child(capabilities, "closing_methods")
    data_collection = child(capabilities, "data_collection")
    actions = child(capabilities, "actions")
    initial_message = child(config, "initial_message")
    post_payment = child(config, "post_payment")
    response = child(config, "response")
    features = child(config, "features")

    contract: dict[str, Any] = {
        "tenant_slug": tenant_slug,
        "identity": _identity(rest, business),
        "offer": offer,
        "terms": terms,
        "payments": payments,
        "sales": _sales(rest, business, sales, pricing),
        "capabilities": {
            "service_channels": take(child(capabilities, "business_channels"), "allowed", []),
            "product_channels": take(child(capabilities, "system_channels"), "allowed", []),
            "actions_primary": take(actions, "primary", []),
            "actions_support": take(actions, "support", []),
            "closing_methods": {
                "payment_link": take(child(closing, "link_payment"), "enabled", False),
                "human_handoff": take(child(closing, "human_handoff"), "enabled", False),
                "data_collection": take(child(closing, "data_collection"), "enabled", False),
            },
            "data_collection": {"enabled": take(data_collection, "enabled", False), "fields": take(data_collection, "fields", [])},
            "restrictions": take(capabilities, "constraints"),
        },
        "messages": {
            "welcome": {"enabled": take(initial_message, "enabled", False), "text": take(initial_message, "text", "")},
            "payment_reported": take(child(post_payment, "on_user_report"), "message"),
            "payment_confirmed": take(child(post_payment, "on_payment_confirmed"), "message"),
        },
        "response_style": {
            "tone": take(business, "tone"),
            "voice": take(business, "voice"),
            "length": take(response, "length"),
            "max_words": take(response, "max_words"),
        },
        "knowledge": {"faqs": take(child(config, "knowledge"), "faqs", [])},
        "fulfillment": take(business, "logistics"),
        "inventory": {"items": take(inventory, "items", []), "track_stock": take(inventory, "track_stock")},
        "engine": {
            "conversation": take(config, "conversation"),
            "features": {
                "pricing_enabled": take(features, "pricing_enabled"),
                "catalog_mode": take(features, "catalog_mode"),
                "business_model": take(features, "business_model"),
            },
        },
    }
    # Los valores nulos se omiten en los campos tipados; la compatibilidad se conserva intacta.
    contract = _drop_none(contract)
    contract["compatibility"] = rest.prune()

    config_model = BusinessConfig.model_validate(contract)
    return ImportResult(
        config=config_model,
        typed_fields=count_leaves(config_model.model_dump(exclude={"compatibility"}, exclude_none=True)),
        compatibility_fields=count_leaves(contract["compatibility"]) if contract["compatibility"] else 0,
        secret_refs=rest.secret_refs,
    )


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _drop_none(child) for key, child in value.items() if child is not None}
    if isinstance(value, list):
        return [_drop_none(child) for child in value]
    return value
