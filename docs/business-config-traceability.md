# Matriz de trazabilidad: YAML antiguos → BusinessConfig v1

Versión del contrato: `1.0`. Negocios: 9. Patrones catalogados: 131.

> Archivo generado por `scripts/generate_traceability_matrix.py` desde
> `project/app/infrastructure/config/legacy_field_catalog.py`. No editar a mano: `--check` falla si
> está desactualizado y `tests/test_business_config_traceability.py` lo comprueba.

Cada fila es un campo de los YAML de origen (`business.yaml`, `sales.yaml`, `pricing.yaml`,
`inventory.yaml`, `config.yaml`). Solo se muestran rutas; los únicos valores son los de interruptores y
opciones, en la tabla de funcionalidades comerciales.

- **Conservado en los datos:** todos los campos, en todos los negocios. Lo comprueba
  `test_business_config_traceability.py::test_every_legacy_field_reaches_its_declared_destination`: el valor original está en el destino declarado.
- **Representado en el contrato:** la columna Destino. `ajustes técnicos` significa que el dato está en
  `engine-settings.json`, fuera del documento comercial (ver Justificación).
- **Interfaz:** `pantalla` (el panel tiene un control), `modelo` (el modelo y el adaptador del panel
  lo admiten, pero aún no hay pantalla) o `no`.
- **Motor:** `sí` solo con evidencia (columna Prueba) de que el motor actual lo usa; `no` si solo está
  representado. Las pruebas de uso están en `tests/test_business_config_engine_integration.py`.
- `[]` es un índice de lista; `<nombre>` una clave variable (id de problema, moneda...).

Clases: **A** configuración que edita el cliente; **B** configuración comercial avanzada; **C** ajuste técnico del motor; **D** información sensible (datos de pago); **E** derivada, obsoleta o redundante.

## Resumen por negocio

| Negocio | Campos | Comerciales | Datos de pago (referencias) | Técnicos | Definición común | A | B | C | D | E |
|---|---|---|---|---|---|---|---|---|---|---|
| agencia_viajes | 145 | 129 | 5 | 6 | 5 | 92 | 36 | 6 | 5 | 6 |
| asesor_ai_prod | 164 | 148 | 5 | 6 | 5 | 83 | 64 | 6 | 5 | 6 |
| clinic | 109 | 93 | 5 | 6 | 5 | 72 | 20 | 6 | 5 | 6 |
| demo | 162 | 141 | 10 | 6 | 5 | 93 | 47 | 4 | 10 | 8 |
| ecommerce | 109 | 93 | 5 | 6 | 5 | 72 | 20 | 6 | 5 | 6 |
| escuela_conduccion | 144 | 128 | 5 | 6 | 5 | 103 | 24 | 6 | 5 | 6 |
| restaurant | 128 | 111 | 5 | 7 | 5 | 90 | 20 | 6 | 5 | 7 |
| saas | 112 | 96 | 5 | 6 | 5 | 72 | 23 | 6 | 5 | 6 |
| tienda_ropa | 138 | 122 | 5 | 6 | 5 | 101 | 20 | 6 | 5 | 6 |
| **Total** | 1211 | 1061 | 50 | 55 | 45 | 778 | 274 | 52 | 50 | 57 |

## Funcionalidades comerciales conservadas

Las funcionalidades que ya tenían los YAML, con sus opciones y valores sin cambios. **Tipo y opciones** sale del
JSON Schema: es la validación que aplica el contrato. **Valores actuales** cuenta cuántos negocios tienen cada valor.

