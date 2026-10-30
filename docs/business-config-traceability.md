# Matriz de trazabilidad: YAML antiguos → BusinessConfig v1

Versión del contrato: `1.0`. Negocios: 9. Patrones catalogados: 131.

> Archivo generado por `scripts/generate_traceability_matrix.py` desde
> `project/app/infrastructure/config/legacy_field_catalog.py`. No editar a mano: `--check` falla si
> está desactualizado y `tests/test_business_config_traceability.py` lo comprueba.

Cada fila es un campo de los YAML de origen (`business.yaml`, `sales.yaml`, `pricing.yaml`,
`inventory.yaml`, `config.yaml`). No se muestran valores, solo rutas.

- **Conservado en los datos:** todos los campos, en todos los negocios. Lo comprueba
  `test_business_config_traceability.py::test_every_legacy_field_reaches_its_declared_destination`: el valor original está en el destino declarado.
- **Representado en el contrato:** la columna Destino. `compatibility` significa que el dato se
  conserva con su ruta original pero no forma parte del contrato (ver Justificación).
- **Interfaz:** `pantalla` (el panel tiene un control), `modelo` (el modelo y el adaptador del panel
  lo admiten, pero aún no hay pantalla) o `no`.
- **Motor:** `sí` solo con evidencia (columna Prueba) de que el motor actual lo usa; `no` si solo está
  representado. Las pruebas de uso están en `tests/test_business_config_engine_integration.py`.
- `[]` es un índice de lista; `<nombre>` una clave variable (id de problema, moneda...).

Clases: **A** configuración que edita el cliente; **B** configuración comercial avanzada; **C** configuración interna del motor; **D** información sensible (datos de pago); **E** derivada, obsoleta o redundante.

## Resumen por negocio

| Negocio | Campos | Tipados | Datos de pago (referencias) | En compatibilidad | A | B | C | D | E |
|---|---|---|---|---|---|---|---|---|---|
| agencia_viajes | 145 | 126 | 5 | 14 | 91 | 30 | 9 | 5 | 10 |
| asesor_ai_prod | 164 | 140 | 5 | 19 | 82 | 57 | 10 | 5 | 10 |
| clinic | 109 | 90 | 5 | 14 | 71 | 14 | 9 | 5 | 10 |
| demo | 162 | 131 | 10 | 21 | 92 | 41 | 7 | 10 | 12 |
| ecommerce | 109 | 90 | 5 | 14 | 71 | 14 | 9 | 5 | 10 |
| escuela_conduccion | 144 | 125 | 5 | 14 | 102 | 18 | 9 | 5 | 10 |
| restaurant | 128 | 108 | 5 | 15 | 89 | 14 | 9 | 5 | 11 |
| saas | 112 | 93 | 5 | 14 | 71 | 17 | 9 | 5 | 10 |
| tienda_ropa | 138 | 119 | 5 | 14 | 100 | 14 | 9 | 5 | 10 |
| **Total** | 1211 | 1022 | 50 | 139 | 769 | 219 | 80 | 50 | 93 |

