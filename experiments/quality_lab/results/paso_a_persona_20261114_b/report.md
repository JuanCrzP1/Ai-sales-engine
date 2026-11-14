# Estándar del asesor: paso_a_persona_20261114_b

**NO PASA** · código `42e7a19 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ❌ pasa al equipo cuando debe (exacta) | 18 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 22 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 23 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ❌ sigue las reglas para pasar (juez) | 19 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |

Gasto de la corrida: asesor USD 0.0361 · juez USD 0.0113. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 3.

## Lo que no pasó

- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con el equipo para que te ayuden. ¿Qué necesitas saber?»
- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 3: debía pasar al equipo y no pasó
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con una persona del equipo que podrá ayudarte mejor. Un momento, por favor.»
- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Voy a pasarte con una persona del equipo para que te ayude. ¿Qué necesitas?»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 3: debía pasar al equipo y no pasó
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Claro, te paso con el equipo para que te ayuden.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 3: debía pasar al equipo y no pasó
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Claro, te paso con una persona del equipo. ¿Qué necesitas?»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 3: debía pasar al equipo y no pasó
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · pide una persona y luego insiste · turno 3: repitió la respuesta anterior
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Te paso con una persona del equipo que podrá ayudarte mejor. Un momento, por favor.»
- **no repite la respuesta** · asesor_ai_prod · pide una persona y luego insiste · turno 3: repitió la respuesta anterior
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.»
- **explica cuando no entienden** · restaurant · la conversación se estanca · turno 3: No explica, solo repite que no entiende y pregunta qué no está claro.
  - Cliente: «Sigo sin entender, ya te lo pregunté y no me ayudas»
  - Asesor: «Entiendo que hay confusión. Estoy aquí para ayudarte. ¿Qué parte no está clara? Quiero asegurarme de que puedas hacer tu pedido sin problemas.»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero antes de pasar el chat.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con el equipo para que te ayuden. ¿Qué necesitas saber?»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero antes de pasar el chat.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con una persona del equipo que podrá ayudarte mejor. Un momento, por favor.»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero antes de pasar el chat.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.»
- **sigue las reglas para pasar** · restaurant · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero antes de pasar el chat.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Claro, te paso con el equipo para que te ayuden.»
- **sigue las reglas para pasar** · restaurant · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero antes de pasar el chat.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Claro, te paso con una persona del equipo. ¿Qué necesitas?»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (incluye la implementación) y luego COP 110.000 cada mes. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con el equipo para que te ayuden. ¿Qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Con este plan podrás automatizar respuestas y hacer seguimiento a tus clientes. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con el equipo para que puedan aclararte todo sobre reembolsos. ¿Te gustaría que lo hiciera ahora?

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Entiendo que busques un descuento, pero no tenemos promociones en este momento. Lo importante es que con solo 3 ventas al mes recuperas lo que pagas. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta 210.000 COP y luego 110.000 COP mensuales. Para continuar, necesito tu nombre, teléfono y detalles. ¿Te gustaría que te envíe los datos de pago ahora?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, a veces puede ser confuso. El Plan Básico te ayuda a responder mensajes y hacer seguimiento automáticamente. El primer mes cuesta 210.000 COP y luego 110.000 COP cada mes. ¿Hay algo específico que te gustaría aclarar sobre el plan?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Permíteme pasar tu consulta al equipo, ellos podrán ayudarte mejor. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración. Voy a pasar tu caso al equipo para que te ayuden directamente. Un momento, por favor.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer pago mensual) y luego COP 110.000 mensualmente. Este plan te ayudará a automatizar las respuestas y mantener el seguimiento con tus clientes. Para continuar, necesitaría tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con una persona del equipo que podrá ayudarte mejor. Un momento, por favor.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con una persona del equipo que podrá ayudarte mejor. Un momento, por favor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu nombre, teléfono y detalles para continuar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te voy a pasar con el equipo para que te aclaren todo sobre el reembolso y las políticas. Un momento.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el sistema mensual. Luego, pagarás COP 110.000 cada mes. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Entiendo tu duda, pero no ofrecemos descuentos ni promociones en este momento. Lo que suele salir caro es perder conversaciones que ya estaban interesadas. Con solo 3 ventas al mes, recuperas lo que pagas. ¿Avanzamos con la activación del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me podrías dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, puedo explicarlo de forma más sencilla. El Plan Básico te ayuda a responder mensajes y hacer seguimiento a tus clientes automáticamente. Así, no pierdes ventas por no responder a tiempo. ¿Te gustaría que te cuente más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no haya quedado claro. Voy a pasar tu consulta al equipo para que te ayuden mejor. ¿Hay algo específico que te gustaría saber?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no hayas recibido la información clara que necesitas. Voy a pasar esto al equipo para que te ayuden con tus dudas. ¿Algo más que quieras comentar?

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico cuesta COP 210.000 en el primer mes, que incluye la configuración inicial y el sistema mensual. Después, pagas COP 110.000 al mes. Para continuar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar, Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con el equipo para que te ayuden con el tema del reembolso. Ellos podrán darte toda la información necesaria.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (que incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me podrías dar tu nombre, teléfono y los detalles para proceder?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Te entiendo, es una inversión importante. Pero lo que suele salir caro es perder conversaciones que ya estaban interesadas. Cuando empiezas a recuperar leads, se paga solo. ¿Avanzamos con la activación del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me podrías dar tu nombre, teléfono y detalles para comenzar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, déjame explicarlo mejor. El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el primer mes del servicio. Luego, cada mes se paga COP 110.000. ¿Hay alguna parte específica que no te quede clara?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Voy a pasarlo con el equipo para que te ayuden mejor. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés recibiendo la ayuda que necesitas. Te voy a pasar con el equipo para que puedan aclarar tus dudas de manera más efectiva.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Voy a pasarte con una persona del equipo para que te ayude. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu inquietud, pero para temas de reembolsos y devoluciones, te paso con el equipo para que te ayuden mejor. ¿Te gustaría que lo haga?

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Pero nuestras hamburguesas son artesanales y recién hechas, ¡perfectas para disfrutar! ¿Te gustaría pedir la Hamburguesa Sencilla con alguna bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Lo siento si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. Además, puedes sumar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o agregar una bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. ¿Qué parte te gustaría que explicara mejor? Estoy aquí para ayudarte.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración. Te pasaré con el equipo para que puedan ayudarte mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, te paso con el equipo para que te ayuden.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas te gustaría pedir?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, te voy a pasar con el equipo. Ellos podrán ayudarte mejor con eso.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Pero la Hamburguesa Sencilla es una excelente opción. ¿Te gustaría pedirla con alguna bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Lo siento si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa a COP 5.000 o jugo natural a COP 7.000. ¿Te gustaría hacer un pedido?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo que esto puede ser confuso. Estoy aquí para ayudarte. ¿Qué parte no está clara? ¿Te gustaría que te explique nuevamente las opciones de la hamburguesa y las bebidas?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés satisfecho. Te voy a pasar con el equipo para que puedan ayudarte mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, te paso con una persona del equipo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, lo mejor es que te pase con el equipo para que te ayuden. ¿Te gustaría que lo hiciera?

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Pero la Hamburguesa Sencilla es una excelente opción. ¿Te gustaría pedirla con una gaseosa o un jugo natural?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, disculpa si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o prefieres alguna bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo que hay confusión. Estoy aquí para ayudarte. ¿Qué parte no está clara? Quiero asegurarme de que puedas hacer tu pedido sin problemas.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés recibiendo la ayuda que necesitas. Voy a pasar tu solicitud a un miembro del equipo para que te ayude mejor.
