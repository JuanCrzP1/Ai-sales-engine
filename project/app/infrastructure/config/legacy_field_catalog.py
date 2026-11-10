"""Catálogo de los campos de los YAML antiguos y su lugar en BusinessConfig v1.

Fuente de la matriz de trazabilidad (`docs/business-config-traceability.md`, generada con
`scripts/generate_traceability_matrix.py`). Las pruebas recorren los cinco YAML de los nueve negocios
y comprueban que cada campo está catalogado y que su valor aparece de verdad en el destino declarado.

Patrones de origen: `[]` es un índice de lista y `<nombre>` una clave variable (id de problema,
moneda...). `.**` al final abarca todos los campos que cuelgan de la ruta, que conservan su nombre
en el destino.
Destinos: ruta del contrato, donde `[{i}]` y `[{j}]` son los índices del origen y
`[campo=<nombre>]` busca en una lista por clave; `engine_settings.<ruta>` (ajustes técnicos, fuera
del documento comercial; `engine_settings.legacy` conserva la ruta original); `secret:<ruta>`
(referencia `legacy_yaml:` al valor, nunca el valor) o `engine_policy` (definición común a todos los
negocios: no está en ningún documento y la aporta el compilador).

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

from app.domain.business_config.engine_policy import COMMON_CLOSING_POLICY

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
ISOLATION_TEST = "test_tenants_stay_isolated"
UNAVAILABLE_TEST = "test_unavailable_offer_is_not_offered"
NOT_IN_PROMPT = "no: el prompt actual no lo usa"
# Perfil comercial del prompt (`app/infrastructure/ai/prompting/sections/business.py` y siguientes): solo con la configuración del contrato.
IN_PROFILE = "sí: perfil comercial del prompt, con la configuración del contrato"
PROFILE_TEST = "test_each_profile_option_reaches_the_prompt"
CATALOG_PRICES_TEST = "test_catalog_prices_reach_the_prompt"
LEGACY_DESTINATION = "engine_settings.legacy"
POLICY_DESTINATION = "engine_policy"


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
    def kind(self) -> Literal["typed", "technical", "secret", "policy"]:
        if self.destination == POLICY_DESTINATION:
            return "policy"
        if self.destination.startswith("engine_settings."):
            return "technical"
        return "secret" if self.destination.startswith("secret:") else "typed"


def _f(pattern: str, meaning: str, category: Category, destination: str, **extra: Any) -> LegacyField:
    evidence = extra.pop("evidence", ())
    return LegacyField(pattern, meaning, category, destination, evidence=tuple(evidence) if isinstance(evidence, (list, tuple)) else (evidence,), **extra)


CATALOG: tuple[LegacyField, ...] = (
    # ------------------------------------------------------------------ business.yaml
    _f("business.name", "Nombre comercial", "A", "identity.name", engine=IN_PROFILE, panel="pantalla",
       evidence=["test_the_profile_block_reaches_the_prompt"]),
    _f("business.brand_name", "Marca", "A", "identity.brand_name", engine=IN_PROFILE, evidence=[PROFILE_TEST],
       note="Igual a `name` en los 9 negocios; se conserva su valor."),
    _f("business.industry", "Sector o tipo de negocio", "A", "identity.industry", engine="sí: prompt (sector)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.description", "Descripción del negocio", "A", "identity.description",
       engine=f"{IN_PROFILE} (y en el contexto del negocio si falta `industry`)", panel="pantalla",
       evidence=["test_removing_profile_options_removes_them_from_the_prompt"]),
    _f("business.promise", "Propuesta de valor", "A", "identity.value_proposition", transform="renombrado",
       engine="sí: prompt (promesa comercial)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.positioning", "A quién se dirige y qué problema resuelve", "A", "identity.positioning",
       engine="sí: prompt (EL NEGOCIO, posicionamiento)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.tone", "Tono de comunicación", "A", "response_style.tone", transform="cambia de sección",
       engine="sí: línea ESTILO del prompt, con la configuración del contrato", panel="modelo", evidence=[ENGINE_TEST]),
    _f("business.voice", "Personalidad o voz de la marca", "A", "response_style.voice", transform="cambia de sección",
       engine="sí: prompt (personalidad de la marca)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.city", "Ciudad", "E", "identity.location.city", transform="duplicado unificado con `business.location.city`",
       engine=IN_PROFILE, evidence=[PROFILE_TEST],
       note="Mismo valor que `business.location.city` en los 9 negocios: el contrato la guarda una sola vez y la compilación la devuelve a las dos rutas."),
    _f("business.type", "Tipo de negocio", "E", LEGACY_DESTINATION, note="Solo restaurant; repite el sector (`industry`) y el tipo de negocio de `features`."),
    _f("business.location.**", "Ubicación y cobertura", "A", "identity.location.**", engine=IN_PROFILE, panel="modelo", evidence=[PROFILE_TEST]),
    _f("business.service_modes", "Modalidades de atención", "A", "identity.service_modes", engine=IN_PROFILE, panel="modelo",
       evidence=[PROFILE_TEST]),
    _f("business.differentiators", "Diferenciadores", "A", "identity.differentiators", engine=IN_PROFILE, panel="modelo",
       evidence=[PROFILE_TEST]),
    _f("business.desired_outcomes", "Resultados que busca el cliente", "A", "sales.benefits", transform="renombrado y cambia de sección",
       engine=IN_PROFILE, panel="modelo", evidence=[PROFILE_TEST]),
    _f("business.pain_points", "Problemas del cliente en sus palabras", "A", "sales.pain_points", transform="cambia de sección",
       engine="sí: prompt (EL CLIENTE, cómo describe sus problemas)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.customer_profile.**", "Cliente ideal", "A", "identity.target_customer.**", transform="renombrado",
       engine="sí: prompt (cliente ideal)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.credibility", "Pruebas de confianza", "A", "identity.credibility", engine="sí: prompt (pruebas de confianza)",
       panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.value_drivers.<motivo>.description", "Qué significa cada motivo de compra", "B",
       "sales.motivations[motivation=<motivo>].description", transform="mapa por motivo → lista con `motivation`; se une con `sales.angles`",
       engine="sí: prompt (motivos de compra)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.value_drivers.<motivo>.triggers", "Frases que revelan cada motivo", "B", "sales.motivations[motivation=<motivo>].signals",
       transform="mapa por motivo → lista; `triggers` → `signals`; se une con `sales.angles`", engine="sí: prompt (motivos de compra)",
       panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.use_cases[].nombre", "Caso de uso típico", "B", "sales.use_cases[{i}].name", transform="`nombre` → `name`",
       engine="sí: respaldo de 'Casos típicos' si no hay impactos", evidence=[ENGINE_TEST]),
    _f("business.use_cases[].senales", "Señales del caso de uso", "B", "sales.use_cases[{i}].signals", transform="`senales` → `signals`",
       engine="sí: prompt (casos típicos)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.use_cases[].enfoque", "Enfoque de la solución para el caso", "B", "sales.use_cases[{i}].approach",
       transform="`enfoque` → `approach`", engine="sí: prompt (casos típicos)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.buying_motivation.primary", "Motivo principal de compra", "A", "sales.buying_motivation.primary", transform="cambia de sección",
       engine="sí: prompt (motores de compra)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.buying_motivation.secondary", "Motivo secundario de compra", "A", "sales.buying_motivation.secondary", transform="cambia de sección",
       engine="sí: prompt (motores de compra)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("business.logistics.**", "Domicilio, envío, recogida y agenda", "A", "fulfillment.**", transform="sección propia `fulfillment`",
       engine="sí: prompt (CÓMO COMPRA Y RECIBE EL CLIENTE)", panel="pantalla", evidence=[ENGINE_TEST]),
    # ------------------------------------------------------------------ sales.yaml
    _f("sales.pain.clusters.<problema>.impacts", "Impactos del problema", "A", "sales.customer_problems[id=<problema>].impacts",
       transform="mapa por problema → lista con `id`", engine="sí: prompt (casos típicos)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.pain.clusters.<problema>.signals", "Frases que revelan el problema", "B", "sales.customer_problems[id=<problema>].signals",
       transform="mapa por problema → lista con `id`", engine="sí: prompt (problemas del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.pain.clusters.<problema>.monetization", "Cuánto le cuesta el problema al cliente", "B",
       "sales.customer_problems[id=<problema>].monetization", transform="mapa por problema → lista con `id`",
       engine="sí: prompt (problemas del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.pain.clusters.<problema>.urgency_levels.**", "Mensajes según la urgencia", "B",
       "sales.customer_problems[id=<problema>].urgency_levels.**", transform="mapa por problema → lista con `id`",
       engine="sí: prompt (problemas del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.pain.clusters.<problema>.recommended_angles", "Ángulos de venta para el problema", "B",
       "sales.customer_problems[id=<problema>].recommended_angles", transform="mapa por problema → lista con `id`",
       engine="sí: prompt (problemas del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.discovery.questions", "Preguntas de diagnóstico", "A", "sales.discovery.questions", engine=IN_PROFILE, panel="modelo",
       evidence=[PROFILE_TEST]),
    _f("sales.discovery.objectives", "Qué debe averiguar el asistente", "B", "sales.discovery.objectives",
       engine="sí: prompt (qué averiguar del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.qualification.detect_offer_fit", "Comprobar que la oferta encaja con el cliente", "B", "sales.qualification.detect_offer_fit",
       engine="sí: prompt (estrategia de venta)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.support.info_handling.explain_first", "Explicar antes de vender", "B", "sales.support.explain_first",
       transform="se aplana `info_handling`", engine="sí: prompt (cómo atender una pregunta)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.support.info_handling.sell_after", "Vender después de explicar", "B", "sales.support.sell_after",
       transform="se aplana `info_handling`", engine="sí: prompt (cómo atender una pregunta)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.support.hard_rules", "Reglas de atención", "B", "sales.support.rules", transform="`hard_rules` → `rules`",
       engine="sí: prompt (reglas de atención)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.angles.<motivo>.when", "Cuándo usar el ángulo de venta", "B", "sales.motivations[motivation=<motivo>].angle.signals",
       transform="se une con `business.value_drivers`; `when` → `signals`", engine="sí: prompt (motivos de compra)", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("sales.angles.<motivo>.execution", "Qué decir con el ángulo de venta", "B", "sales.motivations[motivation=<motivo>].angle.messages",
       transform="se une con `business.value_drivers`; `execution` → `messages`", engine="sí: prompt (motivos de compra)", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("sales.conversation_flow.steps", "Etapas de la conversación", "B", "sales.conversation_flow.steps",
       engine="sí: prompt (orden de la conversación)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.conversation_flow.rules.no_skip_steps", "No saltar etapas", "B", "sales.conversation_flow.no_skip_steps",
       transform="se aplana `rules`", engine="sí: prompt (orden de la conversación)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.conversation_flow.rules.guided_process", "Guiar un proceso paso a paso", "B", "sales.conversation_flow.guided_process",
       transform="se aplana `rules`", engine="sí: prompt (orden de la conversación)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.solution.framing", "Argumentos de venta", "A", "sales.arguments", transform="renombrado", engine=IN_PROFILE, panel="modelo",
       evidence=[PROFILE_TEST]),
    _f("sales.solution.mapping.<problema>", "Qué parte de la solución atiende cada problema", "B",
       "sales.customer_problems[id=<problema>].solutions", transform="se une con `sales.pain.clusters`, que usa la misma clave de problema",
       engine="sí: prompt (problemas del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.solution.process_steps", "Pasos del proceso de compra o servicio", "A", "sales.solution.process_steps",
       engine="sí: prompt (pasos para comprar)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.solution.requirements", "Requisitos del cliente", "A", "sales.solution.requirements",
       engine="sí: prompt (requisitos del cliente)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.offer.strategy.single", "Cómo presentar una sola opción", "B", "sales.offer_presentation.single_offer", transform="renombrado",
       engine="sí: prompt (cómo presentar las opciones)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.offer.strategy.multi", "Cómo presentar varias opciones", "B", "sales.offer_presentation.multiple_offers", transform="renombrado",
       engine="sí: prompt (cómo presentar las opciones)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.offer.recommendation_rules[].condition", "Situación que activa una recomendación", "B", "sales.recommendation_rules[{i}].when",
       transform="`condition` → `when`", engine=IN_PROFILE, evidence=[PROFILE_TEST]),
    _f("sales.offer.recommendation_rules[].recommend", "Plan recomendado", "B", "sales.recommendation_rules[{i}].recommend",
       engine=IN_PROFILE, evidence=[PROFILE_TEST],
       note="En asesor_ai_prod (una) y demo (las dos) apunta a planes que no existen: se conserva, lo señala el diagnóstico"
            " `recomienda_oferta_no_disponible` y el motor no la recomienda."),
    _f("sales.objection.<objecion>.layers.**", "Manejo de la objeción por capas", "B", "sales.objections[topic=<objecion>].**",
       transform="mapa por objeción → lista con `topic`; se aplana `layers`", engine="sí: prompt (cuando el cliente duda)", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("sales.objection.<objecion>.hard_rules", "Reglas al responder la objeción", "B", "sales.objections[topic=<objecion>].rules",
       transform="`hard_rules` → `rules`", engine="sí: prompt (cuando el cliente duda)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.closing.strategy", "Estrategia de cierre", "B", "sales.closing.strategy",
       engine="sí: manual por tipo de negocio (`booking` → servicios con cita)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.closing.required_data", "Datos que necesita el cierre", "B", "sales.closing.required_data",
       engine="sí: prompt (datos para cerrar, junto con `data_collection.fields`)", panel="pantalla", evidence=[ENGINE_TEST],
       note="Se une con `capabilities.data_collection.fields` en una sola lista, en español y sin repetir."),
    _f("sales.closing.triggers", "Señales de intención de compra", "B", "sales.closing.purchase_signals", transform="renombrado",
       engine="sí: prompt (señales de compra)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.closing.actions.high_intent", "Acciones ante intención alta", "B", "sales.closing.high_intent_actions",
       transform="se aplana `actions`", engine="sí: prompt (intención de compra alta)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.closing.next_steps", "Siguientes pasos", "B", "sales.closing.next_steps", engine="sí: prompt (siguientes pasos de la venta)",
       panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.closing.micro_commitments", "Compromisos progresivos", "B", "sales.closing.micro_commitments",
       engine="sí: prompt (compromisos pequeños)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("sales.closing.hard_rules", "Reglas de cierre", "B", "sales.closing.rules", transform="`hard_rules` → `rules`",
       engine="sí: prompt (reglas de cierre)", panel="pantalla", evidence=[ENGINE_TEST],
       note="En asesor_ai_prod tres reglas hablan del texto de la respuesta (p. ej. que no contenga '?'): llegan a la IA como reglas del negocio, tal como las escribió; el motor no las valida aparte."),
    _f("sales.closing.behavior.<estrategia>.goal", "Objetivo de cada tipo de cierre", "E", POLICY_DESTINATION,
       note="Definición común: mismo valor en los 9 negocios, que tienen los cuatro objetivos aunque usen un solo tipo de cierre. Cambiarlo no altera el motor."),
    _f("sales.closing.next_step.action", "Modo del siguiente paso", "C", POLICY_DESTINATION,
       note="Definición común: vale `dynamic` en los 9 negocios y describe cómo funciona el motor; el siguiente paso sale de la respuesta de la IA."),
    _f("sales.progression_rules.required_flow", "Secuencia mínima de la conversación", "B", "sales.conversation_flow.required_flow",
       transform="se une con `sales.conversation_flow`", engine="sí: prompt (pasos que no pueden faltar)", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("sales.progression_rules.forbid", "Lo que el asistente no debe hacer", "B", "sales.conversation_flow.forbid",
       transform="se une con `sales.conversation_flow`", engine="sí: prompt (lo que no debe hacer)", panel="pantalla", evidence=[ENGINE_TEST]),
    # ------------------------------------------------------------------ pricing.yaml
    _f("pricing.model", "Venta por catálogo", "A", "offer.model", engine="sí: prompt (planes o categorías del catálogo)", panel="pantalla",
       evidence=[ISOLATION_TEST]),
    _f("pricing.plans[].id", "Identificador estable del plan", "A", "offer.plans[{i}].id", engine="sí: enlaza el plan con su pago",
       panel="pantalla", evidence=[PAYMENT_TEST]),
    _f("pricing.plans[].name", "Nombre del plan", "A", "offer.plans[{i}].name", engine="sí: prompt (qué se cobra y precios)", panel="pantalla",
       evidence=["test_plan_prices_are_said_like_a_salesperson_would"]),
    _f("pricing.plans[].description", "Descripción del plan", "A", "offer.plans[{i}].description", panel="pantalla", evidence=[ENGINE_TEST],
       engine=f"{IN_PROFILE} (detalle de la oferta)"),
    _f("pricing.plans[].pricing.<moneda>.**", "Precio del plan por moneda (instalación, mensual...)", "A",
       "offer.plans[{i}].prices[currency=<moneda>].**", transform="mapa por moneda → lista con `currency`", engine="sí: prompt (precios)",
       panel="pantalla", evidence=["test_plan_prices_are_said_like_a_salesperson_would", ENGINE_TEST]),
    _f("pricing.plans[].includes", "Qué incluye", "A", "offer.plans[{i}].includes", engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.plans[].not_included", "Qué no incluye", "A", "offer.plans[{i}].not_included", engine="sí: prompt", panel="pantalla",
       evidence=[ENGINE_TEST]),
    _f("pricing.plans[].target", "Para quién es el plan", "A", "offer.plans[{i}].target", engine="sí: prompt (para quién es el plan)",
       panel="pantalla", evidence=[ENGINE_TEST]),
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
    _f("pricing.catalog.items[].id", "Identificador estable del producto", "A", "offer.catalog.items[{i}].id", panel="pantalla",
       engine=f"{IN_PROFILE} (destino de las recomendaciones)", evidence=[PROFILE_TEST]),
    _f("pricing.catalog.items[].name", "Nombre del producto", "A", "offer.catalog.items[{i}].name", panel="pantalla",
       engine="sí: prompt (precio de cada producto)", evidence=[CATALOG_PRICES_TEST]),
    _f("pricing.catalog.items[].category", "Categoría del producto", "A", "offer.catalog.items[{i}].category",
       engine="sí: decide qué categorías se ofrecen", panel="pantalla", evidence=["test_product_category_decides_which_categories_are_offered"]),
    _f("pricing.catalog.items[].description", "Descripción del producto", "A", "offer.catalog.items[{i}].description",
       engine=f"{IN_PROFILE} (detalle de la oferta)", panel="pantalla", evidence=[PROFILE_TEST]),
    _f("pricing.catalog.items[].price.<moneda>", "Precio del producto por moneda", "A", "offer.catalog.items[{i}].prices[currency=<moneda>].amount",
       transform="mapa por moneda → lista con `currency` y `amount`", panel="pantalla",
       engine="sí: prompt (precio de cada producto)", evidence=[CATALOG_PRICES_TEST]),
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
       engine="sí: prompt (argumento de valor, si no hay `break_even_sales`)", panel="pantalla", evidence=[ENGINE_TEST],
       note="Solo agencia_viajes, que vende con cita: el argumento de valor solo va en negocios de planes."),
    _f("pricing.roi_hints", "Argumentos de retorno de la inversión", "B", "terms.roi_hints", transform="cambia de sección",
       engine="sí: prompt (si no hay break_even_sales)", evidence=[ENGINE_TEST]),
    _f("pricing.note", "Aclaración sobre cómo se confirma el precio", "A", "terms.price_note", transform="renombrado",
       engine="sí: prompt (aclaración del precio)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.business_offers.core", "Ofertas principales", "B", "sales.offer_mix.core", transform="cambia de sección",
       engine="sí: prompt (lo principal que vende)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.business_offers.upsell", "Mejoras para vender más", "B", "sales.offer_mix.upsell", transform="cambia de sección",
       engine="sí: prompt (mejoras, solo si están en la oferta)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.business_offers.cross_sell", "Complementos para vender junto", "B", "sales.offer_mix.cross_sell",
       transform="cambia de sección", engine="sí: prompt (complementos, solo si están en la oferta)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("pricing.business_offers.financing.**", "Financiación", "A", "terms.financing.**", transform="cambia de sección",
       engine="sí: prompt (financiación)", panel="pantalla", evidence=[ENGINE_TEST]),
    # ------------------------------------------------------------------ inventory.yaml
    _f("inventory.items", "Inventario (vacío)", "A", "inventory.items", engine="sí: prompt (opciones y existencias de cada producto)",
       panel="pantalla", evidence=[ENGINE_TEST]),
    _f("inventory.items[].**", "Producto con variantes y existencias", "A", "inventory.items[{i}].**",
       engine="sí: prompt (opciones y existencias de cada producto)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("inventory.items[].variants[].sku", "Código interno de la variante", "A", "inventory.items[{i}].variants[{j}].sku",
       engine="no: solo para el equipo; no va a la IA", panel="pantalla",
       evidence=["test_what_only_the_team_sees_or_the_platform_sends_later_never_reaches_the_ai"]),
    _f("inventory.track_stock", "Controlar existencias", "A", "inventory.track_stock", engine="sí: prompt (variantes agotadas)",
       panel="pantalla", evidence=[ENGINE_TEST]),
    # ------------------------------------------------------------------ config.yaml
    _f("config.capabilities.actions.primary", "Acciones de venta", "A", "capabilities.actions_primary", transform="se aplana `actions`",
       engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.capabilities.actions.support", "Acciones de apoyo", "A", "capabilities.actions_support", transform="se aplana `actions`",
       engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.capabilities.business_channels.allowed", "Canales de atención", "A", "capabilities.service_channels", transform="renombrado",
       engine="sí: prompt", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.capabilities.system_channels.allowed", "Canales por los que funciona el producto", "A", "capabilities.product_channels",
       transform="renombrado", engine="sí: prompt", evidence=[ENGINE_TEST]),
    _f("config.capabilities.channels", "Canales (lista antigua)", "E", LEGACY_DESTINATION,
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
    _f("config.capabilities.constraints.**", "Canales y acciones que el negocio no ofrece", "A", "capabilities.restrictions.**",
       transform="renombrado", engine="sí: prompt (canales y acciones que el negocio no ofrece)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.conversation.**", "Ventanas de la conversación", "C", "engine_settings.conversation.**", transform="ajuste técnico, fuera del documento comercial",
       engine="sí: estado y reinicio de la conversación", evidence=["test_conversation_windows_drive_the_conversation_state"],
       note="Parámetro interno: cuándo el motor considera activa o nueva una conversación."),
    _f("config.features.pricing_enabled", "Permite usar precios en la conversación", "B", "features.pricing_enabled",
       transform="sección `features`", engine="sí: prompt (si da precios)", panel="pantalla", evidence=[ENGINE_TEST]),
    _f("config.features.catalog_mode", "Vende opciones tipo catálogo o un servicio o plan", "B", "features.catalog_mode", transform="sección `features`",
       engine="sí: prompt (cuándo mostrar precios)", evidence=[ENGINE_TEST]),
    _f("config.features.business_model", "Tipo de negocio", "B", "features.business_model", transform="sección `features`",
       engine="sí: prompt (cuándo mostrar precios)", evidence=[ENGINE_TEST]),
    _f("config.features.multi_currency", "Permite manejar más de una moneda", "B", "features.multi_currency", transform="sección `features`",
       engine="sí: prompt (todas las monedas o solo la primera)", panel="pantalla", evidence=[ENGINE_TEST],
       note="En agencia_viajes es true con una sola moneda: permitirlo no obliga a usarlo."),
    _f("config.features.multi_plan", "Permite ofrecer varios planes", "B", "features.multi_plan", transform="sección `features`",
       engine="sí: prompt (recomendar un solo plan)", panel="pantalla", evidence=[ENGINE_TEST],
       note="En asesor_ai_prod, clinic y saas es true con un solo plan: permitirlo no obliga a usarlo."),
    _f("config.flags.**", "Banderas internas (ai_first, allow_fallback, log_level)", "C", "engine_settings.flags.**", transform="ajuste técnico, fuera del documento comercial",
       note="Sin consumidor en el motor; no son decisiones del negocio."),
    _f("config.initial_message.enabled", "Mensaje de bienvenida activo", "A", "messages.welcome.enabled", engine="sí: primer mensaje", panel="pantalla",
       evidence=["test_welcome_message_toggle"]),
    _f("config.initial_message.text", "Texto de bienvenida", "A", "messages.welcome.text", engine="sí: primer mensaje", panel="pantalla",
       evidence=["test_welcome_message_toggle"]),
    _f("config.initial_message.recency.**", "Ventanas del mensaje inicial (antiguas)", "E", LEGACY_DESTINATION,
       note="Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h)."),
    _f("config.post_payment.on_user_report.message", "Respuesta al reportar un pago", "A", "messages.payment_reported", transform="renombrado",
       engine="sí: respuesta exacta", panel="pantalla", evidence=["test_payment_report_message_is_optional"]),
    _f("config.post_payment.on_payment_confirmed.message", "Mensaje de pago confirmado", "A", "messages.payment_confirmed", transform="renombrado",
       engine="no: se guarda; lo enviará la plataforma cuando el equipo confirme el pago", panel="pantalla"),
    _f("config.response.length", "Largo de las respuestas", "A", "response_style.length", engine="sí: prompt y recorte", panel="pantalla",
       evidence=["test_each_response_length_option_controls_prompt_and_truncation"]),
    _f("config.response.max_words", "Límite avanzado de palabras", "B", "response_style.max_words", engine="sí: prompt y recorte", panel="modelo",
       evidence=["test_changing_the_contract_changes_response_length"]),
)


# Campos del contrato sin origen en los YAML: qué son y si el panel los ofrece. Su estado en el motor (`x-engine`) y su audiencia (`x-audience`) salen del esquema.
NEW_CONTRACT_FIELDS: dict[str, tuple[str, str]] = {
    # ruta normalizada: (significado, interfaz)
    "payments[].link_enabled": ("Enlace de pago activo", "pantalla"),
    "payments[].transfer_methods[].label": ("Titular o etiqueta de la cuenta", "pantalla"),
    "payments[].transfer_methods[].enabled": ("Cuenta activa", "pantalla"),
    "identity.opening_hours[].days": ("Días de atención", "pantalla"),
    "identity.opening_hours[].opens": ("Hora de apertura", "pantalla"),
    "identity.opening_hours[].closes": ("Hora de cierre", "pantalla"),
    "offer.plans[].prices[].first_payment": ("Valor del primer pago", "pantalla"),
    "offer.plans[].prices[].price": ("Precio de pago único", "pantalla"),
    "offer.plans[].prices[].annual": ("Cobro anual", "pantalla"),
    "offer.plans[].available": ("Plan disponible", "pantalla"),
    "offer.catalog.items[].features": ("Características del producto", "pantalla"),
    "offer.catalog.items[].available": ("Producto disponible", "pantalla"),
    "terms.promotions[].name": ("Nombre de la promoción", "pantalla"),
    "terms.promotions[].details": ("Detalle de la promoción", "pantalla"),
    "terms.promotions[].valid_until": ("Vigencia de la promoción", "pantalla"),
    "terms.policies.warranty": ("Política de garantía", "pantalla"),
    "terms.policies.returns": ("Política de cambios y devoluciones", "pantalla"),
    "terms.policies.cancellation": ("Política de cancelación y reembolso", "pantalla"),
    "sales.instructions": ("Instrucciones de venta", "pantalla"),
    "messages.after_sale": ("Mensaje después de la compra", "pantalla"),
    "messages.data_request": ("Mensaje para pedir datos", "pantalla"),
    "messages.follow_up": ("Mensaje de seguimiento", "pantalla"),
    "messages.human_handoff": ("Mensaje al pasar a una persona", "pantalla"),
    "messages.fallback": ("Mensaje si el asistente no puede responder", "pantalla"),
    "response_style.formality": ("Nivel de formalidad", "pantalla"),
    "response_style.emojis": ("Uso de emojis", "pantalla"),
    "response_style.instructions": ("Indicaciones de comunicación", "pantalla"),
    "knowledge.faqs[].question": ("Pregunta frecuente", "pantalla"),
    "knowledge.faqs[].answer": ("Respuesta oficial", "pantalla"),
    "inventory.items[].variants[].prices[].currency": ("Moneda del precio de la variante", "pantalla"),
    "inventory.items[].variants[].prices[].amount": ("Precio de la variante", "pantalla"),
}

# Campos del contrato que llegan desde una ruta antigua con forma derivada (se cubren aunque su
# ruta no aparezca literalmente en un destino del catálogo).
DERIVED_CONTRACT_FIELDS: dict[str, str] = {
    "schema_version": "Versión del contrato",
    "tenant_slug": "Negocio dueño del documento",
    "sales.customer_problems[].id": "Clave del problema en `sales.pain.clusters`",
    "sales.motivations[].motivation": "Clave del motivo en `business.value_drivers` y `sales.angles`",
    "sales.objections[].topic": "Clave de la objeción en `sales.objection`",
    "offer.plans[].prices[].currency": "Clave de moneda en `pricing.plans[].pricing`",
    "offer.catalog.items[].prices[].currency": "Clave de moneda en `pricing.catalog.items[].price`",
    "payments[].id": "Perfil de pago creado por la importación (id del plan o `catalog`)",
    "offer.plans[].payment_profile": "Enlace del plan con su perfil de pago",
    "offer.catalog.payment_profile": "Enlace del catálogo con su perfil de pago",
}


# Funcionalidades comerciales de los YAML: qué hace cada una, según sus comentarios y lo que comprobamos
# en el motor. Conservan sus opciones y valores; la tabla se publica en la matriz de trazabilidad.
@dataclass(frozen=True)
class CommercialControl:
    group: str
    pattern: str
    behavior: str
    show_values: bool = True


COMMERCIAL_CONTROLS: tuple[CommercialControl, ...] = (
    CommercialControl("Saludo", "config.initial_message.enabled",
                      "Dos modalidades. `true`: ante un saludo sin más en una conversación nueva, el sistema envía el texto fijo, sin IA. "
                      "`false`: no lo envía y responde la IA. Un saludo con intención siempre lo responde la IA."),
    CommercialControl("Saludo", "config.initial_message.text", "Mensaje de apertura que recibe el usuario; se conserva aunque esté desactivado.", False),
    CommercialControl("Extensión de los mensajes", "config.response.length", "Tamaño de la respuesta, en el prompt y al recortarla."),
    CommercialControl("Extensión de los mensajes", "config.response.max_words", "Máximo de palabras por respuesta, dentro del rango de `length`."),
    CommercialControl("Interruptores de venta", "config.features.pricing_enabled", "`true`: permite usar precios en la conversación."),
    CommercialControl("Interruptores de venta", "config.features.catalog_mode", "`true`: vende opciones tipo catálogo. `false`: vende un servicio o plan."),
    CommercialControl("Interruptores de venta", "config.features.multi_currency", "`true`: permite manejar más de una moneda."),
    CommercialControl("Interruptores de venta", "config.features.multi_plan", "`true`: permite ofrecer varios planes."),
    CommercialControl("Interruptores de venta", "config.features.business_model", "Tipo de negocio; con él el motor decide cuándo mostrar precios."),
    CommercialControl("Atención", "sales.support.info_handling.explain_first", "`true`: primero aclara la duda. `false`: vende directo."),
    CommercialControl("Atención", "sales.support.info_handling.sell_after", "`true`: después de explicar, vuelve a llevar al cliente a avanzar."),
    CommercialControl("Atención", "sales.qualification.detect_offer_fit", "`true`: valida si la oferta encaja antes de empujar el cierre."),
    CommercialControl("Flujo de conversación", "sales.conversation_flow.steps", "Pasos que idealmente sigue la conversación."),
    CommercialControl("Flujo de conversación", "sales.conversation_flow.rules.no_skip_steps", "`true`: no se saltan pasos."),
    CommercialControl("Flujo de conversación", "sales.conversation_flow.rules.guided_process", "`true`: guía al cliente paso a paso en un proceso."),
    CommercialControl("Flujo de conversación", "sales.progression_rules.required_flow", "Secuencia mínima que debe respetar la conversación."),
    CommercialControl("Flujo de conversación", "sales.progression_rules.forbid", "Lo que el asistente no debe hacer en este negocio."),
    CommercialControl("Cierre", "sales.closing.strategy", "Tipo de cierre."),
    CommercialControl("Cierre", "config.capabilities.closing_methods.link_payment.enabled", "`true`: permite enviar un enlace de pago directo al cliente."),
    CommercialControl("Cierre", "config.capabilities.closing_methods.human_handoff.enabled", "`true`: permite escalar la conversación a una persona."),
    CommercialControl("Cierre", "config.capabilities.closing_methods.data_collection.enabled", "`true`: permite cerrar pidiendo los datos del cliente."),
    CommercialControl("Cierre", "config.capabilities.data_collection.enabled", "`true`: el asistente puede pedir datos al cliente."),
    CommercialControl("Cierre", "config.capabilities.data_collection.fields", "Datos que el asistente pide."),
    CommercialControl("Precio", "pricing.price_framing.type", "Forma de presentar el precio."),
    CommercialControl("Precio", "pricing.business_offers.financing.available", "`true`: permite financiación. `false`: no la ofrece."),
    CommercialControl("Recomendaciones", "sales.offer.recommendation_rules[].condition", "Situación que activa una recomendación.", False),
    CommercialControl("Recomendaciones", "sales.offer.recommendation_rules[].recommend", "Plan que se recomienda en esa situación.", False),
    CommercialControl("Entrega", "business.logistics.delivery.available", "`true`: ofrece domicilio."),
    CommercialControl("Entrega", "business.logistics.shipping.available", "`true`: ofrece envío."),
    CommercialControl("Entrega", "business.logistics.pickup.available", "`true`: ofrece recogida."),
    CommercialControl("Entrega", "business.logistics.scheduling.required", "`true`: el servicio requiere agendar."),
    CommercialControl("Inventario", "inventory.track_stock", "`true`: el negocio controla existencias."),
)


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
    if entry.destination in (LEGACY_DESTINATION, POLICY_DESTINATION):
        concrete = ".".join(f"[{part}]" if part.isdigit() else part for part in leaf.path.split("."))
        return f"{LEGACY_DESTINATION}.{concrete}".replace(".[", "[")
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
    if entry.kind == "policy":
        if found is not None or resolve_path(document, leaf.path) is not None:
            return f"{leaf.path}: la definición común no debe estar en los documentos"
        if resolve_path(COMMON_CLOSING_POLICY, leaf.path.removeprefix("sales.closing.")) != leaf.value:
            return f"{leaf.path}: no coincide con la política global del cierre"
        return None
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
    value_type: str = ""


def _value_type(target: dict, definitions: dict) -> str:
    """Tipo y opciones de un campo hoja, en palabras, para la documentación."""
    if "enum" in target:
        return " \\| ".join(str(value) for value in target["enum"])
    if "const" in target:
        return str(target["const"])
    numeric = [option for option in target.get("anyOf", []) if option.get("type") in ("integer", "number")]
    if numeric and len(numeric) == len(target["anyOf"]):
        minimum = f" (mínimo {numeric[0]['minimum']})" if "minimum" in numeric[0] else ""
        return f"número{minimum}"
    if target.get("format") == "date":
        return "fecha"
    if target.get("type") == "string" and "pattern" in target:
        return "texto con formato validado"
    if target.get("type") == "array":
        items = target.get("items", {})
        while "$ref" in items:
            items = definitions[items["$ref"].rsplit("/", 1)[-1]]
        return f"lista de {_value_type(items, definitions)}"
    if target.get("properties", {}).keys() == {"secret_ref"}:
        return "referencia a secreto"
    minimum = f" (mínimo {target['minimum']})" if "minimum" in target else ""
    labels = {"boolean": "interruptor true/false", "integer": "entero", "number": "número", "string": "texto", "object": "mapa"}
    return labels.get(target.get("type", ""), "texto o número") + minimum


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
            fields[path] = ContractField(path, audience, engine, " ".join(description.split()), _value_type(target, definitions))

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