## business.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `business.brand_name` | todos | Marca | E | `compatibility` (misma ruta) | — | no | no | Igual a `name` en los 9 negocios. El contrato ofrece `identity.brand_name` para marcas distintas del nombre. | — |
| `business.buying_motivation.primary` | agencia_viajes, asesor_ai_prod | Motivo principal de compra | A | `sales.buying_motivation.primary` | cambia de sección | pantalla | sí: prompt (motores de compra) | — | `test_connected_fields_change_the_prompt` |
| `business.buying_motivation.secondary` | agencia_viajes, asesor_ai_prod | Motivo secundario de compra | A | `sales.buying_motivation.secondary` | cambia de sección | pantalla | sí: prompt (motores de compra) | — | `test_connected_fields_change_the_prompt` |
| `business.city` | todos | Ciudad | E | `compatibility` (misma ruta) | — | no | no | Duplica `business.location.city` (mismo valor en los 9 negocios). | — |
| `business.credibility` | agencia_viajes, asesor_ai_prod | Pruebas de confianza | A | `identity.credibility` | — | no | no | — | — |
| `business.customer_profile.company_size` | agencia_viajes, asesor_ai_prod, clinic, demo, ecommerce, restaurant, saas, tienda_ropa | Cliente ideal | A | `identity.target_customer.company_size` | renombrado | no | no | — | — |
| `business.customer_profile.maturity` | agencia_viajes, asesor_ai_prod | Cliente ideal | A | `identity.target_customer.maturity` | renombrado | no | no | — | — |
| `business.customer_profile.roles` | agencia_viajes, asesor_ai_prod | Cliente ideal | A | `identity.target_customer.roles` | renombrado | no | no | — | — |
| `business.customer_profile.segment` | agencia_viajes, asesor_ai_prod, clinic, demo, ecommerce, restaurant, saas, tienda_ropa | Cliente ideal | A | `identity.target_customer.segment` | renombrado | no | no | — | — |
| `business.description` | todos | Descripción del negocio | A | `identity.description` | — | pantalla | no: el prompt solo la usa si falta `industry`, que el contrato exige | — | — |
| `business.desired_outcomes` | todos | Resultados que busca el cliente | A | `sales.benefits` | renombrado y cambia de sección | modelo | no: el prompt actual no lo usa | — | — |
| `business.differentiators` | agencia_viajes, asesor_ai_prod, clinic, demo, ecommerce, restaurant, saas, tienda_ropa | Diferenciadores | A | `identity.differentiators` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.industry` | todos | Sector o tipo de negocio | A | `identity.industry` | — | pantalla | sí: prompt (sector) | — | `test_connected_fields_change_the_prompt` |
| `business.location.address` | todos | Ubicación y cobertura | A | `identity.location.address` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.location.city` | todos | Ubicación y cobertura | A | `identity.location.city` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.location.coverage.type` | todos | Ubicación y cobertura | A | `identity.location.coverage.type` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.location.coverage.zones` | todos | Ubicación y cobertura | A | `identity.location.coverage.zones` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.location.type` | todos | Ubicación y cobertura | A | `identity.location.type` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.logistics.delivery.available` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.available` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.delivery.cost.type` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.cost.type` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.delivery.cost.value` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.cost.value` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.delivery.time.max` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.time.max` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.delivery.time.min` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.time.min` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.delivery.type` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.type` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.delivery.zones` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.delivery.zones` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.pickup.available` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.pickup.available` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.pickup.instructions` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.pickup.instructions` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.scheduling.required` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.scheduling.required` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.available` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.available` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.cost.type` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.cost.type` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.cost.value` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.cost.value` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.providers` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.providers` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.scope` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.scope` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.time.max` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.time.max` | sección propia `fulfillment` | no | no | — | — |
| `business.logistics.shipping.time.min` | todos | Domicilio, envío, recogida y agenda | A | `fulfillment.shipping.time.min` | sección propia `fulfillment` | no | no | — | — |
| `business.name` | todos | Nombre comercial | A | `identity.name` | — | pantalla | no: el prompt actual no lo usa | — | — |
| `business.pain_points` | todos | Problemas del cliente en sus palabras | A | `sales.pain_points` | cambia de sección | no | no | — | — |
| `business.positioning` | todos | A quién se dirige y qué problema resuelve | A | `identity.positioning` | — | no | no | — | — |
| `business.promise` | todos | Propuesta de valor | A | `identity.value_proposition` | renombrado | pantalla | sí: prompt (promesa comercial) | — | `test_connected_fields_change_the_prompt` |
| `business.service_modes` | todos | Modalidades de atención | A | `identity.service_modes` | — | modelo | no: el prompt actual no lo usa | — | — |
| `business.tone` | todos | Tono de comunicación | A | `response_style.tone` | cambia de sección | modelo | no: el prompt actual no lo usa | — | — |
| `business.type` | restaurant | Tipo de negocio | E | `compatibility` (misma ruta) | — | no | no | Solo restaurant; repite el sector (`industry`) y el modelo de negocio del motor. | — |
| `business.use_cases[].enfoque` | agencia_viajes, asesor_ai_prod | Enfoque de la solución para el caso | B | `sales.use_cases[].approach` | `enfoque` → `approach` | no | no | — | — |
| `business.use_cases[].nombre` | agencia_viajes, asesor_ai_prod | Caso de uso típico | B | `sales.use_cases[].name` | `nombre` → `name` | no | sí: respaldo de 'Casos típicos' si no hay impactos | — | `test_connected_fields_change_the_prompt` |
| `business.use_cases[].senales` | agencia_viajes, asesor_ai_prod | Señales del caso de uso | B | `sales.use_cases[].signals` | `senales` → `signals` | no | no | — | — |
| `business.value_drivers.<motivo>.description` | agencia_viajes, asesor_ai_prod | Qué significa cada motivo de compra | B | `sales.motivation_drivers[motivation=<motivo>].description` | mapa por motivo → lista con `motivation` | no | no | — | — |
| `business.value_drivers.<motivo>.triggers` | agencia_viajes, asesor_ai_prod | Frases que revelan cada motivo | B | `sales.motivation_drivers[motivation=<motivo>].signals` | mapa por motivo → lista; `triggers` → `signals` | no | no | — | — |
| `business.voice` | todos | Personalidad o voz de la marca | A | `response_style.voice` | cambia de sección | no | no | — | — |

## sales.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `sales.angles.<motivo>.execution` | asesor_ai_prod, demo | Qué decir con el ángulo de venta | B | `sales.angles[motivation=<motivo>].messages` | mapa por motivo → lista; `execution` → `messages` | no | no | — | — |
| `sales.angles.<motivo>.when` | asesor_ai_prod, demo | Cuándo usar el ángulo de venta | B | `sales.angles[motivation=<motivo>].signals` | mapa por motivo → lista; `when` → `signals` | no | no | — | — |
| `sales.closing.actions.high_intent` | asesor_ai_prod, demo | Acciones ante intención alta | B | `sales.closing.high_intent_actions` | se aplana `actions` | no | no | — | — |
| `sales.closing.behavior.<estrategia>.goal` | todos | Objetivo de cada estrategia de cierre | E | `compatibility` (misma ruta) | — | no | no | Plantilla idéntica en los 9 negocios (estrategia → objetivo): es una política del motor, no un dato del negocio. | — |
| `sales.closing.hard_rules` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Reglas de cierre | B | `sales.closing.rules` | `hard_rules` → `rules` | no | no | En asesor_ai_prod tres reglas validan el texto de la respuesta (p. ej. que no contenga '?'); el motor no las aplica. Moverlas a las políticas del motor cambia las reglas del negocio: decisión pendiente. | — |
| `sales.closing.micro_commitments` | asesor_ai_prod, demo | Compromisos progresivos | B | `sales.closing.micro_commitments` | — | no | no | — | — |
| `sales.closing.next_step.action` | todos | Modo del siguiente paso | C | `compatibility` (misma ruta) | — | no | no | Vale `dynamic` en los 9 negocios; parámetro interno. | — |
| `sales.closing.next_steps` | todos | Siguientes pasos | B | `sales.closing.next_steps` | — | no | no | — | — |
| `sales.closing.required_data` | todos | Datos que necesita el cierre | B | `sales.closing.required_data` | — | no | no | Se solapa con `capabilities.data_collection.fields`, que es lo que el motor pide hoy. | — |
| `sales.closing.strategy` | todos | Estrategia de cierre | B | `sales.closing.strategy` | — | no | no | — | — |
| `sales.closing.triggers` | todos | Señales de intención de compra | B | `sales.closing.purchase_signals` | renombrado | no | no | — | — |
| `sales.conversation_flow.rules.guided_process` | escuela_conduccion | Guiar un proceso paso a paso | B | `sales.conversation_flow.guided_process` | se aplana `rules` | no | no | — | — |
| `sales.conversation_flow.rules.no_skip_steps` | asesor_ai_prod, demo, escuela_conduccion | No saltar etapas | B | `sales.conversation_flow.no_skip_steps` | se aplana `rules` | no | no | — | — |
| `sales.conversation_flow.steps` | asesor_ai_prod, demo, escuela_conduccion | Etapas de la conversación | B | `sales.conversation_flow.steps` | — | no | no | — | — |
| `sales.discovery.objectives` | todos | Qué debe averiguar el asistente | B | `sales.discovery.objectives` | — | no | no | — | — |
| `sales.discovery.questions` | asesor_ai_prod, demo | Preguntas de diagnóstico | A | `sales.discovery.questions` | — | modelo | no: el prompt actual no lo usa | — | — |
| `sales.objection.<objecion>.hard_rules` | asesor_ai_prod | Reglas al responder la objeción | B | `sales.objections[topic=<objecion>].rules` | `hard_rules` → `rules` | no | no | — | — |
| `sales.objection.<objecion>.layers.acknowledge` | agencia_viajes, asesor_ai_prod, demo, saas | Manejo de la objeción por capas | B | `sales.objections[topic=<objecion>].acknowledge` | mapa por objeción → lista con `topic`; se aplana `layers` | no | no | — | — |
| `sales.objection.<objecion>.layers.proof` | asesor_ai_prod, demo | Manejo de la objeción por capas | B | `sales.objections[topic=<objecion>].proof` | mapa por objeción → lista con `topic`; se aplana `layers` | no | no | — | — |
| `sales.objection.<objecion>.layers.redirect` | agencia_viajes, asesor_ai_prod, demo, saas | Manejo de la objeción por capas | B | `sales.objections[topic=<objecion>].redirect` | mapa por objeción → lista con `topic`; se aplana `layers` | no | no | — | — |
| `sales.objection.<objecion>.layers.reframe` | agencia_viajes, asesor_ai_prod, demo, saas | Manejo de la objeción por capas | B | `sales.objections[topic=<objecion>].reframe` | mapa por objeción → lista con `topic`; se aplana `layers` | no | no | — | — |
| `sales.offer.recommendation_rules[].condition` | asesor_ai_prod, demo | Situación que activa una recomendación | B | `compatibility` (misma ruta) | — | no | no | Apunta a planes que no existen en el negocio (plan_pro, plan_basico). El contrato exige que `sales.recommendation_rules` apunte a la oferta real: requiere decisión del negocio. | — |
| `sales.offer.recommendation_rules[].recommend` | asesor_ai_prod, demo | Plan recomendado | B | `compatibility` (misma ruta) | — | no | no | Ver `condition`: referencia a un plan inexistente. | — |
| `sales.offer.strategy.multi` | asesor_ai_prod, demo | Cómo presentar varias opciones | B | `sales.offer_presentation.multiple_offers` | renombrado | no | no | — | — |
| `sales.offer.strategy.single` | asesor_ai_prod, demo | Cómo presentar una sola opción | B | `sales.offer_presentation.single_offer` | renombrado | no | no | — | — |
| `sales.pain.clusters.<problema>.impacts` | agencia_viajes, asesor_ai_prod, demo, escuela_conduccion | Impactos del problema | A | `sales.customer_problems[id=<problema>].impacts` | mapa por problema → lista con `id` | pantalla | sí: prompt (casos típicos) | — | `test_connected_fields_change_the_prompt` |
| `sales.pain.clusters.<problema>.monetization` | agencia_viajes, asesor_ai_prod, demo, escuela_conduccion | Cuánto le cuesta el problema al cliente | B | `sales.customer_problems[id=<problema>].monetization` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.recommended_angles` | asesor_ai_prod, demo | Ángulos de venta para el problema | B | `sales.customer_problems[id=<problema>].recommended_angles` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.signals` | agencia_viajes, asesor_ai_prod, demo, escuela_conduccion | Frases que revelan el problema | B | `sales.customer_problems[id=<problema>].signals` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.urgency_levels.alto` | asesor_ai_prod, demo | Mensajes según la urgencia | B | `sales.customer_problems[id=<problema>].urgency_levels.alto` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.urgency_levels.medio` | asesor_ai_prod, demo | Mensajes según la urgencia | B | `sales.customer_problems[id=<problema>].urgency_levels.medio` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.progression_rules.forbid` | asesor_ai_prod, demo | Respuestas prohibidas por el flujo | C | `compatibility` (misma ruta) | — | no | no | Códigos internos del motor (asesor_ai_prod, demo). | — |
| `sales.progression_rules.required_flow` | todos | Flujo comercial obligatorio | E | `compatibility` (misma ruta) | — | no | no | Idéntico en los 9 negocios y ya fijado en el prompt del motor (dolor → impacto → solución → acción). | — |
| `sales.qualification.detect_offer_fit` | asesor_ai_prod, demo | Comprobar que la oferta encaja con el cliente | B | `sales.qualification.detect_offer_fit` | — | no | no | — | — |
| `sales.solution.framing` | asesor_ai_prod, demo, escuela_conduccion | Argumentos de venta | A | `sales.arguments` | renombrado | modelo | no: el prompt actual no lo usa | — | — |
| `sales.solution.mapping.<problema>` | asesor_ai_prod, demo | Qué parte de la solución atiende cada problema | B | `sales.solution.mapping[problem=<problema>].solutions` | mapa por problema → lista con `problem` | no | no | — | — |
| `sales.solution.process_steps` | escuela_conduccion | Pasos del proceso de compra o servicio | A | `sales.solution.process_steps` | — | no | no | — | — |
| `sales.solution.requirements` | escuela_conduccion | Requisitos del cliente | A | `sales.solution.requirements` | — | no | no | — | — |
| `sales.support.hard_rules` | asesor_ai_prod | Reglas de atención | B | `sales.support.rules` | `hard_rules` → `rules` | no | no | — | — |
| `sales.support.info_handling.explain_first` | todos | Explicar antes de vender | B | `sales.support.explain_first` | se aplana `info_handling` | no | no | — | — |
| `sales.support.info_handling.sell_after` | todos | Vender después de explicar | B | `sales.support.sell_after` | se aplana `info_handling` | no | no | — | — |

