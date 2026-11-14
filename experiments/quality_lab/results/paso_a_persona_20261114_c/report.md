# Estándar del asesor: paso_a_persona_20261114_c

**NO PASA** · código `42e7a19 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 24 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 24 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 24 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ❌ sigue las reglas para pasar (juez) | 23 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |

Gasto de la corrida: asesor USD 0.0363 · juez USD 0.0087. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 1.

## Lo que no pasó

- **sigue las reglas para pasar** · restaurant · pregunta por un tema del equipo · turno 2: No pasa el chat directamente para un tema de 'always_topics'.
  - Cliente: «Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?»
  - Asesor: «Entiendo tu preocupación, pero el equipo se encarga de los reembolsos y devoluciones. Te puedo ayudar con tu pedido o pasar tu consulta con ellos. ¿Te gustaría que te ayude con tu pedido?»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas saber específicamente?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Entiendo, te paso con una persona del equipo para que te atiendan mejor. Un momento, por favor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, voy a pasarlo con el equipo para que te ayuden mejor.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (que cubre la implementación y el primer pago mensual), y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No manejamos descuentos o promociones en este momento. Sin embargo, con solo tres ventas al mes, recuperas la inversión del plan. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100,000 de implementación y COP 110,000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos a aclararlo. El Plan Básico te ayuda a responder mensajes automáticamente y hacer seguimiento a tus clientes, lo que evita que pierdas ventas. Cuesta COP 210,000 el primer mes, que incluye la configuración y el primer pago mensual. ¿Te gustaría que te explique más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Voy a pasar tu consulta al equipo para que te ayuden mejor. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración, y lamento que no haya sido claro. Voy a pasar tu consulta al equipo para que te ofrezcan la ayuda que necesitas. Un momento, por favor.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio). Luego, se paga mensualidad de COP 110.000. ¿Me puedes dar tu nombre y número de teléfono para proceder?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Entiendo, te voy a pasar con una persona del equipo para que te ayude.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Cuál es tu nombre y número de teléfono para empezar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero lo que puedo hacer es pasarte con el equipo para que te ayuden con ese tema. ¿Te parece bien?

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para comenzar, necesito tu nombre, teléfono y detalles. ¿Te gustaría que te envíe los datos de pago?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Sin embargo, considera que con solo 3 ventas al mes recuperas lo que pagas. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y los detalles para proceder con el pago?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos a desglosarlo. El Plan Básico te ayuda a automatizar las respuestas en WhatsApp y a hacer seguimiento a tus clientes. La implementación cuesta COP 100.000 y luego pagas COP 110.000 cada mes. ¿Te gustaría que te explique cómo funciona en tu caso?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Voy a pasar tu consulta al equipo para que te puedan ayudar mejor. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Voy a pasar tu caso al equipo para que puedan ayudarte directamente. Un momento, por favor.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Este plan incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Entiendo, voy a pasarte con una persona del equipo que te podrá ayudar mejor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con el equipo para que te ayuden con esa consulta sobre reembolsos.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu nombre y teléfono para comenzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Sin embargo, piensa en lo que suele costar perder conversaciones que ya estaban interesadas. Con solo 3 ventas al mes, recuperas lo que pagas por el servicio. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos a hacerlo más sencillo. El Plan Básico te ayuda a responder mensajes y hacer seguimiento automáticamente. Así no pierdes clientes por no contestar a tiempo. ¿Te gustaría saber cómo funcionaría en tu negocio?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Para ayudarte mejor, voy a pasar tu consulta al equipo, ellos podrán explicarte más a fondo. Un momento, por favor.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Voy a pasar tu consulta al equipo para que te ayuden mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, lo mejor es que te ayude el equipo. Te paso con ellos para que te den la información que necesitas.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones disponibles en este momento. Sin embargo, la Hamburguesa Sencilla es una opción deliciosa y a buen precio. ¿Te gustaría seguir con tu pedido?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir algo más, como una gaseosa o un jugo natural?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, disculpa si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres que te explique más sobre el pedido o cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no haya sido claro. Te puedo ayudar con tu pedido de Hamburguesa Sencilla, que cuesta COP 18.000. Si quieres, puedo pasar el chat a un compañero para que te ayude mejor. ¿Te gustaría eso?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés satisfecho. Te pasaré con el equipo para que te ayuden mejor. Ellos podrán resolver tus dudas.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, estoy aquí para ayudarte. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, te paso con el equipo para que te ayuden con eso. ¿Te gustaría que continúe con tu pedido mientras tanto?

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Sin embargo, la Hamburguesa Sencilla es deliciosa y vale la pena. ¿Te gustaría pedirla con una bebida para acompañar?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo que pueda resultar confuso. La Hamburguesa Sencilla cuesta COP 18.000. Además, puedes agregar una bebida: gaseosa a COP 5.000 o jugo natural a COP 7.000. ¿Te gustaría pedir solo la hamburguesa o prefieres añadir una bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Estoy aquí para ayudarte. ¿Te gustaría que te explique mejor las opciones de la hamburguesa y las bebidas? O si prefieres, puedo pasarte con el equipo para que te ayuden.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés satisfecho con la información. Voy a pasar tu consulta al equipo para que puedan ayudarte mejor. Un momento, por favor.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, estoy aquí para ayudarte. ¿Qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Entiendo, te paso con el equipo para que te atiendan mejor.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero el equipo se encarga de los reembolsos y devoluciones. Te puedo ayudar con tu pedido o pasar tu consulta con ellos. ¿Te gustaría que te ayude con tu pedido?

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No ofrecemos descuentos ni promociones en este momento. Pero la Hamburguesa Sencilla es una excelente opción. ¿Te gustaría confirmarla y agregar una bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, permíteme aclarar. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa a COP 5.000 o jugo natural a COP 7.000. ¿Te gustaría pedir la hamburguesa sola o con alguna bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no esté claro. Voy a pasar tu consulta al equipo para que te ayuden mejor. ¿Hay algo específico que quieras saber sobre la Hamburguesa Sencilla?

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Voy a pasar tu consulta al equipo para que te ayuden mejor. Gracias por tu paciencia.
