# Estándar del asesor: paso_a_persona_20261114

**NO PASA** · código `42e7a19 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ❌ pasa al equipo cuando debe (exacta) | 18 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 23 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 21 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ❌ sigue las reglas para pasar (juez) | 19 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |

Gasto de la corrida: asesor USD 0.0357 · juez USD 0.0124. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 5.

## Lo que no pasó

- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Claro, te paso con el equipo ahora mismo para que te ayuden.»
- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te puedo ayudar con eso, pero si prefieres hablar con alguien del equipo, puedo pasarte con ellos. ¿Te gustaría que lo haga?»
- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Voy a pasarte con alguien de nuestro equipo que podrá ayudarte con lo que necesitas.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Entiendo, te paso con el equipo para que te ayuden.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Puedo ayudarte con lo que necesites, pero si prefieres, te paso con alguien del equipo. ¿Qué te gustaría resolver?»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Claro, te paso con una persona del equipo que podrá ayudarte.»
- **no repite la respuesta** · asesor_ai_prod · pide una persona y luego insiste · turno 3: repitió la respuesta anterior
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Voy a pasarte con alguien de nuestro equipo que podrá ayudarte con lo que necesitas.»
- **explica cuando no entienden** · asesor_ai_prod · la conversación se estanca · turno 3: El cliente dice que no entiende y el asesor no explica.
  - Cliente: «Sigo sin entender, ya te lo pregunté y no me ayudas»
  - Asesor: «Lamento que no esté claro. Te paso con el equipo para que te ayuden mejor con esto.»
- **explica cuando no entienden** · restaurant · la conversación se estanca · turno 3: El cliente dice que no entiende y el asesor repite lo mismo.
  - Cliente: «Sigo sin entender, ya te lo pregunté y no me ayudas»
  - Asesor: «Lamento la confusión. Estoy aquí para ayudarte. La Hamburguesa Sencilla cuesta COP 18.000 y puedes agregar una bebida. ¿Te gustaría pedir solo la hamburguesa o prefieres incluir una gaseosa o un jugo?»
- **explica cuando no entienden** · restaurant · la conversación se estanca · turno 3: No explica, solo pregunta qué no entiende el cliente.
  - Cliente: «Sigo sin entender, ya te lo pregunté y no me ayudas»
  - Asesor: «Lamento que no esté claro. Estoy aquí para ayudarte. ¿Podrías decirme qué parte no entiendes para explicarte mejor?»
- **sigue las reglas para pasar** · asesor_ai_prod · pregunta por un tema del equipo · turno 2: El tema 'reembolsos' es 'always_topics', no debe intentar resolverlo.
  - Cliente: «Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?»
  - Asesor: «Entiendo tu preocupación, pero no manejamos reembolsos. Si tienes dudas sobre el servicio, puedo pasarte con el equipo para que te aclaren todo. ¿Te gustaría que lo hiciera?»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero antes de pasar al equipo.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Voy a pasarte con alguien de nuestro equipo que podrá ayudarte con lo que necesitas.»
- **sigue las reglas para pasar** · restaurant · pregunta por un tema del equipo · turno 2: El tema de reembolsos es always_topics, no debe ofrecer ayuda.
  - Cliente: «Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?»
  - Asesor: «Entiendo tu preocupación, pero el tema de reembolsos y devoluciones lo maneja el equipo. Te puedo ayudar a hacer tu pedido o resolver cualquier otra duda que tengas.»
- **sigue las reglas para pasar** · restaurant · la conversación se estanca · turno 4: El cliente no pidió ser pasado a un agente.
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Entiendo tu frustración. Voy a pasar tu consulta al equipo para que te ayuden mejor. Un momento, por favor.»
- **sigue las reglas para pasar** · restaurant · la conversación se estanca · turno 4: No ofrece ayuda primero antes de pasar al equipo.
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Entiendo tu frustración y lamento que no haya sido claro. Voy a pasar tu consulta a un miembro del equipo para que te ayude mejor.»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y el medio de pago que prefieres.

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, te paso con el equipo ahora mismo para que te ayuden.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te entiendo, te paso con el equipo para que te atiendan.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y número de teléfono para avanzar con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con el equipo para que te aclaren el tema de reembolsos y devoluciones. Ellos podrán darte toda la información que necesitas.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes (COP 100.000 de implementación + COP 110.000 al mes). Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para proceder?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No ofrecemos descuentos ni promociones en este momento. Sin embargo, lo que suele salir caro es perder conversaciones que ya estaban interesadas. ¿Te gustaría avanzar con la activación del Plan Básico para empezar a recuperar esas oportunidades?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos paso a paso. El Plan Básico te ayuda a automatizar respuestas y hacer seguimiento a los clientes que contactas por WhatsApp. Así no pierdes ventas por demoras. ¿Qué parte te gustaría que te explique mejor?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Te paso con el equipo para que te ayuden mejor con esto.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no hayamos podido aclarar tus dudas. Voy a pasar tu caso al equipo para que te den la atención que necesitas.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te puedo ayudar con eso, pero si prefieres hablar con alguien del equipo, puedo pasarte con ellos. ¿Te gustaría que lo haga?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con el equipo para que te atiendan. Ellos te ayudarán con lo que necesites.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el sistema mensual. Después, pagas COP 110.000 mensualmente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero no manejamos reembolsos. Si tienes dudas sobre el servicio, puedo pasarte con el equipo para que te aclaren todo. ¿Te gustaría que lo hiciera?

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, la guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. El Plan Básico es una buena inversión, ya que con solo 3 ventas al mes recuperas lo que pagas. ¿Te gustaría avanzar con la activación?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Esto te ayudará a automatizar respuestas y hacer seguimiento a tus clientes. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, déjame explicarte mejor. El Plan Básico te ayuda a responder automáticamente a tus clientes y a hacer seguimiento de las conversaciones, para que no pierdas ventas. La implementación cuesta COP 100.000 y luego pagas COP 110.000 cada mes. ¿Te gustaría que te enviara más información sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Voy a pasar tu consulta al equipo para que te ayuden mejor con esto. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido útil. Voy a pasar tu caso al equipo para que puedan darte la atención que necesitas. Un momento, por favor.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes y luego COP 110.000 mensuales. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Voy a pasarte con alguien de nuestro equipo que podrá ayudarte con lo que necesitas.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Voy a pasarte con alguien de nuestro equipo que podrá ayudarte con lo que necesitas.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te comento que cualquier tema de reembolsos lo maneja el equipo, así que te paso con ellos para que te den toda la información que necesitas.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Podrías darme tu nombre y teléfono para continuar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No ofrecemos descuentos ni promociones en este momento. Sin embargo, lo que suele salir caro es perder conversaciones que ya estaban interesadas. ¿Te gustaría avanzar con el Plan Básico para empezar a recuperar esas oportunidades?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos a aclararlo. El Plan Básico tiene un costo inicial de COP 210.000 que incluye la configuración y el primer mes de servicio. Después, pagas COP 110.000 mensualmente. ¿Te gustaría que te explique cómo te puede ayudar este plan a responder más rápido y hacer seguimiento a tus clientes?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no haya quedado claro. Te lo explico de otra manera. El Plan Básico te permite automatizar respuestas en WhatsApp, así puedes responder a tus clientes sin estar pendiente todo el tiempo. Así evitas perder ventas porque no alcanzas a responder. ¿Te gustaría que pase este tema a alguien del equipo para que te ayude mejor?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no esté siendo útil. Te pasaré con el equipo para que puedan ayudarte mejor con tus dudas.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Entiendo, te paso con el equipo para que te ayuden.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con el equipo para que te atiendan directamente.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero el tema de reembolsos y devoluciones lo maneja el equipo. Te puedo ayudar a hacer tu pedido o resolver cualquier otra duda que tengas.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Sin embargo, la Hamburguesa Sencilla es una opción deliciosa. ¿Te gustaría pedirla con una bebida para hacer tu pedido más completo?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Disculpa si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. Puedes pedirla sola o agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000. ¿Te gustaría agregar alguna bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento la confusión. Estoy aquí para ayudarte. La Hamburguesa Sencilla cuesta COP 18.000 y puedes agregar una bebida. ¿Te gustaría pedir solo la hamburguesa o prefieres incluir una gaseosa o un jugo?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no esté siendo claro. Voy a pasar tu consulta al equipo para que te ayuden mejor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Puedo ayudarte con lo que necesites, pero si prefieres, te paso con alguien del equipo. ¿Qué te gustaría resolver?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con un miembro del equipo para que te atienda. ¡Un momento, por favor!

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Cuántas Hamburguesas Sencillas te gustaría pedir?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero el tema de reembolsos lo maneja el equipo. Puedo pasarte con ellos para que te den más información.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Pero la Hamburguesa Sencilla es una opción deliciosa. ¿Te gustaría pedirla con una gaseosa o un jugo natural?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir la hamburguesa sola o con alguna bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que estés teniendo dificultades. Estoy aquí para ayudarte. ¿Te gustaría que te explique de nuevo los precios o cómo funciona el pedido?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración. Voy a pasar tu consulta al equipo para que te ayuden mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, te paso con una persona del equipo que podrá ayudarte.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Entiendo, te paso con una persona del equipo que podrá ayudarte.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría agregar una gaseosa a tu pedido por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero el tema de reembolsos lo maneja el equipo. Te puedo pasar con ellos para que te den más información. ¿Te gustaría que lo hiciera?

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Sin embargo, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría seguir adelante con el pedido?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Disculpa si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. Puedes agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o también una bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Estoy aquí para ayudarte. ¿Podrías decirme qué parte no entiendes para explicarte mejor?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Voy a pasar tu consulta a un miembro del equipo para que te ayude mejor.