## pricing.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `pricing.business_offers.core` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Ofertas principales | B | `sales.offer_mix.core` | cambia de sección | no | no | — | — |
| `pricing.business_offers.cross_sell` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Complementos para vender junto | B | `sales.offer_mix.cross_sell` | cambia de sección | no | no | — | — |
| `pricing.business_offers.financing.available` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Financiación | A | `terms.financing.available` | cambia de sección | no | no | — | — |
| `pricing.business_offers.financing.options` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Financiación | A | `terms.financing.options` | cambia de sección | no | no | — | — |
| `pricing.business_offers.financing.providers` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Financiación | A | `terms.financing.providers` | cambia de sección | no | no | — | — |
| `pricing.business_offers.upsell` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Mejoras para vender más | B | `sales.offer_mix.upsell` | cambia de sección | no | no | — | — |
| `pricing.catalog.categories[].id` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Identificador de la categoría | A | `offer.catalog.categories[].id` | — | pantalla | sí: categorías con productos disponibles | — | `test_unavailable_offer_is_not_offered` |
| `pricing.catalog.categories[].name` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Nombre de la categoría | A | `offer.catalog.categories[].name` | — | pantalla | sí: prompt (primeras 4 categorías) | — | `test_connected_fields_change_the_prompt` |
| `pricing.catalog.items[].category` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Categoría del producto | A | `offer.catalog.items[].category` | — | pantalla | sí: decide qué categorías se ofrecen | — | `test_product_category_decides_which_categories_are_offered` |
| `pricing.catalog.items[].description` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Descripción del producto | A | `offer.catalog.items[].description` | — | pantalla | no: el prompt actual no lo usa | — | — |
| `pricing.catalog.items[].id` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Identificador estable del producto | A | `offer.catalog.items[].id` | — | pantalla | no | — | — |
| `pricing.catalog.items[].name` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Nombre del producto | A | `offer.catalog.items[].name` | — | pantalla | no: el prompt de catálogo no lista productos (dice 'valores definidos en pricing') | — | — |
| `pricing.catalog.items[].price.<moneda>` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Precio del producto por moneda | A | `offer.catalog.items[].prices[currency=<moneda>].amount` | mapa por moneda → lista con `currency` y `amount` | pantalla | no: el prompt de catálogo no lista precios (dice 'valores definidos en pricing') | — | — |
| `pricing.catalog.payment.link` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Link de pago del catálogo | D | referencia en `payments[id=catalog].link` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.enabled` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Transferencias activas | A | `payments[id=catalog].transfer_enabled` | perfil de pago `catalog` | pantalla | sí: métodos disponibles | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.methods[].account_number` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Número de cuenta | D | referencia en `payments[id=catalog].transfer_methods[].account_number` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.methods[].account_type` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Tipo de cuenta | A | `payments[id=catalog].transfer_methods[].account_type` | — | pantalla | sí: mensaje de pago | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.methods[].bank` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Banco | A | `payments[id=catalog].transfer_methods[].bank` | — | pantalla | sí: mensaje de pago | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.methods[].number` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Celular Nequi o Daviplata | D | referencia en `payments[id=catalog].transfer_methods[].number` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.methods[].reference` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Llave o referencia Bre-B | D | referencia en `payments[id=catalog].transfer_methods[].reference` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.catalog.payment.transfer.methods[].type` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Método de transferencia | A | `payments[id=catalog].transfer_methods[].type` | — | pantalla | sí: métodos disponibles | — | `test_payment_methods_reach_the_customer` |
| `pricing.conditions` | todos | Condiciones comerciales | A | `terms.conditions` | cambia de sección | pantalla | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `pricing.model` | agencia_viajes, escuela_conduccion, restaurant, tienda_ropa | Venta por catálogo | A | `offer.model` | — | pantalla | sí: prompt (planes o categorías del catálogo) | — | `test_tenants_stay_isolated_with_contract_source` |
| `pricing.note` | agencia_viajes | Aclaración sobre cómo se confirma el precio | A | `terms.price_note` | renombrado | no | no | — | — |
| `pricing.plans[].description` | asesor_ai_prod, clinic, demo, ecommerce, saas | Descripción del plan | A | `offer.plans[].description` | — | pantalla | no: el prompt actual no lo usa | — | — |
| `pricing.plans[].id` | asesor_ai_prod, clinic, demo, ecommerce, saas | Identificador estable del plan | A | `offer.plans[].id` | — | pantalla | sí: enlaza el plan con su pago | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].includes` | asesor_ai_prod, clinic, demo, ecommerce, saas | Qué incluye | A | `offer.plans[].includes` | — | pantalla | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `pricing.plans[].name` | asesor_ai_prod, clinic, demo, ecommerce, saas | Nombre del plan | A | `offer.plans[].name` | — | pantalla | sí: prompt (qué se cobra y precios) | — | `test_plan_prices_format_is_unchanged` |
| `pricing.plans[].not_included` | asesor_ai_prod, clinic, demo, ecommerce, saas | Qué no incluye | A | `offer.plans[].not_included` | — | pantalla | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `pricing.plans[].payment.link` | asesor_ai_prod, clinic, demo, ecommerce, saas | Link de pago | D | referencia en `payments[].link` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.enabled` | asesor_ai_prod, clinic, demo, ecommerce, saas | Transferencias activas | A | `payments[].transfer_enabled` | perfil de pago con el id del plan | pantalla | sí: métodos disponibles | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.methods[].account_number` | asesor_ai_prod, clinic, demo, ecommerce, saas | Número de cuenta | D | referencia en `payments[].transfer_methods[].account_number` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.methods[].account_type` | asesor_ai_prod, clinic, demo, ecommerce, saas | Tipo de cuenta | A | `payments[].transfer_methods[].account_type` | — | pantalla | sí: mensaje de pago | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.methods[].bank` | asesor_ai_prod, clinic, demo, ecommerce, saas | Banco | A | `payments[].transfer_methods[].bank` | — | pantalla | sí: mensaje de pago | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.methods[].number` | asesor_ai_prod, clinic, demo, ecommerce, saas | Celular Nequi o Daviplata | D | referencia en `payments[].transfer_methods[].number` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.methods[].reference` | asesor_ai_prod, clinic, demo, ecommerce, saas | Llave o referencia Bre-B | D | referencia en `payments[].transfer_methods[].reference` | valor → referencia `legacy_yaml:` | pantalla | sí: el motor lo entrega al elegir el método | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].payment.transfer.methods[].type` | asesor_ai_prod, clinic, demo, ecommerce, saas | Método de transferencia | A | `payments[].transfer_methods[].type` | — | pantalla | sí: métodos disponibles | — | `test_payment_methods_reach_the_customer` |
| `pricing.plans[].pricing.<moneda>.implementation` | asesor_ai_prod, clinic, demo, ecommerce, saas | Precio del plan por moneda (instalación, mensual...) | A | `offer.plans[].prices[currency=<moneda>].implementation` | mapa por moneda → lista con `currency` | pantalla | sí: prompt (precios) | — | `test_plan_prices_format_is_unchanged`, `test_connected_fields_change_the_prompt` |
| `pricing.plans[].pricing.<moneda>.monthly` | asesor_ai_prod, clinic, demo, ecommerce, saas | Precio del plan por moneda (instalación, mensual...) | A | `offer.plans[].prices[currency=<moneda>].monthly` | mapa por moneda → lista con `currency` | pantalla | sí: prompt (precios) | — | `test_plan_prices_format_is_unchanged`, `test_connected_fields_change_the_prompt` |
| `pricing.plans[].target` | demo | Para quién es el plan | A | `offer.plans[].target` | — | no | no | — | — |
| `pricing.price_framing.type` | todos | Cómo presentar el precio | B | `terms.price_framing` | se aplana `type` | no | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `pricing.roi.break_even_reservas` | agencia_viajes | Reservas para recuperar la inversión | B | `terms.roi_break_even_bookings` | renombrado | no | no | Solo agencia_viajes; el motor solo lee `break_even_sales`. | — |
| `pricing.roi.break_even_sales` | asesor_ai_prod, clinic, demo, ecommerce, restaurant, saas, tienda_ropa | Ventas para recuperar la inversión | B | `terms.roi_break_even_sales` | se aplana `roi` | no | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `pricing.roi_hints` | agencia_viajes | Argumentos de retorno de la inversión | B | `terms.roi_hints` | cambia de sección | no | sí: prompt (si no hay break_even_sales) | — | `test_connected_fields_change_the_prompt` |

## inventory.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `inventory.items` | agencia_viajes, asesor_ai_prod, clinic, demo, ecommerce, escuela_conduccion, restaurant, saas | Inventario (vacío) | A | `inventory.items` | — | no | no | El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta. | — |
| `inventory.items[].product_id` | tienda_ropa | Producto con variantes y existencias | A | `inventory.items[].product_id` | — | no | no | El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta. | — |
| `inventory.items[].variants[].attributes.color` | tienda_ropa | Producto con variantes y existencias | A | `inventory.items[].variants[].attributes.color` | — | no | no | El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta. | — |
| `inventory.items[].variants[].attributes.size` | tienda_ropa | Producto con variantes y existencias | A | `inventory.items[].variants[].attributes.size` | — | no | no | El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta. | — |
| `inventory.items[].variants[].sku` | tienda_ropa | Producto con variantes y existencias | A | `inventory.items[].variants[].sku` | — | no | no | El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta. | — |
| `inventory.items[].variants[].stock` | tienda_ropa | Producto con variantes y existencias | A | `inventory.items[].variants[].stock` | — | no | no | El motor solo lo usaría para reconocer un catálogo, que ya se reconoce por la oferta. | — |
| `inventory.track_stock` | todos | Controlar existencias | A | `inventory.track_stock` | — | no | no | — | — |

## config.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `config.capabilities.actions.primary` | todos | Acciones de venta | A | `capabilities.actions_primary` | se aplana `actions` | pantalla | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `config.capabilities.actions.support` | todos | Acciones de apoyo | A | `capabilities.actions_support` | se aplana `actions` | pantalla | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `config.capabilities.business_channels.allowed` | todos | Canales de atención | A | `capabilities.service_channels` | renombrado | pantalla | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `config.capabilities.channels` | todos | Canales (lista antigua) | E | `compatibility` (misma ruta) | — | no | no | Estructura antigua: el prompt solo la usa si no hay canales de atención ni del sistema, lo que no ocurre en ningún negocio. En asesor_ai_prod contradice a `business_channels` (vacío). | — |
| `config.capabilities.closing_methods.data_collection.enabled` | todos | Cerrar pidiendo datos | A | `capabilities.closing_methods.data_collection` | — | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.closing_methods.human_handoff.enabled` | todos | Pasar a una persona | A | `capabilities.closing_methods.human_handoff` | — | pantalla | sí: prompt (nadie del equipo recibe aviso) | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.closing_methods.link_payment.enabled` | todos | Cerrar enviando el pago | A | `capabilities.closing_methods.payment_link` | renombrado | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.constraints.disallowed_actions` | todos | Canales y acciones que el negocio no ofrece | A | `capabilities.restrictions.disallowed_actions` | renombrado | no | no | — | — |
| `config.capabilities.constraints.disallowed_channels` | todos | Canales y acciones que el negocio no ofrece | A | `capabilities.restrictions.disallowed_channels` | renombrado | no | no | — | — |
| `config.capabilities.data_collection.enabled` | todos | Pedir datos al cliente | A | `capabilities.data_collection.enabled` | — | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.data_collection.fields` | todos | Datos que se piden | A | `capabilities.data_collection.fields` | — | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.system_channels.allowed` | todos | Canales por los que funciona el producto | A | `capabilities.product_channels` | renombrado | no | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `config.conversation.active_window_minutes` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Ventanas de la conversación | C | `engine.conversation.active_window_minutes` | sección interna `engine` | no | sí: estado y reinicio de la conversación | — | `test_conversation_windows_drive_the_conversation_state` |
| `config.conversation.reset_hours` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Ventanas de la conversación | C | `engine.conversation.reset_hours` | sección interna `engine` | no | sí: estado y reinicio de la conversación | — | `test_conversation_windows_drive_the_conversation_state` |
| `config.features.business_model` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Modelo de negocio | C | `engine.features.business_model` | sección interna `engine` | no | sí: prompt (cuándo mostrar precios) | — | `test_connected_fields_change_the_prompt` |
| `config.features.catalog_mode` | todos | Modo catálogo | C | `engine.features.catalog_mode` | sección interna `engine` | no | sí: prompt (cuándo mostrar precios) | — | `test_connected_fields_change_the_prompt` |
| `config.features.multi_currency` | todos | Varias monedas | E | `compatibility` (misma ruta) | — | no | no | Derivable de los precios; contradice la oferta en agencia_viajes (true con una sola moneda). | — |
| `config.features.multi_plan` | todos | Varios planes | E | `compatibility` (misma ruta) | — | no | no | Derivable de la oferta; contradice la oferta en asesor_ai_prod, clinic y saas (true con un solo plan). | — |
| `config.features.pricing_enabled` | todos | Mostrar precios | C | `engine.features.pricing_enabled` | sección interna `engine` | no | no | El prompt solo lo consulta si no hay precios ni pagos, algo que el contrato no permite (toda oferta tiene precio). | — |
| `config.flags.ai_first` | todos | Banderas internas (ai_first, allow_fallback, log_level) | C | `compatibility` (misma ruta) | — | no | no | Sin consumidor en el motor; no son decisiones del negocio. | — |
| `config.flags.allow_fallback` | todos | Banderas internas (ai_first, allow_fallback, log_level) | C | `compatibility` (misma ruta) | — | no | no | Sin consumidor en el motor; no son decisiones del negocio. | — |
| `config.flags.log_level` | todos | Banderas internas (ai_first, allow_fallback, log_level) | C | `compatibility` (misma ruta) | — | no | no | Sin consumidor en el motor; no son decisiones del negocio. | — |
| `config.initial_message.enabled` | todos | Mensaje de bienvenida activo | A | `messages.welcome.enabled` | — | pantalla | sí: primer mensaje | — | `test_welcome_message_toggle` |
| `config.initial_message.recency.active_minutes` | demo | Ventanas del mensaje inicial (antiguas) | E | `compatibility` (misma ruta) | — | no | no | Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h). | — |
| `config.initial_message.recency.reset_hours` | demo | Ventanas del mensaje inicial (antiguas) | E | `compatibility` (misma ruta) | — | no | no | Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h). | — |
| `config.initial_message.text` | todos | Texto de bienvenida | A | `messages.welcome.text` | — | pantalla | sí: primer mensaje | — | `test_welcome_message_toggle` |
| `config.post_payment.on_payment_confirmed.message` | todos | Mensaje de pago confirmado | A | `messages.payment_confirmed` | renombrado | pantalla | sí: prompt post-pago | — | `test_connected_fields_change_the_prompt` |
| `config.post_payment.on_user_report.message` | todos | Respuesta al reportar un pago | A | `messages.payment_reported` | renombrado | pantalla | sí: respuesta exacta | — | `test_payment_report_message_is_optional` |
| `config.response.length` | todos | Largo de las respuestas | A | `response_style.length` | — | pantalla | sí: prompt y recorte | — | `test_each_response_length_option_controls_prompt_and_truncation` |
| `config.response.max_words` | todos | Límite avanzado de palabras | B | `response_style.max_words` | — | modelo | sí: prompt y recorte | — | `test_changing_the_contract_changes_response_length` |