| Grupo | Campo original | Comportamiento | Destino en el contrato | Tipo y opciones | Valores actuales | Motor |
|---|---|---|---|---|---|---|
| Saludo | `config.initial_message.enabled` | Dos modalidades. `true`: ante un saludo sin más en una conversación nueva, el sistema envía el texto fijo, sin IA. `false`: no lo envía y responde la IA. Un saludo con intención siempre lo responde la IA. | `messages.welcome.enabled` | interruptor true/false | true (9) | conectado |
| Saludo | `config.initial_message.text` | Mensaje de apertura que recibe el usuario; se conserva aunque esté desactivado. | `messages.welcome.text` | texto | texto libre (9 valores) | conectado |
| Extensión de los mensajes | `config.response.length` | Tamaño de la respuesta, en el prompt y al recortarla. | `response_style.length` | short \| medium \| long | short (8), medium (1) | conectado |
| Extensión de los mensajes | `config.response.max_words` | Máximo de palabras por respuesta, dentro del rango de `length`. | `response_style.max_words` | entero (mínimo 20) | 60 (8), 75 (1) | conectado |
| Interruptores de venta | `config.features.pricing_enabled` | `true`: permite usar precios en la conversación. | `features.pricing_enabled` | interruptor true/false | true (9) | pendiente |
| Interruptores de venta | `config.features.catalog_mode` | `true`: vende opciones tipo catálogo. `false`: vende un servicio o plan. | `features.catalog_mode` | interruptor true/false | true (5), false (4) | conectado |
| Interruptores de venta | `config.features.multi_currency` | `true`: permite manejar más de una moneda. | `features.multi_currency` | interruptor true/false | false (6), true (3) | pendiente |
| Interruptores de venta | `config.features.multi_plan` | `true`: permite ofrecer varios planes. | `features.multi_plan` | interruptor true/false | false (5), true (4) | pendiente |
| Interruptores de venta | `config.features.business_model` | Tipo de negocio; con él el motor decide cuándo mostrar precios. | `features.business_model` | saas \| catalog \| checkout \| service_booking \| process | catalog (2), saas (2), checkout (2), service_booking (1), process (1) | conectado |
| Atención | `sales.support.info_handling.explain_first` | `true`: primero aclara la duda. `false`: vende directo. | `sales.support.explain_first` | interruptor true/false | true (8), false (1) | pendiente |
| Atención | `sales.support.info_handling.sell_after` | `true`: después de explicar, vuelve a llevar al cliente a avanzar. | `sales.support.sell_after` | interruptor true/false | true (9) | pendiente |
| Atención | `sales.qualification.detect_offer_fit` | `true`: valida si la oferta encaja antes de empujar el cierre. | `sales.qualification.detect_offer_fit` | interruptor true/false | true (2) | pendiente |
| Flujo de conversación | `sales.conversation_flow.steps` | Pasos que idealmente sigue la conversación. | `sales.conversation_flow.steps` | lista de texto con formato validado | ["detect_pain", "amplify_impact", "present_solution", "guide_next_step"] (2), ["detect_pain", "present_solution", "validate_requirements", "guide_next_step"] (1) | pendiente |
| Flujo de conversación | `sales.conversation_flow.rules.no_skip_steps` | `true`: no se saltan pasos. | `sales.conversation_flow.no_skip_steps` | interruptor true/false | true (3) | pendiente |
| Flujo de conversación | `sales.conversation_flow.rules.guided_process` | `true`: guía al cliente paso a paso en un proceso. | `sales.conversation_flow.guided_process` | interruptor true/false | true (1) | pendiente |
| Flujo de conversación | `sales.progression_rules.required_flow` | Secuencia mínima que debe respetar la conversación. | `sales.conversation_flow.required_flow` | lista de texto con formato validado | ["detect_pain", "amplify_impact", "present_solution", "guide_next_step"] (9) | pendiente |
| Flujo de conversación | `sales.progression_rules.forbid` | Lo que el asistente no debe hacer en este negocio. | `sales.conversation_flow.forbid` | lista de texto con formato validado | ["responder_sin_direccion", "responder_sin_solucion"] (2) | pendiente |
| Cierre | `sales.closing.strategy` | Tipo de cierre. | `sales.closing.strategy` | direct_sale \| lead_capture \| booking \| checkout | booking (4), direct_sale (3), checkout (2) | pendiente |
| Cierre | `config.capabilities.closing_methods.link_payment.enabled` | `true`: permite enviar un enlace de pago directo al cliente. | `capabilities.closing_methods.payment_link` | interruptor true/false | true (9) | conectado |
| Cierre | `config.capabilities.closing_methods.human_handoff.enabled` | `true`: permite escalar la conversación a una persona. | `capabilities.closing_methods.human_handoff` | interruptor true/false | true (9) | conectado |
| Cierre | `config.capabilities.closing_methods.data_collection.enabled` | `true`: permite cerrar pidiendo los datos del cliente. | `capabilities.closing_methods.data_collection` | interruptor true/false | true (9) | conectado |
| Cierre | `config.capabilities.data_collection.enabled` | `true`: el asistente puede pedir datos al cliente. | `capabilities.data_collection.enabled` | interruptor true/false | true (9) | conectado |
| Cierre | `config.capabilities.data_collection.fields` | Datos que el asistente pide. | `capabilities.data_collection.fields` | lista de texto | ["nombre", "telefono", "detalles"] (6), ["nombre", "telefono", "direccion", "detalles"] (3) | conectado |
| Precio | `pricing.price_framing.type` | Forma de presentar el precio. | `terms.price_framing` | directo \| comparativo | comparativo (5), directo (4) | conectado |
| Precio | `pricing.business_offers.financing.available` | `true`: permite financiación. `false`: no la ofrece. | `terms.financing.available` | interruptor true/false | true (5), false (3) | pendiente |
| Recomendaciones | `sales.offer.recommendation_rules[].condition` | Situación que activa una recomendación. | `sales.recommendation_rules[].when` | texto | texto libre (4 valores) | pendiente |
| Recomendaciones | `sales.offer.recommendation_rules[].recommend` | Plan que se recomienda en esa situación. | `sales.recommendation_rules[].recommend` | texto con formato validado | texto libre (4 valores) | pendiente |
| Entrega | `business.logistics.delivery.available` | `true`: ofrece domicilio. | `fulfillment.delivery.available` | interruptor true/false | false (7), true (2) | pendiente |
| Entrega | `business.logistics.shipping.available` | `true`: ofrece envío. | `fulfillment.shipping.available` | interruptor true/false | false (7), true (2) | pendiente |
| Entrega | `business.logistics.pickup.available` | `true`: ofrece recogida. | `fulfillment.pickup.available` | interruptor true/false | false (7), true (2) | pendiente |
| Entrega | `business.logistics.scheduling.required` | `true`: el servicio requiere agendar. | `fulfillment.scheduling.required` | interruptor true/false | false (6), true (3) | pendiente |
| Inventario | `inventory.track_stock` | `true`: el negocio controla existencias. | `inventory.track_stock` | interruptor true/false | false (8), true (1) | pendiente |

## Ajustes técnicos

Fuera del documento comercial, en `engine-settings.json`. El negocio no los edita y el panel no los recibe.

| Campo original | Significado | Destino | Motivo |
|---|---|---|---|
| `business.type` | Tipo de negocio | ajustes técnicos: `legacy` (misma ruta) | Solo restaurant; repite el sector (`industry`) y el tipo de negocio de `features`. |
| `config.capabilities.channels` | Canales (lista antigua) | ajustes técnicos: `legacy` (misma ruta) | Estructura antigua: el prompt solo la usa si no hay canales de atención ni del sistema, lo que no ocurre en ningún negocio. En asesor_ai_prod contradice a `business_channels` (vacío). |
| `config.conversation.**` | Ventanas de la conversación | ajustes técnicos: `conversation.**` | Parámetro interno: cuándo el motor considera activa o nueva una conversación. |
| `config.flags.**` | Banderas internas (ai_first, allow_fallback, log_level) | ajustes técnicos: `flags.**` | Sin consumidor en el motor; no son decisiones del negocio. |
| `config.initial_message.recency.**` | Ventanas del mensaje inicial (antiguas) | ajustes técnicos: `legacy` (misma ruta) | Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h). |

## Campos propios del contrato

Finalidad comercial, sin origen en los YAML. No se compilan salvo los marcados `conectado`.

