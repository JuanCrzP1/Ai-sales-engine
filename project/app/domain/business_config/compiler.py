"""Compila un BusinessConfig a las cinco secciones que el motor consume hoy.

Produce exactamente la forma de los YAML (`business`, `sales`, `pricing`, `inventory`, `config`) para
que el pipeline existente funcione sin cambios. Los datos de pago se resuelven con `resolve_secret`;
los campos de `compatibility` se reinyectan en su posición original.

- Todo campo con ruta en los YAML vuelve a esa ruta y con su forma original, lo use el motor o no:
  para un documento importado, la compilación es idéntica a sus YAML y el motor responde igual.
- Los campos que solo existen en el contrato (marca, horarios, promociones, recomendaciones,
  preguntas frecuentes, políticas...) no se compilan: ningún lector del motor actual los consume.
  Conectarlos exige cambiar el motor y acordar su clave de compilación (ver docs/business-config.md).
- Los planes y productos no disponibles no se compilan: el motor no los ofrece.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from app.domain.business_config.contract import BusinessConfig, PaymentProfile, Plan, SecretRef

SecretResolver = Callable[[SecretRef], str]


def _put(target: dict, key: str, value: Any) -> None:
    if value is not None:
        target[key] = value


def _dump(model: Any) -> Any:
    return None if model is None else model.model_dump(mode="json", exclude_none=True)


def _payment_block(profile: PaymentProfile | None, resolve_secret: SecretResolver) -> dict | None:
    if profile is None:
        return None
    methods = []
    for method in profile.transfer_methods:
        entry: dict[str, Any] = {"type": method.type}
        _put(entry, "number", resolve_secret(method.number) if method.number else None)
        _put(entry, "bank", method.bank)
        _put(entry, "account_type", method.account_type)
        _put(entry, "account_number", resolve_secret(method.account_number) if method.account_number else None)
        _put(entry, "reference", resolve_secret(method.reference) if method.reference else None)
        methods.append(entry)
    return {
        "link": resolve_secret(profile.link) if profile.link else "",
        "transfer": {"enabled": profile.transfer_enabled, "methods": methods},
    }


def _plan(plan: Plan, profiles: dict[str, PaymentProfile], resolve_secret: SecretResolver) -> dict:
    pricing: dict[str, dict] = {}
    for price in plan.prices:
        values: dict[str, Any] = {}
        for field in ("implementation", "monthly", "first_payment", "price"):
            _put(values, field, getattr(price, field))
        pricing[price.currency] = values
    entry: dict[str, Any] = {"id": plan.id, "name": plan.name}
    _put(entry, "description", plan.description)
    entry["pricing"] = pricing
    _put(entry, "includes", plan.includes)
    _put(entry, "not_included", plan.not_included)
    _put(entry, "payment", _payment_block(profiles.get(plan.payment_profile or ""), resolve_secret))
    _put(entry, "target", plan.target)
    return entry


def _business(config: BusinessConfig) -> dict:
    identity, sales = config.identity, config.sales
    business: dict[str, Any] = {
        "name": identity.name,
        "description": identity.description,
        "industry": identity.industry,
        "promise": identity.value_proposition,
    }
    _put(business, "buying_motivation", _dump(sales.buying_motivation))
    _put(business, "positioning", identity.positioning)
    _put(business, "differentiators", identity.differentiators)
    _put(business, "location", _dump(identity.location))
    _put(business, "service_modes", identity.service_modes)
    _put(business, "customer_profile", _dump(identity.target_customer))
    _put(business, "credibility", identity.credibility)
    _put(business, "tone", config.response_style.tone)
    _put(business, "voice", config.response_style.voice)
    _put(business, "pain_points", sales.pain_points)
    _put(business, "desired_outcomes", sales.benefits)
    if sales.motivation_drivers is not None:
        business["value_drivers"] = {
            driver.motivation: {"description": driver.description, "triggers": driver.signals} for driver in sales.motivation_drivers
        }
    if sales.use_cases is not None:
        # El prompt los lee aquí como respaldo, con sus nombres antiguos.
        business["use_cases"] = [{"nombre": case.name, "senales": case.signals, "enfoque": case.approach} for case in sales.use_cases]
    _put(business, "logistics", _dump(config.fulfillment))
    return business


def _sales(config: BusinessConfig) -> dict:
    sales_config = config.sales
    sales: dict[str, Any] = {}
    if sales_config.customer_problems is not None:
        sales["pain"] = {
            "clusters": {problem.id: problem.model_dump(mode="json", exclude={"id"}, exclude_none=True) for problem in sales_config.customer_problems}
        }
    solution = sales_config.solution
    section: dict[str, Any] = {}
    _put(section, "framing", sales_config.arguments)
    if solution is not None:
        if solution.mapping is not None:
            section["mapping"] = {entry.problem: entry.solutions for entry in solution.mapping}
        _put(section, "process_steps", solution.process_steps)
        _put(section, "requirements", solution.requirements)
    if section:
        sales["solution"] = section
    if sales_config.angles is not None:
        sales["angles"] = {angle.motivation: {"when": angle.signals, "execution": angle.messages} for angle in sales_config.angles}
    presentation = sales_config.offer_presentation
    if presentation is not None:
        strategy: dict[str, Any] = {}
        _put(strategy, "single", presentation.single_offer)
        _put(strategy, "multi", presentation.multiple_offers)
        sales["offer"] = {"strategy": strategy}
    if sales_config.discovery is not None:
        discovery: dict[str, Any] = {}
        _put(discovery, "questions", sales_config.discovery.questions)
        _put(discovery, "objectives", sales_config.discovery.objectives)
        if discovery:
            sales["discovery"] = discovery
    if sales_config.qualification is not None:
        # `criteria` solo existe en el contrato: no se compila.
        qualification = sales_config.qualification.model_dump(mode="json", exclude={"criteria"}, exclude_none=True)
        _put(sales, "qualification", qualification or None)
    support = sales_config.support
    if support is not None:
        section = {}
        info_handling: dict[str, Any] = {}
        _put(info_handling, "explain_first", support.explain_first)
        _put(info_handling, "sell_after", support.sell_after)
        if info_handling:
            section["info_handling"] = info_handling
        _put(section, "hard_rules", support.rules)
        sales["support"] = section
    flow = sales_config.conversation_flow
    if flow is not None:
        rules: dict[str, Any] = {}
        _put(rules, "no_skip_steps", flow.no_skip_steps)
        _put(rules, "guided_process", flow.guided_process)
        sales["conversation_flow"] = {"steps": flow.steps, **({"rules": rules} if rules else {})}
    if sales_config.objections is not None:
        objections: dict[str, Any] = {}
        for objection in sales_config.objections:
            layers: dict[str, Any] = {}
            for layer in ("acknowledge", "reframe", "proof", "redirect"):
                _put(layers, layer, getattr(objection, layer))
            entry: dict[str, Any] = {"layers": layers} if layers else {}
            _put(entry, "hard_rules", objection.rules)
            objections[objection.topic] = entry
        sales["objection"] = objections
    closing = sales_config.closing
    if closing is not None:
        section = {"strategy": closing.strategy}
        _put(section, "required_data", closing.required_data)
        _put(section, "triggers", closing.purchase_signals)
        if closing.high_intent_actions is not None:
            section["actions"] = {"high_intent": closing.high_intent_actions}
        _put(section, "next_steps", closing.next_steps)
        _put(section, "micro_commitments", closing.micro_commitments)
        _put(section, "hard_rules", closing.rules)
        sales["closing"] = section
    return sales


def _pricing(config: BusinessConfig, resolve_secret: SecretResolver) -> dict:
    profiles = {profile.id: profile for profile in config.payments}
    pricing: dict[str, Any] = {}
    offer = config.offer
    if offer.model == "plans":
        pricing["plans"] = [_plan(plan, profiles, resolve_secret) for plan in offer.plans or [] if plan.available]
    else:
        catalog = offer.catalog
        assert catalog is not None
        items = [item for item in catalog.items if item.available]
        used = {item.category for item in items}
        pricing["model"] = "catalog"
        catalog_section: dict[str, Any] = {
            "categories": [{"id": category.id, "name": category.name} for category in catalog.categories if category.id in used],
            "items": [],
        }
        for item in items:
            entry: dict[str, Any] = {"id": item.id, "name": item.name, "category": item.category}
            _put(entry, "description", item.description)
            entry["price"] = {price.currency: price.amount for price in item.prices}
            catalog_section["items"].append(entry)
        _put(catalog_section, "payment", _payment_block(profiles.get(catalog.payment_profile or ""), resolve_secret))
        pricing["catalog"] = catalog_section

    terms = config.terms
    _put(pricing, "conditions", terms.conditions)
    if terms.price_framing is not None:
        pricing["price_framing"] = {"type": terms.price_framing}
    roi: dict[str, Any] = {}
    _put(roi, "break_even_sales", terms.roi_break_even_sales)
    _put(roi, "break_even_reservas", terms.roi_break_even_bookings)
    if roi:
        pricing["roi"] = roi
    _put(pricing, "roi_hints", terms.roi_hints)
    _put(pricing, "note", terms.price_note)
    business_offers: dict[str, Any] = _dump(config.sales.offer_mix) or {}
    _put(business_offers, "financing", _dump(terms.financing))
    if business_offers:
        pricing["business_offers"] = business_offers
    return pricing


def _inventory(config: BusinessConfig) -> dict:
    # El precio por variante solo existe en el contrato: no se compila.
    items = [item.model_dump(mode="json", exclude={"variants": {"__all__": {"prices"}}}, exclude_none=True) for item in config.inventory.items]
    inventory: dict[str, Any] = {"items": items}
    _put(inventory, "track_stock", config.inventory.track_stock)
    return inventory


def _features(config: BusinessConfig) -> dict:
    if config.engine is not None:
        return config.engine.features.model_dump(exclude_none=True)
    # Sin ajustes internos explícitos: se derivan de la oferta.
    is_catalog = config.offer.model == "catalog"
    features: dict[str, Any] = {"pricing_enabled": True, "catalog_mode": is_catalog}
    if is_catalog:
        features["business_model"] = "catalog"
    return features


def _config(config: BusinessConfig) -> dict:
    section: dict[str, Any] = {}
    if config.engine is not None and config.engine.conversation is not None:
        section["conversation"] = config.engine.conversation.model_dump()
    section["initial_message"] = {"enabled": config.messages.welcome.enabled, "text": config.messages.welcome.text}
    section["features"] = _features(config)
    section["response"] = {"length": config.response_style.length, "max_words": config.response_style.effective_max_words()}
    post_payment: dict[str, dict] = {}
    if config.messages.payment_reported is not None:
        post_payment["on_user_report"] = {"message": config.messages.payment_reported}
    if config.messages.payment_confirmed is not None:
        post_payment["on_payment_confirmed"] = {"message": config.messages.payment_confirmed}
    section["post_payment"] = post_payment
    capabilities = config.capabilities
    section["capabilities"] = {
        "business_channels": {"allowed": list(capabilities.service_channels)},
        "system_channels": {"allowed": list(capabilities.product_channels)},
        "actions": {"primary": list(capabilities.actions_primary), "support": list(capabilities.actions_support)},
        "closing_methods": {
            "link_payment": {"enabled": capabilities.closing_methods.payment_link},
            "human_handoff": {"enabled": capabilities.closing_methods.human_handoff},
            "data_collection": {"enabled": capabilities.closing_methods.data_collection},
        },
        "data_collection": {"enabled": capabilities.data_collection.enabled, "fields": list(capabilities.data_collection.fields)},
    }
    if capabilities.restrictions is not None:
        constraints = capabilities.restrictions.model_dump(mode="json", exclude={"forbidden_claims"}, exclude_none=True)
        section["capabilities"]["constraints"] = constraints
    return section


def merge_compatibility(base: Any, extra: Any, path: str = "") -> Any:
    """Reinyecta campos de compatibilidad sin sobrescribir datos del contrato."""
    if isinstance(base, dict) and isinstance(extra, dict):
        for key, value in extra.items():
            child_path = f"{path}.{key}" if path else key
            base[key] = merge_compatibility(base[key], value, child_path) if key in base else copy.deepcopy(value)
        return base
    if isinstance(base, list) and isinstance(extra, list) and len(base) == len(extra):
        return [merge_compatibility(item, extra_item, f"{path}[{index}]") for index, (item, extra_item) in enumerate(zip(base, extra))]
    raise ValueError(f"conflicto de compatibilidad en '{path}'")


def compile_business_config(config: BusinessConfig, resolve_secret: SecretResolver) -> dict[str, dict]:
    sections = {
        "business": _business(config),
        "sales": _sales(config),
        "pricing": _pricing(config, resolve_secret),
        "inventory": _inventory(config),
        "config": _config(config),
    }
    return merge_compatibility(sections, config.compatibility)
