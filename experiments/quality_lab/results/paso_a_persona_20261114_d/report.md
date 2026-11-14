# Estándar del asesor: paso_a_persona_20261114_d

**NO PASA** · código `031a093 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ❌ pasa al equipo cuando debe (exacta) | 23 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 24 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 24 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ❌ sigue las reglas para pasar (juez) | 23 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |

Gasto de la corrida: asesor USD 0.0374 · juez USD 0.0099. Llamadas al modelo por mensaje: 2.02. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 3.

## Lo que no pasó

- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 3: debía pasar al equipo y no pasó
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda primero, no pasar directamente.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 3: Debió pasar el chat después de la segunda solicitud del cliente.
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesitaré tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración y el primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu nombre, teléfono y cómo prefieres pagar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con el equipo para que te ayuden con el tema de reembolsos. Un momento por favor.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Entiendo que busques una opción más económica, pero en este momento no tenemos descuentos ni promociones. Lo importante es que este plan te ayudará a recuperar conversaciones y ventas que podrías estar perdiendo. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración inicial y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y un correo para proceder con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos paso a paso. El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración y el sistema. Luego, cada mes pagas COP 110.000. ¿Te gustaría que te explique más sobre lo que incluye?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no hayamos avanzado. Te paso con alguien del equipo para que te ayuden mejor. Un momento, por favor.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero voy a pasarlo con el equipo para que te puedan ayudar con ese tema. Un momento.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y el medio de pago que prefieres.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Lo que vale la pena considerar es que al recuperar solo 3 ventas al mes, ya recuperas lo que pagas. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para activar el servicio, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, permíteme explicarte de manera más sencilla. El Plan Básico te ayuda a responder mensajes automáticamente y hacer seguimiento a tus clientes, así no pierdes oportunidades de venta. ¿Te gustaría que te explique cómo funciona el proceso de activación?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no estés entendiendo. Voy a pasarte con alguien del equipo que podrá ayudarte mejor. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no hayas recibido la ayuda que necesitabas. Te voy a pasar con alguien del equipo para que te brinde la atención adecuada. Un momento, por favor.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (que incluye la implementación y el primer pago mensual) y luego COP 110.000 mensuales. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu inquietud, pero para temas de reembolsos te paso con alguien del equipo que podrá ayudarte mejor. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 mensual) y luego COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones, pero el valor del Plan Básico se recupera rápidamente con solo 3 ventas al mes. Es una inversión que te ayudará a no perder más oportunidades. ¿Te gustaría que te enviara los datos de pago para avanzar?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000, que incluye la configuración inicial y el primer mes. Luego, se paga mensualmente COP 110.000. Para proceder, necesito tu nombre, teléfono y cómo prefieres realizar el pago.

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, déjame explicarte de otra manera. El Plan Básico cuesta COP 210.000, que cubre la configuración inicial y el primer mes. Luego, seguirías pagando COP 110.000 cada mes. ¿Hay alguna parte en particular que te gustaría que aclarara?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo que no está claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no hayamos podido aclarar tus dudas. Te paso con el equipo para que te ayuden mejor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, mejor te paso con el equipo para que te ayuden. ¿Te gustaría que lo haga?

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa a COP 5.000 o un jugo natural a COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento, pero la Hamburguesa Sencilla es una excelente opción por su calidad. ¿Te gustaría confirmar tu pedido con una bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Lo siento si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o agregar una bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo que estás confundido. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés satisfecho. Te paso con el equipo para que puedan ayudarte mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar algo más, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, te pasaré con el equipo para que puedan ayudarte. Un momento, por favor.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Pero la Hamburguesa Sencilla es una excelente opción a un buen precio. ¿Te gustaría pedirla junto con una bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Disculpa si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. También puedes sumar una bebida: gaseosa a COP 5.000 o jugo natural a COP 7.000. ¿Te gustaría pedir solo la hamburguesa o incluir una bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no estés entendiendo. ¿Podrías decirme qué parte te confunde? Estoy aquí para ayudarte.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés satisfecho. Te voy a pasar con alguien del equipo para que te ayuden mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, ¿qué necesitas? Estoy aquí para ayudarte.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu duda, pero para temas de reembolsos y devoluciones, te paso con alguien del equipo para que te ayude. En un momento te escriben.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa a COP 5.000 o un jugo natural a COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Pero la Hamburguesa Sencilla es una opción deliciosa. ¿Te gustaría pedirla junto con una bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, déjame explicarlo mejor. La Hamburguesa Sencilla cuesta COP 18.000. También puedes elegir una bebida, como gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o agregar una bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento la confusión. Te puedo ayudar a hacer tu pedido. ¿Quieres solo la Hamburguesa Sencilla o prefieres agregar una bebida? Estoy aquí para ayudarte.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no haya sido claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.