| Módulo | Campo | Responsabilidad | Tipo y opciones | Audiencia | Motor | Interfaz |
|---|---|---|---|---|---|---|
| identity | `identity.opening_hours[].closes` | Hora de cierre (HH:MM, 24 h). | texto con formato validado | cliente | pendiente | no |
| identity | `identity.opening_hours[].days` | Días en los que aplica este horario. | lista de lunes \| martes \| miercoles \| jueves \| viernes \| sabado \| domingo | cliente | pendiente | no |
| identity | `identity.opening_hours[].opens` | Hora de apertura (HH:MM, 24 h). | texto con formato validado | cliente | pendiente | no |
| inventory | `inventory.items[].variants[].prices[].amount` | Precio en esa moneda. | número | cliente | pendiente | no |
| inventory | `inventory.items[].variants[].prices[].currency` | Moneda (código ISO de tres letras). | texto con formato validado | cliente | pendiente | no |
| knowledge | `knowledge.faqs[].answer` | Respuesta oficial del negocio. | texto | cliente | pendiente | pantalla |
| knowledge | `knowledge.faqs[].question` | Pregunta tal como la haría el cliente. | texto | cliente | pendiente | pantalla |
| messages | `messages.after_sale` | Mensaje después de una compra. | texto | cliente | pendiente | no |
| messages | `messages.data_request` | Mensaje para pedir los datos del cliente. | texto | cliente | pendiente | no |
| messages | `messages.follow_up` | Mensaje de seguimiento a un cliente que no respondió. | texto | cliente | pendiente | no |
| messages | `messages.human_handoff` | Mensaje al pasar la conversación a una persona. | texto | cliente | pendiente | no |
| offer | `offer.catalog.items[].available` | Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos). | interruptor true/false | cliente | conectado | pantalla |
| offer | `offer.catalog.items[].features` | Características del producto. | lista de texto | cliente | pendiente | pantalla |
| offer | `offer.plans[].available` | Si es false, el plan se conserva pero no se ofrece. | interruptor true/false | cliente | conectado | pantalla |
| offer | `offer.plans[].prices[].annual` | Cobro anual. | número | cliente | pendiente | no |
| offer | `offer.plans[].prices[].first_payment` | Valor del primer pago, si difiere de los siguientes. | número | cliente | conectado | no |
| offer | `offer.plans[].prices[].price` | Precio de pago único. | número | cliente | conectado | pantalla |
| payments | `payments[].link_enabled` | Si es false, el enlace se conserva pero no se ofrece. | interruptor true/false | cliente | conectado | pantalla |
| payments | `payments[].transfer_methods[].enabled` | Si es false, la cuenta se conserva pero no se ofrece. | interruptor true/false | cliente | conectado | pantalla |
| payments | `payments[].transfer_methods[].label` | Titular o etiqueta para reconocer la cuenta en el panel. No se comparte con el cliente. | texto | cliente | pendiente | pantalla |
| response_style | `response_style.emojis` | Si el asistente puede usar emojis. | interruptor true/false | cliente | pendiente | no |
| response_style | `response_style.formality` | informal (tutea), neutral o formal (usted). | informal \| neutral \| formal | cliente | pendiente | no |
| response_style | `response_style.instructions` | Cómo debe expresarse el asistente en este negocio. | lista de texto | cliente | pendiente | no |
| sales | `sales.instructions` | Cómo debe vender el asistente en este negocio. | lista de texto | cliente | pendiente | modelo |
| terms | `terms.policies.cancellation` | Cancelaciones y reembolsos (citas, reservas, suscripciones). | texto | cliente | pendiente | no |
| terms | `terms.policies.returns` | Cambios y devoluciones. | texto | cliente | pendiente | no |
| terms | `terms.policies.warranty` | Garantía: qué cubre y por cuánto tiempo. | texto | cliente | pendiente | no |
| terms | `terms.promotions[].details` | Qué incluye la promoción y a qué aplica. | texto | cliente | pendiente | modelo |
| terms | `terms.promotions[].name` | Nombre con el que se presenta la promoción. | texto | cliente | pendiente | modelo |
| terms | `terms.promotions[].valid_until` | Último día de vigencia. | fecha | cliente | pendiente | modelo |

## Definición común del sistema

Mismos valores para todos los negocios, que no los configuran: no están en BusinessConfig ni en los ajustes técnicos.
Están en `COMMON_CLOSING_POLICY` (`engine_policy.py`) y el compilador los añade a `sales.closing`, de modo que el motor
recibe lo mismo que con los YAML. Si los YAML de un negocio no coinciden, la importación se detiene.

| Campo original | Valor | Motivo |
|---|---|---|
| `sales.closing.behavior.direct_sale.goal` | `confirmar_compra` | Definición común: mismo valor en los 9 negocios, que tienen los cuatro objetivos aunque usen un solo tipo de cierre. Cambiarlo no altera el motor. |
| `sales.closing.behavior.lead_capture.goal` | `capturar_datos` | Definición común: mismo valor en los 9 negocios, que tienen los cuatro objetivos aunque usen un solo tipo de cierre. Cambiarlo no altera el motor. |
| `sales.closing.behavior.booking.goal` | `agendar` | Definición común: mismo valor en los 9 negocios, que tienen los cuatro objetivos aunque usen un solo tipo de cierre. Cambiarlo no altera el motor. |
| `sales.closing.behavior.checkout.goal` | `enviar_pago` | Definición común: mismo valor en los 9 negocios, que tienen los cuatro objetivos aunque usen un solo tipo de cierre. Cambiarlo no altera el motor. |
| `sales.closing.next_step.action` | `dynamic` | Definición común: vale `dynamic` en los 9 negocios y describe cómo funciona el motor; el siguiente paso sale de la respuesta de la IA. |

## business.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `business.brand_name` | todos | Marca | A | `identity.brand_name` | — | no | no | Igual a `name` en los 9 negocios; se conserva su valor. | — |
| `business.buying_motivation.primary` | agencia_viajes, asesor_ai_prod | Motivo principal de compra | A | `sales.buying_motivation.primary` | cambia de sección | pantalla | sí: prompt (motores de compra) | — | `test_connected_fields_change_the_prompt` |
| `business.buying_motivation.secondary` | agencia_viajes, asesor_ai_prod | Motivo secundario de compra | A | `sales.buying_motivation.secondary` | cambia de sección | pantalla | sí: prompt (motores de compra) | — | `test_connected_fields_change_the_prompt` |
| `business.city` | todos | Ciudad | E | `identity.location.city` | duplicado unificado con `business.location.city` | no | no | Mismo valor que `business.location.city` en los 9 negocios: el contrato la guarda una sola vez y la compilación la devuelve a las dos rutas. | — |
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
| `business.type` | restaurant | Tipo de negocio | E | ajustes técnicos: `legacy` (misma ruta) | — | no | no | Solo restaurant; repite el sector (`industry`) y el tipo de negocio de `features`. | — |
| `business.use_cases[].enfoque` | agencia_viajes, asesor_ai_prod | Enfoque de la solución para el caso | B | `sales.use_cases[].approach` | `enfoque` → `approach` | no | no | — | — |
| `business.use_cases[].nombre` | agencia_viajes, asesor_ai_prod | Caso de uso típico | B | `sales.use_cases[].name` | `nombre` → `name` | no | sí: respaldo de 'Casos típicos' si no hay impactos | — | `test_connected_fields_change_the_prompt` |
| `business.use_cases[].senales` | agencia_viajes, asesor_ai_prod | Señales del caso de uso | B | `sales.use_cases[].signals` | `senales` → `signals` | no | no | — | — |
| `business.value_drivers.<motivo>.description` | agencia_viajes, asesor_ai_prod | Qué significa cada motivo de compra | B | `sales.motivations[motivation=<motivo>].description` | mapa por motivo → lista con `motivation`; se une con `sales.angles` | no | no | — | — |
| `business.value_drivers.<motivo>.triggers` | agencia_viajes, asesor_ai_prod | Frases que revelan cada motivo | B | `sales.motivations[motivation=<motivo>].signals` | mapa por motivo → lista; `triggers` → `signals`; se une con `sales.angles` | no | no | — | — |
| `business.voice` | todos | Personalidad o voz de la marca | A | `response_style.voice` | cambia de sección | no | no | — | — |

