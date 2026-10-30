"""Catálogo de los campos de los YAML antiguos y su lugar en BusinessConfig v1.

Fuente de la matriz de trazabilidad (`docs/business-config-traceability.md`, generada con
`scripts/generate_traceability_matrix.py`). Las pruebas recorren los cinco YAML de los nueve negocios
y comprueban que cada campo está catalogado y que su valor aparece de verdad en el destino declarado.

Patrones de origen: `[]` es un índice de lista y `<nombre>` una clave variable (id de problema,
moneda...). `.**` al final abarca todos los campos que cuelgan de la ruta, que conservan su nombre
en el destino.
Destinos: ruta del contrato, donde `[{i}]` y `[{j}]` son los índices del origen y
`[campo=<nombre>]` busca en una lista por clave; `compatibility` (misma ruta dentro de
`compatibility`) o `secret:<ruta>` (referencia `legacy_yaml:` al valor, nunca el valor).

Clases (misión de auditoría del contrato):
- A: configuración que edita el cliente.
- B: configuración comercial avanzada (reglas de venta, objeciones, cierre...).
- C: configuración interna del motor.
- D: información sensible (datos de pago): fuera del contrato, como referencia.
- E: derivada, obsoleta o redundante.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Literal

Category = Literal["A", "B", "C", "D", "E"]

# Secciones de los YAML: el archivo de origen de cada una.
SOURCE_FILES = {
    "business": "business.yaml",
    "sales": "sales.yaml",
    "pricing": "pricing.yaml",
    "inventory": "inventory.yaml",
    "config": "config.yaml",
}

# Mapas con claves variables: la clave se representa con un marcador en el patrón.
DYNAMIC_KEYS = {
    "business.value_drivers": "<motivo>",
    "sales.pain.clusters": "<problema>",
    "sales.angles": "<motivo>",
    "sales.solution.mapping": "<problema>",
    "sales.objection": "<objecion>",
    "sales.closing.behavior": "<estrategia>",
    "pricing.plans[].pricing": "<moneda>",
    "pricing.catalog.items[].price": "<moneda>",
}

# Pruebas que demuestran conservación y uso en el motor actual. Las de uso están en
# tests/test_business_config_engine_integration.py; `test_evidence_names_exist` comprueba que existen.
CONSERVED = "test_business_config_traceability.py::test_every_legacy_field_reaches_its_declared_destination"
ENGINE_TEST = "test_connected_fields_change_the_prompt"
PAYMENT_TEST = "test_payment_methods_reach_the_customer"
ISOLATION_TEST = "test_tenants_stay_isolated_with_contract_source"
UNAVAILABLE_TEST = "test_unavailable_offer_is_not_offered"
NOT_IN_PROMPT = "no: el prompt actual no lo usa"


@dataclass(frozen=True)
class LegacyField:
    pattern: str
    meaning: str
    category: Category
    destination: str
    transform: str = ""
    engine: str = "no"
    panel: Literal["pantalla", "modelo", "no"] = "no"
    note: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)

    @property
    def kind(self) -> Literal["typed", "compatibility", "secret"]:
        if self.destination == "compatibility":
            return "compatibility"
        return "secret" if self.destination.startswith("secret:") else "typed"


def _f(pattern: str, meaning: str, category: Category, destination: str, **extra: Any) -> LegacyField:
    evidence = extra.pop("evidence", ())
    return LegacyField(pattern, meaning, category, destination, evidence=tuple(evidence) if isinstance(evidence, (list, tuple)) else (evidence,), **extra)


CATALOG: tuple[LegacyField, ...] = (
    # ------------------------------------------------------------------ business.yaml
    _f("business.name", "Nombre comercial", "A", "identity.name", engine=NOT_IN_PROMPT, panel="pantalla"),
    _f("business.brand_name", "Marca", "E", "compatibility",
       note="Igual a `name` en los 9 negocios. El contrato ofrece `identity.brand_name` para marcas distintas del nombre."),
    _f("business.industry", "Sector o tipo de negocio", "A", "identity.industry", engine="sí: prompt (sector)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.description", "Descripción del negocio", "A", "identity.description",
       engine="no: el prompt solo la usa si falta `industry`, que el contrato exige", panel="pantalla"),
    _f("business.promise", "Propuesta de valor", "A", "identity.value_proposition", transform="renombrado",
       engine="sí: prompt (promesa comercial)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.positioning", "A quién se dirige y qué problema resuelve", "A", "identity.positioning"),
    _f("business.tone", "Tono de comunicación", "A", "response_style.tone", transform="cambia de sección", engine=NOT_IN_PROMPT, panel="modelo"),
    _f("business.voice", "Personalidad o voz de la marca", "A", "response_style.voice", transform="cambia de sección"),
    _f("business.city", "Ciudad", "E", "compatibility", note="Duplica `business.location.city` (mismo valor en los 9 negocios)."),
    _f("business.type", "Tipo de negocio", "E", "compatibility", note="Solo restaurant; repite el sector (`industry`) y el modelo de negocio del motor."),
    _f("business.location.**", "Ubicación y cobertura", "A", "identity.location.**", engine=NOT_IN_PROMPT, panel="modelo"),
    _f("business.service_modes", "Modalidades de atención", "A", "identity.service_modes", engine=NOT_IN_PROMPT, panel="modelo"),
    _f("business.differentiators", "Diferenciadores", "A", "identity.differentiators", engine=NOT_IN_PROMPT, panel="modelo"),
    _f("business.desired_outcomes", "Resultados que busca el cliente", "A", "sales.benefits", transform="renombrado y cambia de sección",
       engine=NOT_IN_PROMPT, panel="modelo"),
    _f("business.pain_points", "Problemas del cliente en sus palabras", "A", "sales.pain_points", transform="cambia de sección"),
    _f("business.customer_profile.**", "Cliente ideal", "A", "identity.target_customer.**", transform="renombrado"),
    _f("business.credibility", "Pruebas de confianza", "A", "identity.credibility"),
    _f("business.value_drivers.<motivo>.description", "Qué significa cada motivo de compra", "B",
       "sales.motivation_drivers[motivation=<motivo>].description", transform="mapa por motivo → lista con `motivation`"),
    _f("business.value_drivers.<motivo>.triggers", "Frases que revelan cada motivo", "B",
       "sales.motivation_drivers[motivation=<motivo>].signals", transform="mapa por motivo → lista; `triggers` → `signals`"),
    _f("business.use_cases[].nombre", "Caso de uso típico", "B", "sales.use_cases[{i}].name", transform="`nombre` → `name`",
       engine="sí: respaldo de 'Casos típicos' si no hay impactos", evidence=[ENGINE_TEST]),
    _f("business.use_cases[].senales", "Señales del caso de uso", "B", "sales.use_cases[{i}].signals", transform="`senales` → `signals`"),
    _f("business.use_cases[].enfoque", "Enfoque de la solución para el caso", "B", "sales.use_cases[{i}].approach", transform="`enfoque` → `approach`"),
    _f("business.buying_motivation.primary", "Motivo principal de compra", "A", "sales.buying_motivation.primary", transform="cambia de sección",
       engine="sí: prompt (motores de compra)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.buying_motivation.secondary", "Motivo secundario de compra", "A", "sales.buying_motivation.secondary", transform="cambia de sección",
       engine="sí: prompt (motores de compra)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.logistics.**", "Domicilio, envío, recogida y agenda", "A", "fulfillment.**", transform="sección propia `fulfillment`"),
    # ------------------------------------------------------------------ sales.yaml
    _f("sales.pain.clusters.<problema>.impacts", "Impactos del problema", "A", "sales.customer_problems[id=<problema>].impacts",
       transform="mapa por problema → lista con `id`", engine="sí: prompt (casos típicos)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.pain.clusters.<problema>.signals", "Frases que revelan el problema", "B", "sales.customer_problems[id=<problema>].signals",
       transform="mapa por problema → lista con `id`"),
    _f("sales.pain.clusters.<problema>.monetization", "Cuánto le cuesta el problema al cliente", "B",
       "sales.customer_problems[id=<problema>].monetization", transform="mapa por problema → lista con `id`"),
    _f("sales.pain.clusters.<problema>.urgency_levels.**", "Mensajes según la urgencia", "B",
       "sales.customer_problems[id=<problema>].urgency_levels.**", transform="mapa por problema → lista con `id`"),
    _f("sales.pain.clusters.<problema>.recommended_angles", "Ángulos de venta para el problema", "B",
       "sales.customer_problems[id=<problema>].recommended_angles", transform="mapa por problema → lista con `id`"),
    _f("sales.discovery.questions", "Preguntas de diagnóstico", "A", "sales.discovery.questions", engine=NOT_IN_PROMPT, panel="modelo"),
    _f("sales.discovery.objectives", "Qué debe averiguar el asistente", "B", "sales.discovery.objectives"),
    _f("sales.qualification.detect_offer_fit", "Comprobar que la oferta encaja con el cliente", "B", "sales.qualification.detect_offer_fit"),
    _f("sales.support.info_handling.explain_first", "Explicar antes de vender", "B", "sales.support.explain_first", transform="se aplana `info_handling`"),
    _f("sales.support.info_handling.sell_after", "Vender después de explicar", "B", "sales.support.sell_after", transform="se aplana `info_handling`"),
    _f("sales.support.hard_rules", "Reglas de atención", "B", "sales.support.rules", transform="`hard_rules` → `rules`"),
    _f("sales.angles.<motivo>.when", "Cuándo usar el ángulo de venta", "B", "sales.angles[motivation=<motivo>].signals",
       transform="mapa por motivo → lista; `when` → `signals`"),
    _f("sales.angles.<motivo>.execution", "Qué decir con el ángulo de venta", "B", "sales.angles[motivation=<motivo>].messages",
       transform="mapa por motivo → lista; `execution` → `messages`"),
    _f("sales.conversation_flow.steps", "Etapas de la conversación", "B", "sales.conversation_flow.steps"),
    _f("sales.conversation_flow.rules.no_skip_steps", "No saltar etapas", "B", "sales.conversation_flow.no_skip_steps", transform="se aplana `rules`"),
    _f("sales.conversation_flow.rules.guided_process", "Guiar un proceso paso a paso", "B", "sales.conversation_flow.guided_process",
       transform="se aplana `rules`"),
    _f("sales.solution.framing", "Argumentos de venta", "A", "sales.arguments", transform="renombrado", engine=NOT_IN_PROMPT, panel="modelo"),
    _f("sales.solution.mapping.<problema>", "Qué parte de la solución atiende cada problema", "B",
       "sales.solution.mapping[problem=<problema>].solutions", transform="mapa por problema → lista con `problem`"),
    _f("sales.solution.process_steps", "Pasos del proceso de compra o servicio", "A", "sales.solution.process_steps"),
    _f("sales.solution.requirements", "Requisitos del cliente", "A", "sales.solution.requirements"),
    _f("sales.offer.strategy.single", "Cómo presentar una sola opción", "B", "sales.offer_presentation.single_offer", transform="renombrado"),
    _f("sales.offer.strategy.multi", "Cómo presentar varias opciones", "B", "sales.offer_presentation.multiple_offers", transform="renombrado"),
    _f("sales.offer.recommendation_rules[].condition", "Situación que activa una recomendación", "B", "compatibility",
       note="Apunta a planes que no existen en el negocio (plan_pro, plan_basico). El contrato exige que "
            "`sales.recommendation_rules` apunte a la oferta real: requiere decisión del negocio."),
    _f("sales.offer.recommendation_rules[].recommend", "Plan recomendado", "B", "compatibility",
       note="Ver `condition`: referencia a un plan inexistente."),
    _f("sales.objection.<objecion>.layers.**", "Manejo de la objeción por capas", "B", "sales.objections[topic=<objecion>].**",
       transform="mapa por objeción → lista con `topic`; se aplana `layers`"),
    _f("sales.objection.<objecion>.hard_rules", "Reglas al responder la objeción", "B", "sales.objections[topic=<objecion>].rules",
       transform="`hard_rules` → `rules`"),
    _f("sales.closing.strategy", "Estrategia de cierre", "B", "sales.closing.strategy"),
    _f("sales.closing.required_data", "Datos que necesita el cierre", "B", "sales.closing.required_data",
       note="Se solapa con `capabilities.data_collection.fields`, que es lo que el motor pide hoy."),
    _f("sales.closing.triggers", "Señales de intención de compra", "B", "sales.closing.purchase_signals", transform="renombrado"),
    _f("sales.closing.actions.high_intent", "Acciones ante intención alta", "B", "sales.closing.high_intent_actions", transform="se aplana `actions`"),
    _f("sales.closing.next_steps", "Siguientes pasos", "B", "sales.closing.next_steps"),
    _f("sales.closing.micro_commitments", "Compromisos progresivos", "B", "sales.closing.micro_commitments"),
    _f("sales.closing.hard_rules", "Reglas de cierre", "B", "sales.closing.rules", transform="`hard_rules` → `rules`",
       note="En asesor_ai_prod tres reglas validan el texto de la respuesta (p. ej. que no contenga '?'); el motor no "
            "las aplica. Moverlas a las políticas del motor cambia las reglas del negocio: decisión pendiente."),
    _f("sales.closing.behavior.<estrategia>.goal", "Objetivo de cada estrategia de cierre", "E", "compatibility",
       note="Plantilla idéntica en los 9 negocios (estrategia → objetivo): es una política del motor, no un dato del negocio."),
    _f("sales.closing.next_step.action", "Modo del siguiente paso", "C", "compatibility", note="Vale `dynamic` en los 9 negocios; parámetro interno."),
    _f("sales.progression_rules.required_flow", "Flujo comercial obligatorio", "E", "compatibility",
       note="Idéntico en los 9 negocios y ya fijado en el prompt del motor (dolor → impacto → solución → acción)."),
    _f("sales.progression_rules.forbid", "Respuestas prohibidas por el flujo", "C", "compatibility", note="Códigos internos del motor (asesor_ai_prod, demo)."),
    # ------------------------------------------------------------------ pricing.yaml
    _f("pricing.model", "Venta por catálogo", "A", "offer.model", engine="sí: prompt (planes o categorías del catálogo)", panel="pantalla",
       evidence=[ISOLATION_TEST]),
    _f("pricing.plans[].id", "Identificador estable del plan", "A", "offer.plans[{i}].id", engine="sí: enlaza el plan con su pago",
       panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].name", "Nombre del plan", "A", "offer.plans[{i}].name", engine="sí: prompt (qué se cobra y precios)", panel="pantalla",
       evidence=["test_plan_prices_format_is_unchanged"]),
    _f("pricing.plans[].description", "Descripción del plan", "A", "offer.plans[{i}].description", engine=NOT_IN_PROMPT, panel="pantalla"),
    _f("pricing.plans[].pricing.<moneda>.**", "Precio del plan por moneda (instalación, mensual...)", "A",
       "offer.plans[{i}].prices[currency=<moneda>].**", transform="mapa por moneda → lista con `currency`", engine="sí: prompt (precios)",
       panel="pantalla", evidence=["test_plan_prices_format_is_unchanged", ENGINE_TEST]),
    _f("pricing.plans[].includes", "Qué incluye", "A", "offer.plans[{i}].includes", engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.plans[].not_included", "Qué no incluye", "A", "offer.plans[{i}].not_included", engine="sí: prompt", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("pricing.plans[].target", "Para quién es el plan", "A", "offer.plans[{i}].target"),
    _f("pricing.plans[].payment.link", "Link de pago", "D", "secret:payments[{i}].link", transform="valor → referencia `legacy_yaml:`",
       engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.enabled", "Transferencias activas", "A", "payments[{i}].transfer_enabled",
       transform="perfil de pago con el id del plan", engine="sí: métodos disponibles", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.methods[].type", "Método de transferencia", "A", "payments[{i}].transfer_methods[{j}].type",
       engine="sí: métodos disponibles", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.methods[].bank", "Banco", "A", "payments[{i}].transfer_methods[{j}].bank",
       engine="sí: mensaje de pago", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.methods[].account_type", "Tipo de cuenta", "A", "payments[{i}].transfer_methods[{j}].account_type",
       engine="sí: mensaje de pago", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.methods[].number", "Celular Nequi o Daviplata", "D", "secret:payments[{i}].transfer_methods[{j}].number",
       transform="valor → referencia `legacy_yaml:`", engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.methods[].account_number", "Número de cuenta", "D",
       "secret:payments[{i}].transfer_methods[{j}].account_number", transform="valor → referencia `legacy_yaml:`",
       engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].payment.transfer.methods[].reference", "Llave o referencia Bre-B", "D", "secret:payments[{i}].transfer_methods[{j}].reference",
       transform="valor → referencia `legacy_yaml:`", engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.categories[].id", "Identificador de la categoría", "A", "offer.catalog.categories[{i}].id",
       engine="sí: categorías con productos disponibles", panel="pantalla", evidence=[UNAVAILABLE_TEST]),
    _f("pricing.catalog.categories[].name", "Nombre de la categoría", "A", "offer.catalog.categories[{i}].name",
       engine="sí: prompt (primeras 4 categorías)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.catalog.items[].id", "Identificador estable del producto", "A", "offer.catalog.items[{i}].id", panel="pantalla"),
    _f("pricing.catalog.items[].name", "Nombre del producto", "A", "offer.catalog.items[{i}].name", panel="pantalla",
       engine="no: el prompt de catálogo no lista productos (dice 'valores definidos en pricing')"),
    _f("pricing.catalog.items[].category", "Categoría del producto", "A", "offer.catalog.items[{i}].category",
       engine="sí: decide qué categorías se ofrecen", panel="pantalla", evidence=["test_product_category_decides_which_categories_are_offered"]),
    _f("pricing.catalog.items[].description", "Descripción del producto", "A", "offer.catalog.items[{i}].description",
       engine=NOT_IN_PROMPT, panel="pantalla"),
    _f("pricing.catalog.items[].price.<moneda>", "Precio del producto por moneda", "A", "offer.catalog.items[{i}].prices[currency=<moneda>].amount",
       transform="mapa por moneda → lista con `currency` y `amount`", panel="pantalla",
       engine="no: el prompt de catálogo no lista precios (dice 'valores definidos en pricing')"),
    _f("pricing.catalog.payment.link", "Link de pago del catálogo", "D", "secret:payments[id=catalog].link", transform="valor → referencia `legacy_yaml:`",
       engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.enabled", "Transferencias activas", "A", "payments[id=catalog].transfer_enabled",
       transform="perfil de pago `catalog`", engine="sí: métodos disponibles", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.methods[].type", "Método de transferencia", "A", "payments[id=catalog].transfer_methods[{i}].type",
       engine="sí: métodos disponibles", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.methods[].bank", "Banco", "A", "payments[id=catalog].transfer_methods[{i}].bank",
       engine="sí: mensaje de pago", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.methods[].account_type", "Tipo de cuenta", "A", "payments[id=catalog].transfer_methods[{i}].account_type",
       engine="sí: mensaje de pago", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.methods[].number", "Celular Nequi o Daviplata", "D", "secret:payments[id=catalog].transfer_methods[{i}].number",
       transform="valor → referencia `legacy_yaml:`", engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.methods[].account_number", "Número de cuenta", "D",
       "secret:payments[id=catalog].transfer_methods[{i}].account_number", transform="valor → referencia `legacy_yaml:`",
       engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.catalog.payment.transfer.methods[].reference", "Llave o referencia Bre-B", "D",
       "secret:payments[id=catalog].transfer_methods[{i}].reference", transform="valor → referencia `legacy_yaml:`",
       engine="sí: el motor lo entrega al elegir el método", panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.conditions", "Condiciones comerciales", "A", "terms.conditions", transform="cambia de sección", engine="sí: prompt", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("pricing.price_framing.type", "Cómo presentar el precio", "B", "terms.price_framing", transform="se aplana `type`", engine="sí: prompt",
       evidence=[ENGINE_TEST]),
    _f("pricing.roi.break_even_sales", "Ventas para recuperar la inversión", "B", "terms.roi_break_even_sales", transform="se aplana `roi`",
       engine="sí: prompt", evidence=[ENGINE_TEST]),
    _f("pricing.roi.break_even_reservas", "Reservas para recuperar la inversión", "B", "terms.roi_break_even_bookings", transform="renombrado",
       note="Solo agencia_viajes; el motor solo lee `break_even_sales`."),
    _f("pricing.roi_hints", "Argumentos de retorno de la inversión", "B", "terms.roi_hints", transform="cambia de sección",
       engine="sí: prompt (si no hay break_even_sales)", evidence=[ENGINE_TEST]),
    _f("pricing.note", "Aclaración sobre cómo se confirma el precio", "A", "terms.price_note", transform="renombrado"),
    _f("pricing.business_offers.core", "Ofertas principales", "B", "sales.offer_mix.core", transform="cambia de sección"),
    _f("pricing.business_offers.upsell", "Mejoras para vender más", "B", "sales.offer_mix.upsell", transform="cambia de sección"),
    _f("pricing.business_offers.cross_sell", "Complementos para vender junto", "B", "sales.offer_mix.cross_sell", transform="cambia de sección"),
    _f("pricing.business_offers.financing.**", "Financiación", "A", "terms.financing.**", transform="cambia de sección"),
    # ------------------------------------------------------------------ inventory.yaml
    _f("inventory.items", "Inventario (vacío)", "A", "inventory.items",
       note="El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta."),
    _f("inventory.items[].**", "Producto con variantes y existencias", "A", "inventory.items[{i}].**",
       note="El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta."),
    _f("inventory.track_stock", "Controlar existencias", "A", "inventory.track_stock"),
    # ------------------------------------------------------------------ config.yaml
    _f("config.capabilities.actions.primary", "Acciones de venta", "A", "capabilities.actions_primary", transform="se aplana `actions`",
       engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.capabilities.actions.support", "Acciones de apoyo", "A", "capabilities.actions_support", transform="se aplana `actions`",
       engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.capabilities.business_channels.allowed", "Canales de atención", "A", "capabilities.service_channels", transform="renombrado",
       engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.capabilities.system_channels.allowed", "Canales por los que funciona el producto", "A", "capabilities.product_channels",
       transform="renombrado", engine="sí: prompt", evidence=[ENGINE_TEST]),
    _f("config.capabilities.channels", "Canales (lista antigua)", "E", "compatibility",
       note="Estructura antigua: el prompt solo la usa si no hay canales de atención ni del sistema, lo que no ocurre en "
            "ningún negocio. En asesor_ai_prod contradice a `business_channels` (vacío)."),
    _f("config.capabilities.closing_methods.link_payment.enabled", "Cerrar enviando el pago", "A", "capabilities.closing_methods.payment_link",
       transform="renombrado", engine="sí: prompt", panel="pantalla", evidence=["test_closing_and_data_collection_toggles_change_the_prompt"]),
    _f("config.capabilities.closing_methods.human_handoff.enabled", "Pasar a una persona", "A", "capabilities.closing_methods.human_handoff",
       engine="sí: prompt (nadie del equipo recibe aviso)", panel="pantalla", evidence=["test_closing_and_data_collection_toggles_change_the_prompt"]),
    _f("config.capabilities.closing_methods.data_collection.enabled", "Cerrar pidiendo datos", "A", "capabilities.closing_methods.data_collection",
       engine="sí: prompt", panel="pantalla", evidence=["test_closing_and_data_collection_toggles_change_the_prompt"]),
    _f("config.capabilities.data_collection.enabled", "Pedir datos al cliente", "A", "capabilities.data_collection.enabled",
       engine="sí: prompt", panel="pantalla", evidence=["test_closing_and_data_collection_toggles_change_the_prompt"]),
    _f("config.capabilities.data_collection.fields", "Datos que se piden", "A", "capabilities.data_collection.fields",
       engine="sí: prompt", panel="pantalla", evidence=["test_closing_and_data_collection_toggles_change_the_prompt"]),
    _f("config.capabilities.constraints.**", "Canales y acciones que el negocio no ofrece", "A", "capabilities.restrictions.**", transform="renombrado"),
    _f("config.conversation.**", "Ventanas de la conversación", "C", "engine.conversation.**", transform="sección interna `engine`",
       engine="sí: estado y reinicio de la conversación", evidence=["test_conversation_windows_drive_the_conversation_state"]),
    _f("config.features.pricing_enabled", "Mostrar precios", "C", "engine.features.pricing_enabled", transform="sección interna `engine`",
       note="El prompt solo lo consulta si no hay precios ni pagos, algo que el contrato no permite (toda oferta tiene precio)."),
    _f("config.features.catalog_mode", "Modo catálogo", "C", "engine.features.catalog_mode", transform="sección interna `engine`",
       engine="sí: prompt (cuándo mostrar precios)", evidence=[ENGINE_TEST]),
    _f("config.features.business_model", "Modelo de negocio", "C", "engine.features.business_model", transform="sección interna `engine`",
       engine="sí: prompt (cuándo mostrar precios)", evidence=[ENGINE_TEST]),
    _f("config.features.multi_currency", "Varias monedas", "E", "compatibility",
       note="Derivable de los precios; contradice la oferta en agencia_viajes (true con una sola moneda)."),
    _f("config.features.multi_plan", "Varios planes", "E", "compatibility",
       note="Derivable de la oferta; contradice la oferta en asesor_ai_prod, clinic y saas (true con un solo plan)."),
    _f("config.flags.**", "Banderas internas (ai_first, allow_fallback, log_level)", "C", "compatibility",
       note="Sin consumidor en el motor; no son decisiones del negocio."),
    _f("config.initial_message.enabled", "Mensaje de bienvenida activo", "A", "messages.welcome.enabled", engine="sí: primer mensaje", panel="pantalla",
       evidence=["test_welcome_message_toggle"]),
    _f("config.initial_message.text", "Texto de bienvenida", "A", "messages.welcome.text", engine="sí: primer mensaje", panel="pantalla",
       evidence=["test_welcome_message_toggle"]),
    _f("config.initial_message.recency.**", "Ventanas del mensaje inicial (antiguas)", "E", "compatibility",
       note="Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h)."),
    _f("config.post_payment.on_user_report.message", "Respuesta al reportar un pago", "A", "messages.payment_reported", transform="renombrado",
       engine="sí: respuesta exacta", panel="pantalla", evidence=["test_payment_report_message_is_optional"]),
    _f("config.post_payment.on_payment_confirmed.message", "Mensaje de pago confirmado", "A", "messages.payment_confirmed", transform="renombrado",
       engine="sí: prompt post-pago", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.response.length", "Largo de las respuestas", "A", "response_style.length", engine="sí: prompt y recorte", panel="pantalla",
       evidence=["test_each_response_length_option_controls_prompt_and_truncation"]),
    _f("config.response.max_words", "Límite avanzado de palabras", "B", "response_style.max_words", engine="sí: prompt y recorte", panel="modelo",
       evidence=["test_changing_the_contract_changes_response_length"]),
)


# Campos del contrato sin origen en los YAML (o cuyo origen queda en compatibilidad): qué son y si el
# panel los ofrece. Su estado en el motor (`x-engine`) y su audiencia (`x-audience`) salen del esquema.
NEW_CONTRACT_FIELDS: dict[str, tuple[str, str]] = {
    # ruta normalizada: (significado, interfaz)
    "identity.brand_name": ("Marca distinta del nombre", "modelo"),
    "identity.opening_hours[].days": ("Días de atención", "no"),
    "identity.opening_hours[].opens": ("Hora de apertura", "no"),
    "identity.opening_hours[].closes": ("Hora de cierre", "no"),
    "offer.plans[].prices[].first_payment": ("Valor del primer pago", "no"),
    "offer.plans[].prices[].price": ("Precio de pago único", "pantalla"),
    "offer.plans[].prices[].annual": ("Cobro anual", "no"),
    "offer.plans[].available": ("Plan disponible", "pantalla"),
    "offer.catalog.items[].features": ("Características del producto", "pantalla"),
    "offer.catalog.items[].available": ("Producto disponible", "pantalla"),
    "terms.prices_include_taxes": ("Precios con impuestos incluidos", "no"),
    "terms.promotions[].name": ("Nombre de la promoción", "modelo"),
    "terms.promotions[].details": ("Detalle de la promoción", "modelo"),
    "terms.promotions[].valid_until": ("Vigencia de la promoción", "modelo"),
    "terms.policies.warranty": ("Política de garantía", "no"),
    "terms.policies.returns": ("Política de cambios y devoluciones", "no"),
    "terms.policies.cancellation": ("Política de cancelación y reembolso", "no"),
    "payments[].instructions": ("Indicaciones para pagar", "no"),
    "sales.qualification.criteria": ("Criterios de calificación", "no"),
    "sales.recommendation_rules[].when": ("Situación del cliente", "modelo"),
    "sales.recommendation_rules[].recommend": ("Oferta recomendada", "modelo"),
    "sales.instructions": ("Instrucciones de venta", "modelo"),
    "capabilities.data_collection.consent_notice": ("Aviso de tratamiento de datos", "no"),
    "capabilities.human_handoff_when": ("Cuándo pasar a una persona", "no"),
    "capabilities.restrictions.forbidden_claims": ("Promesas prohibidas", "no"),
    "messages.after_sale": ("Mensaje después de la compra", "no"),
    "messages.data_request": ("Mensaje para pedir datos", "no"),
    "messages.follow_up": ("Mensaje de seguimiento", "no"),
    "messages.human_handoff": ("Mensaje al pasar a una persona", "no"),
    "response_style.formality": ("Nivel de formalidad", "no"),
    "response_style.emojis": ("Uso de emojis", "no"),
    "response_style.instructions": ("Indicaciones de comunicación", "no"),
    "knowledge.faqs[].question": ("Pregunta frecuente", "pantalla"),
    "knowledge.faqs[].answer": ("Respuesta oficial", "pantalla"),
    "inventory.items[].variants[].prices[].currency": ("Moneda del precio de la variante", "no"),
    "inventory.items[].variants[].prices[].amount": ("Precio de la variante", "no"),
}

# Campos del contrato que llegan desde una ruta antigua con forma derivada (se cubren aunque su
# ruta no aparezca literalmente en un destino del catálogo).
DERIVED_CONTRACT_FIELDS: dict[str, str] = {
    "schema_version": "Versión del contrato",
    "tenant_slug": "Negocio dueño del documento",
    "sales.customer_problems[].id": "Clave del problema en `sales.pain.clusters`",
    "sales.motivation_drivers[].motivation": "Clave del motivo en `business.value_drivers`",
    "sales.angles[].motivation": "Clave del motivo en `sales.angles`",
    "sales.objections[].topic": "Clave de la objeción en `sales.objection`",
    "sales.solution.mapping[].problem": "Clave del problema en `sales.solution.mapping`",
    "offer.plans[].prices[].currency": "Clave de moneda en `pricing.plans[].pricing`",
    "offer.catalog.items[].prices[].currency": "Clave de moneda en `pricing.catalog.items[].price`",
    "payments[].id": "Perfil de pago creado por la importación (id del plan o `catalog`)",
    "offer.plans[].payment_profile": "Enlace del plan con su perfil de pago",
    "offer.catalog.payment_profile": "Enlace del catálogo con su perfil de pago",
    "compatibility": "Datos antiguos sin lugar en el contrato",
}


# ---------------------------------------------------------------------------
# Recorrido de los YAML y resolución de destinos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LegacyLeaf:
    pattern: str
    path: str
    indices: tuple[int, ...]
    keys: dict[str, str]
    value: Any


def legacy_leaves(sections: dict[str, dict]) -> Iterator[LegacyLeaf]:
    """Campos hoja de los YAML: escalares, listas de valores simples y contenedores vacíos."""

    def _walk(node: Any, pattern: str, path: str, indices: tuple[int, ...], keys: dict[str, str]) -> Iterator[LegacyLeaf]:
        if isinstance(node, dict) and node:
            marker = DYNAMIC_KEYS.get(pattern)
            for key, value in node.items():
                child_pattern = marker or key
                child_keys = {**keys, marker.strip("<>"): str(key)} if marker else keys
                yield from _walk(value, f"{pattern}.{child_pattern}" if pattern else str(child_pattern), f"{path}.{key}" if path else str(key), indices, child_keys)
        elif isinstance(node, list) and node and all(isinstance(item, dict) for item in node):
            for index, item in enumerate(node):
                yield from _walk(item, f"{pattern}[]", f"{path}.{index}", indices + (index,), keys)
        else:
            yield LegacyLeaf(pattern, path, indices, keys, node)

    yield from _walk(sections, "", "", (), {})


def find_entry(pattern: str) -> LegacyField | None:
    """Entrada del catálogo para un patrón: la exacta o, si no, la `.**` de prefijo más largo."""
    for entry in CATALOG:
        if entry.pattern == pattern:
            return entry
    wildcard = [entry for entry in CATALOG if entry.pattern.endswith(".**") and pattern.startswith(entry.pattern[:-2])]
    return max(wildcard, key=lambda entry: len(entry.pattern), default=None)


_SEGMENT = re.compile(r"([^.\[\]]+)|\[([^\]]*)\]")


def resolve_path(document: Any, path: str) -> Any:
    """Valor en `path` (`a.b[2].c[campo=valor]`); None si no existe."""
    node = document
    for name, selector in _SEGMENT.findall(path):
        if name:
            node = node.get(name) if isinstance(node, dict) else None
        elif "=" in selector:
            field_name, expected = selector.split("=", 1)
            node = next((item for item in node if isinstance(item, dict) and str(item.get(field_name)) == expected), None) if isinstance(node, list) else None
        else:
            index = int(selector)
            node = node[index] if isinstance(node, list) and index < len(node) else None
        if node is None:
            return None
    return node


def destination_path(entry: LegacyField, leaf: LegacyLeaf) -> str:
    """Ruta concreta del destino en el documento del contrato."""
    destination = entry.destination.removeprefix("secret:")
    if entry.kind == "compatibility":
        concrete = ".".join(f"[{part}]" if part.isdigit() else part for part in leaf.path.split("."))
        return f"compatibility.{concrete}".replace(".[", "[")
    indices = list(leaf.indices)
    if entry.pattern.endswith(".**"):
        prefix = entry.pattern[:-3]
        consumed = prefix.count("[]")
        suffix = leaf.pattern[len(prefix) + 1:]
        remaining = indices[consumed:]
        for marker in re.findall(r"<[^>]+>", suffix):
            suffix = suffix.replace(marker, leaf.keys[marker.strip("<>")], 1)
        for index in remaining:
            suffix = suffix.replace("[]", f"[{index}]", 1)
        destination = destination[:-2] + suffix
        indices = indices[:consumed]
    for name, index in zip(("{i}", "{j}"), indices):
        destination = destination.replace(name, str(index))
    for key, value in leaf.keys.items():
        destination = destination.replace(f"<{key}>", value)
    return destination


def check_leaf(document: dict, leaf: LegacyLeaf) -> str | None:
    """None si el valor del campo antiguo está en su destino; si no, la descripción del problema."""
    entry = find_entry(leaf.pattern)
    if entry is None:
        return f"{leaf.path}: campo sin catalogar ({leaf.pattern})"
    path = destination_path(entry, leaf)
    found = resolve_path(document, path)
    if entry.kind == "secret":
        expected = None if str(leaf.value or "").strip() == "" else {"secret_ref": f"legacy_yaml:{leaf.path}"}
    else:
        expected = leaf.value
    if found != expected:
        return f"{leaf.path}: se esperaba {'una referencia' if entry.kind == 'secret' else 'el valor original'} en {path}"
    return None


# ---------------------------------------------------------------------------
# Campos del contrato (desde el JSON Schema publicado)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContractField:
    path: str
    audience: str
    engine: str
    description: str


def contract_fields(schema: dict) -> dict[str, ContractField]:
    """Campos hoja del contrato (`a.b[].c`) con su audiencia y su estado en el motor.

    Los mapas libres, las listas de valores y las referencias a secretos (`SecretRef`) son hojas.
    `x-audience` y `x-engine` se heredan del nivel más cercano que los declara; sin ninguno, el campo
    está `pendiente` (representado, sin uso en el motor actual).
    """
    definitions = schema.get("$defs", {})

    def _deref(node: dict) -> dict:
        while "$ref" in node:
            node = definitions[node["$ref"].rsplit("/", 1)[-1]]
        options = [option for option in node.get("anyOf", []) if option.get("type") != "null"]
        return _deref(options[0]) if len(options) == 1 else node

    fields: dict[str, ContractField] = {}

    def _walk(node: dict, path: str, audience: str, engine: str, description: str) -> None:
        audience = node.get("x-audience", audience)
        engine = node.get("x-engine", engine)
        description = node.get("description", description) if path else ""
        target = _deref(node)
        if target.get("type") == "object" and target.get("properties") and set(target["properties"]) != {"secret_ref"}:
            for name, child in target["properties"].items():
                _walk(child, f"{path}.{name}" if path else name, audience, engine, "")
        elif target.get("type") == "array" and _deref(target.get("items", {})).get("properties"):
            _walk(target["items"], f"{path}[]", audience, engine, description)
        else:
            fields[path] = ContractField(path, audience, engine, " ".join(description.split()))

    _walk(schema, "", "sistema", "pendiente", "")
    return fields


def contract_leaf_paths(schema: dict) -> set[str]:
    """Rutas hoja del contrato (`a.b[].c`)."""
    return set(contract_fields(schema))


def normalize_path(path: str) -> str:
    """Ruta concreta del contrato → forma del esquema (`offer.plans[0].prices[currency=COP]` → `offer.plans[].prices[]`)."""
    return re.sub(r"\[[^\]]*\]", "[]", path)


def covering_leaf(path: str, leaves: set[str]) -> str | None:
    """Hoja del esquema que contiene la ruta (ella misma o un mapa libre que la incluye).

    Si la ruta es una lista u objeto del contrato (p. ej. una lista vacía en el origen), devuelve la propia ruta.
    """
    normalized = normalize_path(path)
    covering = next((leaf for leaf in leaves if normalized == leaf or normalized.startswith(f"{leaf}.")), None)
    if covering is None and any(leaf.startswith((f"{normalized}[", f"{normalized}.")) for leaf in leaves):
        return normalized
    return covering