## Referencia de campos del contrato

Generada del JSON Schema (`x-audience`, `x-engine`). Cada campo hoja del contrato, con quién lo configura,
si el motor actual lo usa y de dónde viene.

- **Audiencia:** `cliente` (lo configura el negocio), `avanzado` (estrategia comercial detallada, opcional),
  `operador` (ajustes internos del motor) o `sistema`.
- **Motor:** `conectado` (el motor actual lo usa; prueba en `tests/test_business_config_engine_integration.py`),
  `pendiente` (representado y conservado, sin uso en el motor actual) o `conservado` (`compatibility`).
- **Origen:** campo de los YAML, `nuevo` (solo existe en el contrato) o `derivado` (lo crea la importación).

| Audiencia | Conectados | Pendientes | Conservados |
|---|---|---|---|
| cliente | 47 | 89 | 0 |
| avanzado | 5 | 39 | 0 |
| operador | 4 | 4 | 0 |
| sistema | 2 | 0 | 1 |
| **Total** | 58 | 132 | 1 |

| Campo | Audiencia | Motor | Origen | Interfaz | Descripción |
|---|---|---|---|---|---|
| `capabilities.actions_primary` | cliente | conectado | `config.capabilities.actions.primary` | pantalla | Acciones de venta. |
| `capabilities.actions_support` | cliente | conectado | `config.capabilities.actions.support` | pantalla | Acciones de apoyo. |
| `capabilities.closing_methods.data_collection` | cliente | conectado | `config.capabilities.closing_methods.data_collection.enabled` | pantalla | Cerrar pidiendo datos |
| `capabilities.closing_methods.human_handoff` | cliente | conectado | `config.capabilities.closing_methods.human_handoff.enabled` | pantalla | Pasar a una persona |
| `capabilities.closing_methods.payment_link` | cliente | conectado | `config.capabilities.closing_methods.link_payment.enabled` | pantalla | Cerrar enviando el pago |
| `capabilities.data_collection.consent_notice` | cliente | pendiente | nuevo | no | Aviso de tratamiento de datos personales que el asistente comparte al pedirlos. |
| `capabilities.data_collection.enabled` | cliente | conectado | `config.capabilities.data_collection.enabled` | pantalla | Pedir datos al cliente |
| `capabilities.data_collection.fields` | cliente | conectado | `config.capabilities.data_collection.fields` | pantalla | Datos que se piden |
| `capabilities.human_handoff_when` | cliente | pendiente | nuevo | no | Situaciones en las que el asistente pasa la conversación a una persona. |
| `capabilities.product_channels` | cliente | conectado | `config.capabilities.system_channels.allowed` | no | Canales por los que funciona el producto que se vende. |
| `capabilities.restrictions.disallowed_actions` | cliente | pendiente | `config.capabilities.constraints.**` | no | Acciones que el negocio no realiza (p. ej. llamadas). |
| `capabilities.restrictions.disallowed_channels` | cliente | pendiente | `config.capabilities.constraints.**` | no | Canales por los que el negocio no atiende. |
| `capabilities.restrictions.forbidden_claims` | cliente | pendiente | nuevo | no | Promesas o afirmaciones que el asistente nunca debe hacer (resultados garantizados, diagnósticos...). |
| `capabilities.service_channels` | cliente | conectado | `config.capabilities.business_channels.allowed` | pantalla | Canales de atención al cliente. |
| `compatibility` | sistema | conservado | derivado | — | Datos de los YAML antiguos sin lugar en el contrato, conservados con su ruta original. |
| `engine.conversation.active_window_minutes` | operador | conectado | `config.conversation.**` | no | Minutos sin mensajes tras los que la conversación deja de estar activa. |
| `engine.conversation.reset_hours` | operador | conectado | `config.conversation.**` | no | Horas sin mensajes tras las que la conversación empieza de nuevo. |
| `engine.features.business_model` | operador | conectado | `config.features.business_model` | no | Modelo de negocio con el que el motor decide cuándo mostrar precios. |
| `engine.features.catalog_mode` | operador | conectado | `config.features.catalog_mode` | no | Debe coincidir con `offer.model` (catalog). |
| `engine.features.pricing_enabled` | operador | pendiente | `config.features.pricing_enabled` | no | Bandera heredada: el motor solo la consulta si no hay precios ni pagos, y el contrato siempre los exige. |
| `fulfillment.delivery.available` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.delivery.cost.type` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.delivery.cost.value` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.delivery.time.max` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.delivery.time.min` | cliente | pendiente | `business.logistics.**` | no | Tiempo mínimo, en texto (p. ej. 30 min, 2 dias). |
| `fulfillment.delivery.type` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.delivery.zones` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.pickup.available` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.pickup.instructions` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.scheduling.required` | cliente | pendiente | `business.logistics.**` | no | Si el servicio requiere agendar una cita o reserva. |
| `fulfillment.shipping.available` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.shipping.cost.type` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.shipping.cost.value` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.shipping.providers` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.shipping.scope` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.shipping.time.max` | cliente | pendiente | `business.logistics.**` | no | Domicilio, envío, recogida y agenda |
| `fulfillment.shipping.time.min` | cliente | pendiente | `business.logistics.**` | no | Tiempo mínimo, en texto (p. ej. 30 min, 2 dias). |
| `identity.brand_name` | cliente | pendiente | nuevo | modelo | Marca con la que el asistente presenta al negocio, si es distinta del nombre. |
| `identity.credibility` | cliente | pendiente | `business.credibility` | no | Pruebas de confianza: casos, resultados, trayectoria. |
| `identity.description` | cliente | pendiente | `business.description` | pantalla | Qué hace el negocio. |
| `identity.differentiators` | cliente | pendiente | `business.differentiators` | modelo | Por qué elegir este negocio y no otro. |
| `identity.industry` | cliente | conectado | `business.industry` | pantalla | Sector o tipo de negocio, en pocas palabras. |
| `identity.location.address` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.city` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.coverage.type` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.coverage.zones` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.type` | cliente | pendiente | `business.location.**` | modelo | virtual, fisico (local propio) o mixto. |
| `identity.name` | cliente | pendiente | `business.name` | pantalla | Nombre del negocio. |
| `identity.opening_hours[].closes` | cliente | pendiente | nuevo | no | Hora HH:MM (24 h). |
| `identity.opening_hours[].days` | cliente | pendiente | nuevo | no | Días de atención |
| `identity.opening_hours[].opens` | cliente | pendiente | nuevo | no | Hora HH:MM (24 h). |
| `identity.positioning` | cliente | pendiente | `business.positioning` | no | A quién se dirige y qué problema resuelve. |
| `identity.service_modes` | cliente | pendiente | `business.service_modes` | modelo | Cómo recibe el cliente el servicio o producto. |
| `identity.target_customer.company_size` | cliente | pendiente | `business.customer_profile.**` | no | Cliente ideal |
| `identity.target_customer.maturity` | cliente | pendiente | `business.customer_profile.**` | no | Situación típica del cliente al llegar. |
| `identity.target_customer.roles` | cliente | pendiente | `business.customer_profile.**` | no | Quién suele escribir o decidir la compra. |
| `identity.target_customer.segment` | cliente | pendiente | `business.customer_profile.**` | no | Tipo de cliente al que se dirige el negocio. |
| `identity.value_proposition` | cliente | conectado | `business.promise` | pantalla | Promesa comercial: qué gana el cliente. |
| `inventory.items[].product_id` | cliente | pendiente | `inventory.items[].**` | no | Id de un producto del catálogo. |
| `inventory.items[].variants[].attributes` | cliente | pendiente | `inventory.items[].**` | no | Talla, color u otras características. |
| `inventory.items[].variants[].prices[].amount` | cliente | pendiente | nuevo | no | Precio de la variante |
| `inventory.items[].variants[].prices[].currency` | cliente | pendiente | nuevo | no | Moneda del precio de la variante |
| `inventory.items[].variants[].sku` | cliente | pendiente | `inventory.items[].**` | no | Producto con variantes y existencias |
| `inventory.items[].variants[].stock` | cliente | pendiente | `inventory.items[].**` | no | Producto con variantes y existencias |
| `inventory.track_stock` | cliente | pendiente | `inventory.track_stock` | no | Si el negocio controla existencias. |
| `knowledge.faqs[].answer` | cliente | pendiente | nuevo | pantalla | Respuesta oficial |
| `knowledge.faqs[].question` | cliente | pendiente | nuevo | pantalla | Pregunta frecuente |
| `messages.after_sale` | cliente | pendiente | nuevo | no | Mensaje después de una compra. |
| `messages.data_request` | cliente | pendiente | nuevo | no | Mensaje para pedir los datos del cliente. |
| `messages.follow_up` | cliente | pendiente | nuevo | no | Mensaje de seguimiento a un cliente que no respondió. |
| `messages.human_handoff` | cliente | pendiente | nuevo | no | Mensaje al pasar la conversación a una persona. |
| `messages.payment_confirmed` | cliente | conectado | `config.post_payment.on_payment_confirmed.message` | pantalla | Mensaje cuando el pago queda confirmado. |
| `messages.payment_reported` | cliente | conectado | `config.post_payment.on_user_report.message` | pantalla | Respuesta exacta cuando el cliente reporta un pago. |
| `messages.welcome.enabled` | cliente | conectado | `config.initial_message.enabled` | pantalla | Mensaje de bienvenida activo |
| `messages.welcome.text` | cliente | conectado | `config.initial_message.text` | pantalla | Texto de bienvenida |
| `offer.catalog.categories[].id` | cliente | conectado | `pricing.catalog.categories[].id` | pantalla | Identificador de la categoría |
| `offer.catalog.categories[].name` | cliente | conectado | `pricing.catalog.categories[].name` | pantalla | Nombre de la categoría |
| `offer.catalog.items[].available` | cliente | conectado | nuevo | pantalla | Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos). |
| `offer.catalog.items[].category` | cliente | conectado | `pricing.catalog.items[].category` | pantalla | Id de su categoría; una categoría sin productos disponibles no se ofrece. |
| `offer.catalog.items[].description` | cliente | pendiente | `pricing.catalog.items[].description` | pantalla | Detalle del producto. |
| `offer.catalog.items[].features` | cliente | pendiente | nuevo | pantalla | Características del producto. |
| `offer.catalog.items[].id` | cliente | pendiente | `pricing.catalog.items[].id` | pantalla | Identificador estable del producto |
| `offer.catalog.items[].name` | cliente | pendiente | `pricing.catalog.items[].name` | pantalla | Nombre del producto |
| `offer.catalog.items[].prices[].amount` | cliente | pendiente | `pricing.catalog.items[].price.<moneda>` | pantalla | Precio del producto por moneda |
| `offer.catalog.items[].prices[].currency` | cliente | pendiente | derivado | — | Clave de moneda en `pricing.catalog.items[].price` |
| `offer.catalog.payment_profile` | cliente | conectado | derivado | — | Perfil de pago con el que se cobra. |
| `offer.model` | cliente | conectado | `pricing.model` | pantalla | plans: planes o servicios; catalog: productos de un catálogo. |
| `offer.plans[].available` | cliente | conectado | nuevo | pantalla | Si es false, el plan se conserva pero no se ofrece. |
| `offer.plans[].description` | cliente | pendiente | `pricing.plans[].description` | pantalla | Detalle del plan. |
| `offer.plans[].id` | cliente | conectado | `pricing.plans[].id` | pantalla | Identificador estable del plan |
| `offer.plans[].includes` | cliente | conectado | `pricing.plans[].includes` | pantalla | Qué incluye |
| `offer.plans[].name` | cliente | conectado | `pricing.plans[].name` | pantalla | Nombre del plan |
| `offer.plans[].not_included` | cliente | conectado | `pricing.plans[].not_included` | pantalla | Qué no incluye |
| `offer.plans[].payment_profile` | cliente | conectado | derivado | — | Perfil de pago con el que se cobra. |
| `offer.plans[].prices[].annual` | cliente | pendiente | nuevo | no | Cobro anual. |
| `offer.plans[].prices[].currency` | cliente | conectado | derivado | — | Clave de moneda en `pricing.plans[].pricing` |
| `offer.plans[].prices[].first_payment` | cliente | conectado | nuevo | no | Valor del primer pago cuando difiere del mensual. |
| `offer.plans[].prices[].implementation` | cliente | conectado | `pricing.plans[].pricing.<moneda>.**` | pantalla | Pago único inicial (instalación, implementación, inscripción). |
| `offer.plans[].prices[].monthly` | cliente | conectado | `pricing.plans[].pricing.<moneda>.**` | pantalla | Cobro mensual. |
| `offer.plans[].prices[].price` | cliente | conectado | nuevo | pantalla | Precio de pago único. |
| `offer.plans[].target` | cliente | pendiente | `pricing.plans[].target` | no | Para quién es este plan. |
| `payments[].id` | cliente | conectado | derivado | — | Perfil de pago creado por la importación (id del plan o `catalog`) |
| `payments[].instructions` | cliente | pendiente | nuevo | no | Indicaciones para pagar, sin números ni links (esos datos son secretos). |
| `payments[].link` | cliente | conectado | `pricing.catalog.payment.link`, `pricing.plans[].payment.link` | pantalla | Link de pago del catálogo |
| `payments[].transfer_enabled` | cliente | conectado | `pricing.catalog.payment.transfer.enabled`, `pricing.plans[].payment.transfer.enabled` | pantalla | Transferencias activas |
| `payments[].transfer_methods[].account_number` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].account_number`, `pricing.plans[].payment.transfer.methods[].account_number` | pantalla | Número de cuenta |
| `payments[].transfer_methods[].account_type` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].account_type`, `pricing.plans[].payment.transfer.methods[].account_type` | pantalla | Tipo de cuenta |
| `payments[].transfer_methods[].bank` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].bank`, `pricing.plans[].payment.transfer.methods[].bank` | pantalla | Banco |
| `payments[].transfer_methods[].number` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].number`, `pricing.plans[].payment.transfer.methods[].number` | pantalla | Celular Nequi o Daviplata |
| `payments[].transfer_methods[].reference` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].reference`, `pricing.plans[].payment.transfer.methods[].reference` | pantalla | Llave o referencia Bre-B |
| `payments[].transfer_methods[].type` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].type`, `pricing.plans[].payment.transfer.methods[].type` | pantalla | Método de transferencia |
| `response_style.emojis` | cliente | pendiente | nuevo | no | Si el asistente puede usar emojis. |
| `response_style.formality` | cliente | pendiente | nuevo | no | informal (tutea), neutral o formal (usted). |
| `response_style.instructions` | cliente | pendiente | nuevo | no | Indicaciones de comunicación del negocio. |
| `response_style.length` | cliente | conectado | `config.response.length` | pantalla | short (cortas), medium (equilibradas) o long (detalladas). |
| `response_style.max_words` | avanzado | conectado | `config.response.max_words` | modelo | Ajuste dentro del rango de la opción elegida. Si falta, el límite de la opción. |
| `response_style.tone` | cliente | pendiente | `business.tone` | modelo | Tono del asistente (p. ej. cercano y claro). |
| `response_style.voice` | cliente | pendiente | `business.voice` | no | Personalidad de la marca. |
| `sales.angles[].messages` | avanzado | pendiente | `sales.angles.<motivo>.execution` | no | Qué decir con este ángulo. |
| `sales.angles[].motivation` | avanzado | pendiente | derivado | — | Motivo de compra de `motivation_drivers` al que responde. |
| `sales.angles[].signals` | avanzado | pendiente | `sales.angles.<motivo>.when` | no | Cuándo usar el ángulo: frases del cliente. |
| `sales.arguments` | cliente | pendiente | `sales.solution.framing` | modelo | Argumentos de venta. |
| `sales.benefits` | cliente | pendiente | `business.desired_outcomes` | modelo | Resultados que obtiene el cliente. |
| `sales.buying_motivation.primary` | cliente | conectado | `business.buying_motivation.primary` | pantalla | Motivo principal de compra |
| `sales.buying_motivation.secondary` | cliente | conectado | `business.buying_motivation.secondary` | pantalla | Motivo secundario de compra |
| `sales.closing.high_intent_actions` | avanzado | pendiente | `sales.closing.actions.high_intent` | no | Qué hacer ante una intención de compra alta. |
| `sales.closing.micro_commitments` | avanzado | pendiente | `sales.closing.micro_commitments` | no | Compromisos pequeños para avanzar. |
| `sales.closing.next_steps` | avanzado | pendiente | `sales.closing.next_steps` | no | Siguientes pasos que el asistente propone. |
| `sales.closing.purchase_signals` | avanzado | pendiente | `sales.closing.triggers` | no | Frases que indican intención de compra. |
| `sales.closing.required_data` | avanzado | pendiente | `sales.closing.required_data` | no | Datos que necesita el cierre (name, phone, address...). |
| `sales.closing.rules` | avanzado | pendiente | `sales.closing.hard_rules` | no | Reglas de cierre del negocio. |
| `sales.closing.strategy` | avanzado | pendiente | `sales.closing.strategy` | no | Venta directa, captación de datos, reserva o compra con pago (checkout). |
| `sales.conversation_flow.guided_process` | operador | pendiente | `sales.conversation_flow.rules.guided_process` | no | Guiar al cliente paso a paso en un proceso (trámites, matrículas). |
| `sales.conversation_flow.no_skip_steps` | operador | pendiente | `sales.conversation_flow.rules.no_skip_steps` | no | No saltar etapas |
| `sales.conversation_flow.steps` | operador | pendiente | `sales.conversation_flow.steps` | no | Etapas internas del motor, en orden (p. ej. detect_pain, present_solution). |
| `sales.customer_problems[].id` | cliente | conectado | derivado | — | Clave del problema en `sales.pain.clusters` |
| `sales.customer_problems[].impacts` | cliente | conectado | `sales.pain.clusters.<problema>.impacts` | pantalla | Qué le causa el problema al cliente. |
| `sales.customer_problems[].monetization` | avanzado | pendiente | `sales.pain.clusters.<problema>.monetization` | no | Cómo el problema le cuesta dinero al cliente. |
| `sales.customer_problems[].recommended_angles` | avanzado | pendiente | `sales.pain.clusters.<problema>.recommended_angles` | no | Ángulos de venta para este problema. |
| `sales.customer_problems[].signals` | avanzado | pendiente | `sales.pain.clusters.<problema>.signals` | no | Frases del cliente que revelan el problema. |
| `sales.customer_problems[].urgency_levels` | avanzado | pendiente | `sales.pain.clusters.<problema>.urgency_levels.**` | no | Mensajes según la urgencia. |
| `sales.discovery.objectives` | avanzado | pendiente | `sales.discovery.objectives` | no | Qué debe averiguar el asistente. |
| `sales.discovery.questions` | cliente | pendiente | `sales.discovery.questions` | modelo | Preguntas para entender al cliente. |
| `sales.instructions` | cliente | pendiente | nuevo | modelo | Instrucciones de venta del negocio. |
| `sales.motivation_drivers[].description` | avanzado | pendiente | `business.value_drivers.<motivo>.description` | no | Qué significa cada motivo de compra |
| `sales.motivation_drivers[].motivation` | avanzado | pendiente | derivado | — | Motivo de compra (p. ej. tiempo, dinero). |
| `sales.motivation_drivers[].signals` | avanzado | pendiente | `business.value_drivers.<motivo>.triggers` | no | Frases del cliente que revelan este motivo. |
| `sales.objections[].acknowledge` | avanzado | pendiente | `sales.objection.<objecion>.layers.**` | no | Cómo reconocer la objeción. |
| `sales.objections[].proof` | avanzado | pendiente | `sales.objection.<objecion>.layers.**` | no | Pruebas que la desmienten. |
| `sales.objections[].redirect` | avanzado | pendiente | `sales.objection.<objecion>.layers.**` | no | Cómo volver al siguiente paso. |
| `sales.objections[].reframe` | avanzado | pendiente | `sales.objection.<objecion>.layers.**` | no | Cómo replantearla. |
| `sales.objections[].rules` | avanzado | pendiente | `sales.objection.<objecion>.hard_rules` | no | Reglas al responder esta objeción. |
| `sales.objections[].topic` | avanzado | pendiente | derivado | — | Objeción que se atiende (p. ej. price). |
| `sales.offer_mix.core` | avanzado | pendiente | `pricing.business_offers.core` | no | Ofertas principales. |
| `sales.offer_mix.cross_sell` | avanzado | pendiente | `pricing.business_offers.cross_sell` | no | Complementos para vender junto. |
| `sales.offer_mix.upsell` | avanzado | pendiente | `pricing.business_offers.upsell` | no | Mejoras para vender más. |
| `sales.offer_presentation.multiple_offers` | avanzado | pendiente | `sales.offer.strategy.multi` | no | Cómo presentar cuando hay varias opciones. |
| `sales.offer_presentation.single_offer` | avanzado | pendiente | `sales.offer.strategy.single` | no | Cómo presentar cuando hay una sola opción. |
| `sales.pain_points` | cliente | pendiente | `business.pain_points` | no | Problemas del cliente en sus palabras. |
| `sales.qualification.criteria` | avanzado | pendiente | nuevo | no | Criterios para considerar a alguien un cliente potencial. |
| `sales.qualification.detect_offer_fit` | avanzado | pendiente | `sales.qualification.detect_offer_fit` | no | Si el asistente debe comprobar que la oferta encaja con el cliente. |
| `sales.recommendation_rules[].recommend` | cliente | pendiente | nuevo | modelo | Id de un plan, producto o categoría de la oferta. |
| `sales.recommendation_rules[].when` | cliente | pendiente | nuevo | modelo | Situación o necesidad del cliente. |
| `sales.solution.mapping[].problem` | avanzado | pendiente | derivado | — | Id de un problema de `customer_problems`. |
| `sales.solution.mapping[].solutions` | avanzado | pendiente | `sales.solution.mapping.<problema>` | no | Qué parte de la solución atiende cada problema |
| `sales.solution.process_steps` | cliente | pendiente | `sales.solution.process_steps` | no | Pasos que sigue el cliente para comprar o recibir el servicio. |
| `sales.solution.requirements` | cliente | pendiente | `sales.solution.requirements` | no | Requisitos que debe cumplir el cliente. |
| `sales.support.explain_first` | avanzado | pendiente | `sales.support.info_handling.explain_first` | no | Ante una pregunta, explicar antes de vender. |
| `sales.support.rules` | avanzado | pendiente | `sales.support.hard_rules` | no | Reglas de atención del negocio. |
| `sales.support.sell_after` | avanzado | pendiente | `sales.support.info_handling.sell_after` | no | Después de explicar, llevar la conversación a la venta. |
| `sales.use_cases[].approach` | avanzado | pendiente | `business.use_cases[].enfoque` | no | Enfoque de la solución para este caso. |
| `sales.use_cases[].name` | avanzado | conectado | `business.use_cases[].nombre` | no | Caso de uso típico |
| `sales.use_cases[].signals` | avanzado | pendiente | `business.use_cases[].senales` | no | Señales del caso de uso |
| `schema_version` | sistema | conectado | derivado | — | Versión del contrato |
| `tenant_slug` | sistema | conectado | derivado | — | Negocio dueño del documento |
| `terms.conditions` | cliente | conectado | `pricing.conditions` | pantalla | Condiciones reales de compra. |
| `terms.financing.available` | cliente | pendiente | `pricing.business_offers.financing.**` | no | Financiación |
| `terms.financing.options` | cliente | pendiente | `pricing.business_offers.financing.**` | no | Modalidades (abono, cuotas...). |
| `terms.financing.providers` | cliente | pendiente | `pricing.business_offers.financing.**` | no | Entidades con las que se financia. |
| `terms.policies.cancellation` | cliente | pendiente | nuevo | no | Cancelaciones y reembolsos (citas, reservas, suscripciones). |
| `terms.policies.returns` | cliente | pendiente | nuevo | no | Cambios y devoluciones. |
| `terms.policies.warranty` | cliente | pendiente | nuevo | no | Garantía: qué cubre y por cuánto tiempo. |
| `terms.price_framing` | avanzado | conectado | `pricing.price_framing.type` | no | Cómo responder si el cliente duda del precio. |
| `terms.price_note` | cliente | pendiente | `pricing.note` | no | Aclaración sobre cómo se confirma el precio. |
| `terms.prices_include_taxes` | cliente | pendiente | nuevo | no | Si los precios publicados ya incluyen los impuestos (IVA). |
| `terms.promotions[].details` | cliente | pendiente | nuevo | modelo | Qué incluye la promoción y a qué aplica. |
| `terms.promotions[].name` | cliente | pendiente | nuevo | modelo | Nombre de la promoción |
| `terms.promotions[].valid_until` | cliente | pendiente | nuevo | modelo | Último día de vigencia. |
| `terms.roi_break_even_bookings` | avanzado | pendiente | `pricing.roi.break_even_reservas` | no | Reservas con las que el cliente recupera la inversión. |
| `terms.roi_break_even_sales` | avanzado | conectado | `pricing.roi.break_even_sales` | no | Ventas al mes con las que el cliente recupera la inversión. |
| `terms.roi_hints` | avanzado | conectado | `pricing.roi_hints` | no | Argumentos de retorno de la inversión. |

## Campos del contrato que crea la importación

Se derivan de claves o de la estructura de los YAML, no de un valor concreto.

| Campo | Origen |
|---|---|
| `compatibility` | Datos antiguos sin lugar en el contrato |
| `offer.catalog.items[].prices[].currency` | Clave de moneda en `pricing.catalog.items[].price` |
| `offer.catalog.payment_profile` | Enlace del catálogo con su perfil de pago |
| `offer.plans[].payment_profile` | Enlace del plan con su perfil de pago |
| `offer.plans[].prices[].currency` | Clave de moneda en `pricing.plans[].pricing` |
| `payments[].id` | Perfil de pago creado por la importación (id del plan o `catalog`) |
| `sales.angles[].motivation` | Clave del motivo en `sales.angles` |
| `sales.customer_problems[].id` | Clave del problema en `sales.pain.clusters` |
| `sales.motivation_drivers[].motivation` | Clave del motivo en `business.value_drivers` |
| `sales.objections[].topic` | Clave de la objeción en `sales.objection` |
| `sales.solution.mapping[].problem` | Clave del problema en `sales.solution.mapping` |
| `schema_version` | Versión del contrato |
| `tenant_slug` | Negocio dueño del documento |