## sales.yaml

| Campo antiguo | Negocios | Significado | Clase | Destino | Transformación | Interfaz | Motor | Justificación | Prueba |
|---|---|---|---|---|---|---|---|---|---|
| `sales.angles.<motivo>.execution` | asesor_ai_prod, demo | Qué decir con el ángulo de venta | B | `sales.motivations[motivation=<motivo>].angle.messages` | se une con `business.value_drivers`; `execution` → `messages` | no | no | — | — |
| `sales.angles.<motivo>.when` | asesor_ai_prod, demo | Cuándo usar el ángulo de venta | B | `sales.motivations[motivation=<motivo>].angle.signals` | se une con `business.value_drivers`; `when` → `signals` | no | no | — | — |
| `sales.closing.actions.high_intent` | asesor_ai_prod, demo | Acciones ante intención alta | B | `sales.closing.high_intent_actions` | se aplana `actions` | no | no | — | — |
| `sales.closing.behavior.<estrategia>.goal` | todos | Objetivo de cada tipo de cierre | E | definición común (`engine_policy.py`) | — | no | no | Definición común: mismo valor en los 9 negocios, que tienen los cuatro objetivos aunque usen un solo tipo de cierre. Cambiarlo no altera el motor. | — |
| `sales.closing.hard_rules` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Reglas de cierre | B | `sales.closing.rules` | `hard_rules` → `rules` | no | no | En asesor_ai_prod tres reglas validan el texto de la respuesta (p. ej. que no contenga '?'); el motor no las aplica. Moverlas a las políticas del motor cambia las reglas del negocio: decisión pendiente. | — |
| `sales.closing.micro_commitments` | asesor_ai_prod, demo | Compromisos progresivos | B | `sales.closing.micro_commitments` | — | no | no | — | — |
| `sales.closing.next_step.action` | todos | Modo del siguiente paso | C | definición común (`engine_policy.py`) | — | no | no | Definición común: vale `dynamic` en los 9 negocios y describe cómo funciona el motor; el siguiente paso sale de la respuesta de la IA. | — |
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
| `sales.offer.recommendation_rules[].condition` | asesor_ai_prod, demo | Situación que activa una recomendación | B | `sales.recommendation_rules[].when` | `condition` → `when` | no | no | — | — |
| `sales.offer.recommendation_rules[].recommend` | asesor_ai_prod, demo | Plan recomendado | B | `sales.recommendation_rules[].recommend` | — | no | no | En asesor_ai_prod y demo apunta a planes que no existen: se conserva y lo señala el diagnóstico `recomienda_oferta_no_disponible`. | — |
| `sales.offer.strategy.multi` | asesor_ai_prod, demo | Cómo presentar varias opciones | B | `sales.offer_presentation.multiple_offers` | renombrado | no | no | — | — |
| `sales.offer.strategy.single` | asesor_ai_prod, demo | Cómo presentar una sola opción | B | `sales.offer_presentation.single_offer` | renombrado | no | no | — | — |
| `sales.pain.clusters.<problema>.impacts` | agencia_viajes, asesor_ai_prod, demo, escuela_conduccion | Impactos del problema | A | `sales.customer_problems[id=<problema>].impacts` | mapa por problema → lista con `id` | pantalla | sí: prompt (casos típicos) | — | `test_connected_fields_change_the_prompt` |
| `sales.pain.clusters.<problema>.monetization` | agencia_viajes, asesor_ai_prod, demo, escuela_conduccion | Cuánto le cuesta el problema al cliente | B | `sales.customer_problems[id=<problema>].monetization` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.recommended_angles` | asesor_ai_prod, demo | Ángulos de venta para el problema | B | `sales.customer_problems[id=<problema>].recommended_angles` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.signals` | agencia_viajes, asesor_ai_prod, demo, escuela_conduccion | Frases que revelan el problema | B | `sales.customer_problems[id=<problema>].signals` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.urgency_levels.alto` | asesor_ai_prod, demo | Mensajes según la urgencia | B | `sales.customer_problems[id=<problema>].urgency_levels.alto` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.pain.clusters.<problema>.urgency_levels.medio` | asesor_ai_prod, demo | Mensajes según la urgencia | B | `sales.customer_problems[id=<problema>].urgency_levels.medio` | mapa por problema → lista con `id` | no | no | — | — |
| `sales.progression_rules.forbid` | asesor_ai_prod, demo | Lo que el asistente no debe hacer | B | `sales.conversation_flow.forbid` | se une con `sales.conversation_flow` | no | no | — | — |
| `sales.progression_rules.required_flow` | todos | Secuencia mínima de la conversación | B | `sales.conversation_flow.required_flow` | se une con `sales.conversation_flow` | no | no | — | — |
| `sales.qualification.detect_offer_fit` | asesor_ai_prod, demo | Comprobar que la oferta encaja con el cliente | B | `sales.qualification.detect_offer_fit` | — | no | no | — | — |
| `sales.solution.framing` | asesor_ai_prod, demo, escuela_conduccion | Argumentos de venta | A | `sales.arguments` | renombrado | modelo | no: el prompt actual no lo usa | — | — |
| `sales.solution.mapping.<problema>` | asesor_ai_prod, demo | Qué parte de la solución atiende cada problema | B | `sales.customer_problems[id=<problema>].solutions` | se une con `sales.pain.clusters`, que usa la misma clave de problema | no | no | — | — |
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
| `config.capabilities.channels` | todos | Canales (lista antigua) | E | ajustes técnicos: `legacy` (misma ruta) | — | no | no | Estructura antigua: el prompt solo la usa si no hay canales de atención ni del sistema, lo que no ocurre en ningún negocio. En asesor_ai_prod contradice a `business_channels` (vacío). | — |
| `config.capabilities.closing_methods.data_collection.enabled` | todos | Cerrar pidiendo datos | A | `capabilities.closing_methods.data_collection` | — | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.closing_methods.human_handoff.enabled` | todos | Pasar a una persona | A | `capabilities.closing_methods.human_handoff` | — | pantalla | sí: prompt (nadie del equipo recibe aviso) | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.closing_methods.link_payment.enabled` | todos | Cerrar enviando el pago | A | `capabilities.closing_methods.payment_link` | renombrado | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.constraints.disallowed_actions` | todos | Canales y acciones que el negocio no ofrece | A | `capabilities.restrictions.disallowed_actions` | renombrado | no | no | — | — |
| `config.capabilities.constraints.disallowed_channels` | todos | Canales y acciones que el negocio no ofrece | A | `capabilities.restrictions.disallowed_channels` | renombrado | no | no | — | — |
| `config.capabilities.data_collection.enabled` | todos | Pedir datos al cliente | A | `capabilities.data_collection.enabled` | — | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.data_collection.fields` | todos | Datos que se piden | A | `capabilities.data_collection.fields` | — | pantalla | sí: prompt | — | `test_closing_and_data_collection_toggles_change_the_prompt` |
| `config.capabilities.system_channels.allowed` | todos | Canales por los que funciona el producto | A | `capabilities.product_channels` | renombrado | no | sí: prompt | — | `test_connected_fields_change_the_prompt` |
| `config.conversation.active_window_minutes` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Ventanas de la conversación | C | ajustes técnicos: `conversation.active_window_minutes` | ajuste técnico, fuera del documento comercial | no | sí: estado y reinicio de la conversación | Parámetro interno: cuándo el motor considera activa o nueva una conversación. | `test_conversation_windows_drive_the_conversation_state` |
| `config.conversation.reset_hours` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Ventanas de la conversación | C | ajustes técnicos: `conversation.reset_hours` | ajuste técnico, fuera del documento comercial | no | sí: estado y reinicio de la conversación | Parámetro interno: cuándo el motor considera activa o nueva una conversación. | `test_conversation_windows_drive_the_conversation_state` |
| `config.features.business_model` | agencia_viajes, asesor_ai_prod, clinic, ecommerce, escuela_conduccion, restaurant, saas, tienda_ropa | Tipo de negocio | B | `features.business_model` | sección `features` | no | sí: prompt (cuándo mostrar precios) | — | `test_connected_fields_change_the_prompt` |
| `config.features.catalog_mode` | todos | Vende opciones tipo catálogo o un servicio o plan | B | `features.catalog_mode` | sección `features` | no | sí: prompt (cuándo mostrar precios) | — | `test_connected_fields_change_the_prompt` |
| `config.features.multi_currency` | todos | Permite manejar más de una moneda | B | `features.multi_currency` | sección `features` | no | no | En agencia_viajes es true con una sola moneda: permitirlo no obliga a usarlo. | — |
| `config.features.multi_plan` | todos | Permite ofrecer varios planes | B | `features.multi_plan` | sección `features` | no | no | En asesor_ai_prod, clinic y saas es true con un solo plan: permitirlo no obliga a usarlo. | — |
| `config.features.pricing_enabled` | todos | Permite usar precios en la conversación | B | `features.pricing_enabled` | sección `features` | no | no | El prompt solo lo consulta si no hay precios ni pagos, algo que el contrato no permite (toda oferta tiene precio). | — |
| `config.flags.ai_first` | todos | Banderas internas (ai_first, allow_fallback, log_level) | C | ajustes técnicos: `flags.ai_first` | ajuste técnico, fuera del documento comercial | no | no | Sin consumidor en el motor; no son decisiones del negocio. | — |
| `config.flags.allow_fallback` | todos | Banderas internas (ai_first, allow_fallback, log_level) | C | ajustes técnicos: `flags.allow_fallback` | ajuste técnico, fuera del documento comercial | no | no | Sin consumidor en el motor; no son decisiones del negocio. | — |
| `config.flags.log_level` | todos | Banderas internas (ai_first, allow_fallback, log_level) | C | ajustes técnicos: `flags.log_level` | ajuste técnico, fuera del documento comercial | no | no | Sin consumidor en el motor; no son decisiones del negocio. | — |
| `config.initial_message.enabled` | todos | Mensaje de bienvenida activo | A | `messages.welcome.enabled` | — | pantalla | sí: primer mensaje | — | `test_welcome_message_toggle` |
| `config.initial_message.recency.active_minutes` | demo | Ventanas del mensaje inicial (antiguas) | E | ajustes técnicos: `legacy` (misma ruta) | — | no | no | Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h). | — |
| `config.initial_message.recency.reset_hours` | demo | Ventanas del mensaje inicial (antiguas) | E | ajustes técnicos: `legacy` (misma ruta) | — | no | no | Solo demo: ubicación antigua de las ventanas de conversación, con los mismos valores por defecto del motor (15 min, 4 h). | — |
| `config.initial_message.text` | todos | Texto de bienvenida | A | `messages.welcome.text` | — | pantalla | sí: primer mensaje | — | `test_welcome_message_toggle` |
| `config.post_payment.on_payment_confirmed.message` | todos | Mensaje de pago confirmado | A | `messages.payment_confirmed` | renombrado | pantalla | sí: prompt post-pago | — | `test_connected_fields_change_the_prompt` |
| `config.post_payment.on_user_report.message` | todos | Respuesta al reportar un pago | A | `messages.payment_reported` | renombrado | pantalla | sí: respuesta exacta | — | `test_payment_report_message_is_optional` |
| `config.response.length` | todos | Largo de las respuestas | A | `response_style.length` | — | pantalla | sí: prompt y recorte | — | `test_each_response_length_option_controls_prompt_and_truncation` |
| `config.response.max_words` | todos | Límite avanzado de palabras | B | `response_style.max_words` | — | modelo | sí: prompt y recorte | — | `test_changing_the_contract_changes_response_length` |

