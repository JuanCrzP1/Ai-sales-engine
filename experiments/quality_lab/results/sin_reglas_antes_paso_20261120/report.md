# Estándar del asesor: sin_reglas_antes_paso_20261120

**NO PASA** · código `66adbb9` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 24 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 21 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 24 de 24 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 24 de 24 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 23 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 24 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 24 de 24 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0277 · juez USD 0.0087. Llamadas al modelo por mensaje: 2.36. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 6.

Por cada mensaje del cliente: responde en 3.0 s (el 5 % más lento, 3.8 s o más) · USD 0.42 por cada 1.000 mensajes · fuera de formato: 1 de 66 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **no repite la respuesta** · asesor_ai_prod · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha expresado su frustración por no recibir la ayuda que necesita.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información sobre precios y opciones de bebida. Se siente frustrado por no recibir la ayuda que necesita.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información que le proporcionaron y se mostró frustrado por no recibir la ayuda que necesita.»
- **explica cuando no entienden** · restaurant · la conversación se estanca · turno 2: No explica, solo repite la pregunta de qué no entiende.
  - Cliente: «No entiendo nada de lo que me dices»
  - Asesor: «Entiendo, ¿qué parte no te queda clara? Estoy aquí para ayudarte a decidir.»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer mes de servicio. Luego, se paga COP 110.000 mensualmente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber específicamente?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Solicita hablar con una persona en lugar de continuar con el asesor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (que incluye la implementación) y luego COP 110.000 mensual. ¿Me puedes dar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta sobre el proceso de reembolso en caso de que no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y algún detalle adicional para avanzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Sin embargo, lo importante es que con solo 3 ventas al mes, recuperas lo que pagas. ¿Qué te parece si avanzamos con la activación del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El costo es de COP 210.000 en el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, es normal sentirse así al principio. El Plan Básico te ayuda a responder mensajes rápidamente y hacer seguimiento a tus clientes automáticamente. Así no pierdes oportunidades de venta. ¿Te gustaría que te explique de nuevo los beneficios o cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha solicitado ser atendido por alguien del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha expresado su frustración por no recibir la ayuda que necesita.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000, que incluye la implementación y el primer mes. Luego, pagas COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para avanzar?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo, ¿qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Solicita hablar con una persona en lugar de continuar con el asesor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te entiendo, pero no manejo información sobre reembolsos. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta sobre el proceso de reembolso en caso de que no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 (implementación + primer mes) y luego COP 110.000 al mes. Para avanzar, necesito tu nombre y teléfono. ¿Me los puedes dar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Entiendo que busques descuentos, pero no tenemos promociones en este momento. Lo que suele salir caro es perder conversaciones que ya estaban interesadas. Cuando empiezas a recuperar leads, se paga solo. ¿Te gustaría seguir adelante con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, puede ser un poco confuso al principio. El Plan Básico incluye la configuración inicial y un asistente que responde automáticamente en WhatsApp. El primer mes se paga una sola vez, y luego es un costo mensual. ¿Te gustaría que te explique más sobre lo que incluye?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada sobre el plan y ha solicitado ser atendido por una persona del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te entiendo, y lamento que no hayas recibido la ayuda necesaria. Te paso con alguien del equipo para que te puedan asistir mejor. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Expresó que no entiende la información proporcionada y ha manifestado su frustración por no recibir la ayuda necesaria.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo, ¿qué necesitas saber? Estoy aquí para ayudarte.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Solicita hablar con una persona en lugar de continuar con el asistente.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Listo para continuar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero no manejo el tema de reembolsos. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta sobre el proceso de reembolso en caso de que no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Pero lo que suele salir caro es perder conversaciones que ya estaban interesadas. ¿Te parece si avanzamos con la activación del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de suscripción) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, déjame explicarte mejor. El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el primer mes de servicio. Después de eso, pagas COP 110.000 cada mes. ¿Te gustaría que te ayude a entender cómo esto puede ayudarte con tus mensajes?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada sobre el costo y la activación del plan. Pidió ser atendido por alguien del equipo porque no logró avanzar con el asistente.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración. Te paso con alguien del equipo para que te ayuden mejor. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Expresó que no entiende la información proporcionada sobre el costo y la activación del plan. Se siente frustrado por no recibir la ayuda necesaria y ha solicitado ser atendido por alguien del equipo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es tu pedido? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre la Hamburguesa Sencilla?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Solicita hablar con una persona en lugar de continuar con el asesor.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es tu pedido? También puedes agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 si te interesa.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu duda, pero para temas de reembolsos, te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Preguntó sobre el proceso de reembolso y si le devolverían el dinero en caso de que no le sirviera.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Pero la Hamburguesa Sencilla es una excelente opción por su calidad. ¿Te gustaría pedirla?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo más, como una gaseosa o un jugo natural?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, déjame aclarar. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o agregar algo más?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Mencionó que no entiende la información que le han proporcionado y ha solicitado ser atendido por una persona del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo que esto puede ser frustrante. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información proporcionada y ha manifestado su frustración al no recibir ayuda adecuada. Solicita ser atendido por una persona del equipo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pidió hablar con una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos, te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Preguntó sobre el proceso de reembolso y si le devolverían el dinero si no le sirve.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿La quieres llevar sola o te gustaría agregar una bebida como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento. Pero la Hamburguesa Sencilla es una opción deliciosa. ¿Te gustaría pedirla sola o con alguna bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, no hay problema. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir la hamburguesa sola o con bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Mencionó que no entiende la información sobre precios y opciones de bebida. Pidió ser atendido por una persona del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información sobre precios y opciones de bebida. Se siente frustrado por no recibir la ayuda que necesita.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, estoy aquí para ayudarte. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Ha solicitado hablar con una persona en lugar de continuar con el asistente.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es tu pedido? Además, ¿quieres agregar una bebida, como gaseosa o jugo natural?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones, te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Preguntó sobre el proceso de reembolso y si le devolverían el dinero si no le sirve.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No manejamos descuentos ni promociones en este momento. Pero la Hamburguesa Sencilla a COP 18.000 es una opción deliciosa. ¿Te gustaría seguir con el pedido?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, ¿qué parte no te queda clara? Estoy aquí para ayudarte a decidir.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. No entiende la información que le proporcionó el asesor y ha solicitado ser atendido por alguien del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información que le proporcionaron y se mostró frustrado por no recibir la ayuda que necesita.