## Referencia de campos del contrato

Generada del JSON Schema (`x-audience`, `x-engine`). Cada campo hoja del contrato, con quién lo configura,
si el motor actual lo usa y de dónde viene.

- **Audiencia:** `cliente` (lo configura el negocio), `avanzado` (estrategia comercial detallada, opcional)
  o `sistema`.
- **Motor:** `conectado` (el motor actual lo usa; prueba en `tests/test_business_config_engine_integration.py`)
  o `pendiente` (representado y conservado, sin uso en el motor actual).
- **Origen:** campo de los YAML, `nuevo` (solo existe en el contrato) o `derivado` (lo crea la importación).

| Audiencia | Conectados | Pendientes |
|---|---|---|
| cliente | 49 | 85 |
| avanzado | 7 | 44 |
| sistema | 2 | 0 |
| **Total** | 58 | 129 |

| Campo | Audiencia | Motor | Origen | Interfaz | Descripción |
|---|---|---|---|---|---|
| `capabilities.actions_primary` | cliente | conectado | `config.capabilities.actions.primary` | pantalla | Acciones de venta. |
| `capabilities.actions_support` | cliente | conectado | `config.capabilities.actions.support` | pantalla | Acciones de apoyo. |
| `capabilities.closing_methods.data_collection` | cliente | conectado | `config.capabilities.closing_methods.data_collection.enabled` | pantalla | Cerrar pidiendo datos |
| `capabilities.closing_methods.human_handoff` | cliente | conectado | `config.capabilities.closing_methods.human_handoff.enabled` | pantalla | Pasar a una persona |
| `capabilities.closing_methods.payment_link` | cliente | conectado | `config.capabilities.closing_methods.link_payment.enabled` | pantalla | Cerrar enviando el pago |
| `capabilities.data_collection.enabled` | cliente | conectado | `config.capabilities.data_collection.enabled` | pantalla | Pedir datos al cliente |
| `capabilities.data_collection.fields` | cliente | conectado | `config.capabilities.data_collection.fields` | pantalla | Datos que el asistente puede pedir al cliente; solo esos. |
| `capabilities.product_channels` | cliente | conectado | `config.capabilities.system_channels.allowed` | no | Canales por los que funciona el producto que se vende. |
| `capabilities.restrictions.disallowed_actions` | cliente | pendiente | `config.capabilities.constraints.**` | no | Acciones que el negocio no realiza (p. ej. llamadas). |
| `capabilities.restrictions.disallowed_channels` | cliente | pendiente | `config.capabilities.constraints.**` | no | Canales por los que el negocio no atiende. |
| `capabilities.service_channels` | cliente | conectado | `config.capabilities.business_channels.allowed` | pantalla | Canales de atención al cliente. |
| `features.business_model` | avanzado | conectado | `config.features.business_model` | no | Tipo de negocio; con él el motor decide cuándo mostrar precios. |
| `features.catalog_mode` | avanzado | conectado | `config.features.catalog_mode` | no | true: vende opciones tipo catálogo. false: vende un servicio o plan. |
| `features.multi_currency` | avanzado | pendiente | `config.features.multi_currency` | no | true: permite manejar más de una moneda. |
| `features.multi_plan` | avanzado | pendiente | `config.features.multi_plan` | no | true: permite ofrecer varios planes. |
| `features.pricing_enabled` | avanzado | pendiente | `config.features.pricing_enabled` | no | true: permite usar precios en la conversación. |
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
| `identity.brand_name` | cliente | pendiente | `business.brand_name` | no | Marca con la que el asistente presenta al negocio, si es distinta del nombre. |
| `identity.credibility` | cliente | pendiente | `business.credibility` | no | Pruebas de confianza: casos, resultados, trayectoria. |
| `identity.description` | cliente | pendiente | `business.description` | pantalla | Qué hace el negocio. |
| `identity.differentiators` | cliente | pendiente | `business.differentiators` | modelo | Por qué elegir este negocio y no otro. |
| `identity.industry` | cliente | conectado | `business.industry` | pantalla | Sector o tipo de negocio, en pocas palabras. |
| `identity.location.address` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.city` | cliente | pendiente | `business.city`, `business.location.**` | modelo/no | Ciudad |
| `identity.location.coverage.type` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.coverage.zones` | cliente | pendiente | `business.location.**` | modelo | Ubicación y cobertura |
| `identity.location.type` | cliente | pendiente | `business.location.**` | modelo | virtual, fisico (local propio) o mixto. |
| `identity.name` | cliente | pendiente | `business.name` | pantalla | Nombre del negocio. |
| `identity.opening_hours[].closes` | cliente | pendiente | nuevo | no | Hora de cierre (HH:MM, 24 h). |
| `identity.opening_hours[].days` | cliente | pendiente | nuevo | no | Días en los que aplica este horario. |
| `identity.opening_hours[].opens` | cliente | pendiente | nuevo | no | Hora de apertura (HH:MM, 24 h). |
| `identity.positioning` | cliente | pendiente | `business.positioning` | no | A quién se dirige y qué problema resuelve. |
| `identity.service_modes` | cliente | pendiente | `business.service_modes` | modelo | Cómo recibe el cliente el servicio o producto. |
| `identity.target_customer.company_size` | cliente | pendiente | `business.customer_profile.**` | no | Cliente ideal |
| `identity.target_customer.maturity` | cliente | pendiente | `business.customer_profile.**` | no | Situación típica del cliente al llegar. |
| `identity.target_customer.roles` | cliente | pendiente | `business.customer_profile.**` | no | Quién suele escribir o decidir la compra. |
| `identity.target_customer.segment` | cliente | pendiente | `business.customer_profile.**` | no | Tipo de cliente al que se dirige el negocio. |
| `identity.value_proposition` | cliente | conectado | `business.promise` | pantalla | Promesa comercial: qué gana el cliente. |
| `inventory.items[].product_id` | cliente | pendiente | `inventory.items[].**` | no | Id de un producto del catálogo. |
| `inventory.items[].variants[].attributes` | cliente | pendiente | `inventory.items[].**` | no | Talla, color u otras características. |
| `inventory.items[].variants[].prices[].amount` | cliente | pendiente | nuevo | no | Precio en esa moneda. |
| `inventory.items[].variants[].prices[].currency` | cliente | pendiente | nuevo | no | Moneda (código ISO de tres letras). |
| `inventory.items[].variants[].sku` | cliente | pendiente | `inventory.items[].**` | no | Producto con variantes y existencias |
| `inventory.items[].variants[].stock` | cliente | pendiente | `inventory.items[].**` | no | Producto con variantes y existencias |
| `inventory.track_stock` | cliente | pendiente | `inventory.track_stock` | no | Si el negocio controla existencias. |
| `knowledge.faqs[].answer` | cliente | pendiente | nuevo | pantalla | Respuesta oficial del negocio. |
| `knowledge.faqs[].question` | cliente | pendiente | nuevo | pantalla | Pregunta tal como la haría el cliente. |
| `messages.after_sale` | cliente | pendiente | nuevo | no | Mensaje después de una compra. |
| `messages.data_request` | cliente | pendiente | nuevo | no | Mensaje para pedir los datos del cliente. |
| `messages.follow_up` | cliente | pendiente | nuevo | no | Mensaje de seguimiento a un cliente que no respondió. |
| `messages.human_handoff` | cliente | pendiente | nuevo | no | Mensaje al pasar la conversación a una persona. |
| `messages.payment_confirmed` | cliente | conectado | `config.post_payment.on_payment_confirmed.message` | pantalla | Mensaje cuando el pago queda confirmado. |
| `messages.payment_reported` | cliente | conectado | `config.post_payment.on_user_report.message` | pantalla | Respuesta exacta cuando el cliente reporta un pago. |
| `messages.welcome.enabled` | cliente | conectado | `config.initial_message.enabled` | pantalla | true: envía el mensaje inicial fijo, sin IA. false: no lo envía y responde la IA. |
| `messages.welcome.text` | cliente | conectado | `config.initial_message.text` | pantalla | Mensaje de apertura que recibe el cliente. |
| `offer.catalog.categories[].id` | cliente | conectado | `pricing.catalog.categories[].id` | pantalla | Identificador de la categoría |
| `offer.catalog.categories[].name` | cliente | conectado | `pricing.catalog.categories[].name` | pantalla | Nombre de la categoría |
| `offer.catalog.items[].available` | cliente | conectado | nuevo | pantalla | Si es false, el producto se conserva pero no se ofrece (ni su categoría, si se queda sin productos). |
| `offer.catalog.items[].category` | cliente | conectado | `pricing.catalog.items[].category` | pantalla | Id de su categoría; una categoría sin productos disponibles no se ofrece. |
| `offer.catalog.items[].description` | cliente | pendiente | `pricing.catalog.items[].description` | pantalla | Detalle del producto. |
| `offer.catalog.items[].features` | cliente | pendiente | nuevo | pantalla | Características del producto. |
| `offer.catalog.items[].id` | cliente | pendiente | `pricing.catalog.items[].id` | pantalla | Identificador estable del producto |
| `offer.catalog.items[].name` | cliente | pendiente | `pricing.catalog.items[].name` | pantalla | Nombre del producto |
| `offer.catalog.items[].prices[].amount` | cliente | pendiente | `pricing.catalog.items[].price.<moneda>` | pantalla | Precio en esa moneda. |
| `offer.catalog.items[].prices[].currency` | cliente | pendiente | derivado | — | Moneda (código ISO de tres letras). |
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
| `offer.plans[].prices[].first_payment` | cliente | conectado | nuevo | no | Valor del primer pago, si difiere de los siguientes. |
| `offer.plans[].prices[].implementation` | cliente | conectado | `pricing.plans[].pricing.<moneda>.**` | pantalla | Pago único inicial (instalación, implementación, inscripción). |
| `offer.plans[].prices[].monthly` | cliente | conectado | `pricing.plans[].pricing.<moneda>.**` | pantalla | Cobro mensual. |
| `offer.plans[].prices[].price` | cliente | conectado | nuevo | pantalla | Precio de pago único. |
| `offer.plans[].target` | cliente | pendiente | `pricing.plans[].target` | no | Para quién es este plan. |
| `payments[].id` | cliente | conectado | derivado | — | Perfil de pago creado por la importación (id del plan o `catalog`) |
| `payments[].link` | cliente | conectado | `pricing.catalog.payment.link`, `pricing.plans[].payment.link` | pantalla | Link de pago del catálogo |
| `payments[].link_enabled` | cliente | conectado | nuevo | pantalla | Si es false, el enlace se conserva pero no se ofrece. |
| `payments[].transfer_enabled` | cliente | conectado | `pricing.catalog.payment.transfer.enabled`, `pricing.plans[].payment.transfer.enabled` | pantalla | Transferencias activas |
| `payments[].transfer_methods[].account_number` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].account_number`, `pricing.plans[].payment.transfer.methods[].account_number` | pantalla | Número de cuenta |
| `payments[].transfer_methods[].account_type` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].account_type`, `pricing.plans[].payment.transfer.methods[].account_type` | pantalla | Tipo de cuenta |
| `payments[].transfer_methods[].bank` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].bank`, `pricing.plans[].payment.transfer.methods[].bank` | pantalla | Banco |
| `payments[].transfer_methods[].enabled` | cliente | conectado | nuevo | pantalla | Si es false, la cuenta se conserva pero no se ofrece. |
| `payments[].transfer_methods[].label` | cliente | pendiente | nuevo | pantalla | Titular o etiqueta para reconocer la cuenta en el panel. No se comparte con el cliente. |
| `payments[].transfer_methods[].number` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].number`, `pricing.plans[].payment.transfer.methods[].number` | pantalla | Celular Nequi o Daviplata |
| `payments[].transfer_methods[].reference` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].reference`, `pricing.plans[].payment.transfer.methods[].reference` | pantalla | Llave o referencia Bre-B |
| `payments[].transfer_methods[].type` | cliente | conectado | `pricing.catalog.payment.transfer.methods[].type`, `pricing.plans[].payment.transfer.methods[].type` | pantalla | Método de transferencia |
| `response_style.emojis` | cliente | pendiente | nuevo | no | Si el asistente puede usar emojis. |
| `response_style.formality` | cliente | pendiente | nuevo | no | informal (tutea), neutral o formal (usted). |
| `response_style.instructions` | cliente | pendiente | nuevo | no | Cómo debe expresarse el asistente en este negocio. |
| `response_style.length` | cliente | conectado | `config.response.length` | pantalla | short (cortas), medium (equilibradas) o long (detalladas). |
| `response_style.max_words` | avanzado | conectado | `config.response.max_words` | modelo | Ajuste dentro del rango de la opción elegida. Si falta, el límite de la opción. |
| `response_style.tone` | cliente | pendiente | `business.tone` | modelo | Tono del asistente (p. ej. cercano y claro). |
| `response_style.voice` | cliente | pendiente | `business.voice` | no | Personalidad de la marca. |
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
| `sales.closing.strategy` | avanzado | pendiente | `sales.closing.strategy` | no | Tipo de cierre: direct_sale (confirmar la compra), lead_capture (capturar datos), booking (agendar) o checkout (enviar el pago). |
| `sales.conversation_flow.forbid` | avanzado | pendiente | `sales.progression_rules.forbid` | no | Lo que el asistente no debe hacer en este negocio (p. ej. responder_sin_solucion). |
| `sales.conversation_flow.guided_process` | avanzado | pendiente | `sales.conversation_flow.rules.guided_process` | no | true: guía al cliente paso a paso en un proceso (trámites, matrículas). |
| `sales.conversation_flow.no_skip_steps` | avanzado | pendiente | `sales.conversation_flow.rules.no_skip_steps` | no | true: no se saltan pasos de la conversación. |
| `sales.conversation_flow.required_flow` | avanzado | pendiente | `sales.progression_rules.required_flow` | no | Secuencia mínima que debe respetar la conversación. |
| `sales.conversation_flow.steps` | avanzado | pendiente | `sales.conversation_flow.steps` | no | Pasos que idealmente sigue la conversación, en orden. |
| `sales.customer_problems[].id` | cliente | conectado | derivado | — | Clave del problema en `sales.pain.clusters` |
| `sales.customer_problems[].impacts` | cliente | conectado | `sales.pain.clusters.<problema>.impacts` | pantalla | Qué le causa el problema al cliente. |
| `sales.customer_problems[].monetization` | avanzado | pendiente | `sales.pain.clusters.<problema>.monetization` | no | Cómo el problema le cuesta dinero al cliente. |
| `sales.customer_problems[].recommended_angles` | avanzado | pendiente | `sales.pain.clusters.<problema>.recommended_angles` | no | Ángulos de venta para este problema. |
| `sales.customer_problems[].signals` | avanzado | pendiente | `sales.pain.clusters.<problema>.signals` | no | Frases del cliente que revelan el problema. |
| `sales.customer_problems[].solutions` | avanzado | pendiente | `sales.solution.mapping.<problema>` | no | Qué parte de la solución atiende este problema. |
| `sales.customer_problems[].urgency_levels` | avanzado | pendiente | `sales.pain.clusters.<problema>.urgency_levels.**` | no | Mensajes según la urgencia. |
| `sales.discovery.objectives` | avanzado | pendiente | `sales.discovery.objectives` | no | Qué debe averiguar el asistente. |
| `sales.discovery.questions` | cliente | pendiente | `sales.discovery.questions` | modelo | Preguntas para entender al cliente. |
| `sales.instructions` | cliente | pendiente | nuevo | modelo | Cómo debe vender el asistente en este negocio. |
| `sales.motivations[].angle.messages` | avanzado | pendiente | `sales.angles.<motivo>.execution` | no | Qué decir con este ángulo. |
| `sales.motivations[].angle.signals` | avanzado | pendiente | `sales.angles.<motivo>.when` | no | Cuándo usar el ángulo: frases del cliente. |
| `sales.motivations[].description` | avanzado | pendiente | `business.value_drivers.<motivo>.description` | no | Qué significa este motivo para el cliente. |
| `sales.motivations[].motivation` | avanzado | pendiente | derivado | — | Motivo de compra (p. ej. tiempo, dinero). |
| `sales.motivations[].signals` | avanzado | pendiente | `business.value_drivers.<motivo>.triggers` | no | Frases del cliente que revelan este motivo. |
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
| `sales.qualification.detect_offer_fit` | avanzado | pendiente | `sales.qualification.detect_offer_fit` | no | true: valida si la oferta encaja antes de empujar el cierre. |
| `sales.recommendation_rules[].recommend` | cliente | pendiente | `sales.offer.recommendation_rules[].recommend` | no | Plan, producto o categoría que se recomienda. Si no está en la oferta, el diagnóstico lo señala. |
| `sales.recommendation_rules[].when` | cliente | pendiente | `sales.offer.recommendation_rules[].condition` | no | Situación o necesidad del cliente. |
| `sales.solution.process_steps` | cliente | pendiente | `sales.solution.process_steps` | no | Pasos que sigue el cliente para comprar o recibir el servicio. |
| `sales.solution.requirements` | cliente | pendiente | `sales.solution.requirements` | no | Requisitos que debe cumplir el cliente. |
| `sales.support.explain_first` | avanzado | pendiente | `sales.support.info_handling.explain_first` | no | true: primero aclara la duda. false: vende directo. |
| `sales.support.rules` | avanzado | pendiente | `sales.support.hard_rules` | no | Reglas de atención del negocio. |
| `sales.support.sell_after` | avanzado | pendiente | `sales.support.info_handling.sell_after` | no | true: después de explicar, vuelve a llevar al cliente a avanzar. |
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
| `terms.promotions[].details` | cliente | pendiente | nuevo | modelo | Qué incluye la promoción y a qué aplica. |
| `terms.promotions[].name` | cliente | pendiente | nuevo | modelo | Nombre con el que se presenta la promoción. |
| `terms.promotions[].valid_until` | cliente | pendiente | nuevo | modelo | Último día de vigencia. |
| `terms.roi_break_even_bookings` | avanzado | pendiente | `pricing.roi.break_even_reservas` | no | Reservas con las que el cliente recupera la inversión. |
| `terms.roi_break_even_sales` | avanzado | conectado | `pricing.roi.break_even_sales` | no | Ventas al mes con las que el cliente recupera la inversión. |
| `terms.roi_hints` | avanzado | conectado | `pricing.roi_hints` | no | Argumentos de retorno de la inversión. |

## Campos del contrato que crea la importación

Se derivan de claves o de la estructura de los YAML, no de un valor concreto.

| Campo | Origen |
|---|---|
| `offer.catalog.items[].prices[].currency` | Clave de moneda en `pricing.catalog.items[].price` |
| `offer.catalog.payment_profile` | Enlace del catálogo con su perfil de pago |
| `offer.plans[].payment_profile` | Enlace del plan con su perfil de pago |
| `offer.plans[].prices[].currency` | Clave de moneda en `pricing.plans[].pricing` |
| `payments[].id` | Perfil de pago creado por la importación (id del plan o `catalog`) |
| `sales.customer_problems[].id` | Clave del problema en `sales.pain.clusters` |
| `sales.motivations[].motivation` | Clave del motivo en `business.value_drivers` y `sales.angles` |
| `sales.objections[].topic` | Clave de la objeción en `sales.objection` |
| `schema_version` | Versión del contrato |
| `tenant_slug` | Negocio dueño del documento |
