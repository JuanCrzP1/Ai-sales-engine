# Estándar del asesor: sin_reglas_despues_paso_20261120

**NO PASA** · código `66adbb9 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ❌ pasa al equipo cuando debe (exacta) | 23 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 22 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 24 de 24 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 24 de 24 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 23 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 24 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ❌ nota fiel (juez) | 23 de 24 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0274 · juez USD 0.0096. Llamadas al modelo por mensaje: 2.38. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 5.

Por cada mensaje del cliente: responde en 3.5 s (el 5 % más lento, 4.7 s o más) · USD 0.42 por cada 1.000 mensajes · fuera de formato: 3 de 66 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico. Ha solicitado hablar con una persona.»
- **no repite la respuesta** · asesor_ai_prod · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te entiendo, lamento que no haya quedado claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha expresado su frustración por no recibir la ayuda que necesita.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Mencionó que no entiende la información que le proporcionaron y expresó su frustración por no recibir ayuda adecuada.»
- **explica cuando no entienden** · restaurant · la conversación se estanca · turno 2: No explica, solo pregunta qué no entiende sin dar contexto.
  - Cliente: «No entiendo nada de lo que me dices»
  - Asesor: «Entiendo, ¿hay algo específico que no te quede claro? Estoy aquí para ayudarte a decidir.»
- **nota fiel** · restaurant · la conversación se estanca · turno 3: El cliente no pidió ser atendido por una persona.
  - Cliente: «Sigo sin entender, ya te lo pregunté y no me ayudas»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. No logró entender la información sobre el precio y la cantidad del pedido. Pidió ser atendido por una persona del equipo.»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 al mes). ¿Me puedes compartir tu nombre y teléfono para avanzar?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Solicita hablar con una persona en lugar de continuar con el asesor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 en el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y número de teléfono para avanzar con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta sobre el proceso de reembolso en caso de que no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, necesito tu nombre, teléfono y detalles para proceder con el pago.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No ofrecemos descuentos o promociones en este momento. Sin embargo, cada venta que recuperas puede cubrir el costo del servicio. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Este plan te ofrece configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para continuar?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, es normal que al principio parezca confuso. El Plan Básico te ayuda a responder y hacer seguimiento a tus clientes automáticamente, así evitas perder ventas por no responder a tiempo. ¿Te gustaría que te explique más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te entiendo, lamento que no haya quedado claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha solicitado ser atendido por alguien del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te entiendo, lamento que no haya quedado claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha expresado su frustración por no recibir la ayuda que necesita.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Cómo te gustaría pagar?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas saber sobre el Plan Básico o algún otro aspecto?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Solicita hablar con una persona para obtener más información.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Tiene un costo de COP 100.000 de implementación y COP 110.000 al mes. Para continuar, necesitaría tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta sobre el proceso de reembolso en caso de que no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Sin embargo, con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para continuar?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, a veces puede ser confuso. El Plan Básico te ayuda a responder mensajes de manera automática y mantener el seguimiento con tus clientes. Así no pierdes oportunidades de venta. ¿Te gustaría que te explique más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y ha expresado que no entiende la información proporcionada sobre el mismo. Ha solicitado ser atendido por una persona del equipo debido a la confusión que tiene con la explicación.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no hayas recibido la ayuda que necesitas. Te paso con alguien del equipo para que puedan atenderte mejor. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Expresó que no entiende la información proporcionada y ha manifestado su frustración por no recibir la ayuda necesaria.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Me los puedes proporcionar?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Ha solicitado hablar con una persona.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Solicita hablar con una persona en lugar de continuar con el asesor.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Este plan incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para iniciar el proceso?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Preguntó sobre el proceso de reembolso en caso de que el plan no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones. Lo que suele salir caro es perder conversaciones que ya estaban interesadas. El Plan Básico te ayuda a recuperar esas oportunidades. ¿Te parece bien avanzar con la activación?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración inicial y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, es normal sentirse así al inicio. El Plan Básico incluye la configuración inicial y un asistente que responde automáticamente en WhatsApp. Con esto, podrás responder rápido y hacer seguimiento a tus clientes. ¿Te gustaría que te explique más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te entiendo, lamento que no esté claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha solicitado ser atendido por una persona del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te entiendo, lamento que no estés recibiendo la ayuda que necesitas. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que no entiende la información proporcionada y ha expresado su frustración por no recibir la ayuda necesaria.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre tu pedido?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Ha solicitado hablar con una persona para recibir atención. No ha mencionado si ya realizó un pago.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** No puedo ayudarte con eso, pero te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Preguntó sobre el proceso de reembolso y si le devolverían el dinero en caso de que no le sirviera.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es tu pedido? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No manejamos descuentos ni promociones, pero nuestra Hamburguesa Sencilla es deliciosa y fresca. ¿Te gustaría pedirla junto con una gaseosa o un jugo natural?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿La quieres acompañar con una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Lo siento si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. Puedes agregar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría alguna bebida con tu hamburguesa?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo que puede ser confuso. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. No logró entender la información sobre los precios y las opciones de bebida. Pidió ser atendido por una persona del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que estés teniendo esta experiencia. Voy a pasarte con alguien del equipo para que te ayuden mejor. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. No entiende la información sobre los precios y las opciones de bebidas. Ha expresado su frustración por no recibir la ayuda que necesita.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas saber sobre la Hamburguesa Sencilla?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Ha solicitado hablar con una persona para recibir atención directa.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y la quieres con algún complemento, como una gaseosa o un jugo natural?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolsos y devoluciones te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Preguntó sobre el proceso de reembolso y si le devolverían el dinero en caso de que no le sirviera.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿La quieres acompañar con algo, como una gaseosa o un jugo natural?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones en este momento, pero la Hamburguesa Sencilla es una excelente opción por su precio. ¿Te gustaría seguir con el pedido?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, ¿hay algo específico que no te quede claro? Estoy aquí para ayudarte a decidir.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. No entiende la información que le proporcionó el asesor y ha solicitado ser atendido por alguien del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Mencionó que no entiende la información que le proporcionaron y expresó su frustración por no recibir ayuda adecuada.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Ha solicitado hablar con una persona para recibir atención directa.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación por el reembolso, pero te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Preguntó sobre el proceso de reembolso y si le devolverían el dinero en caso de que no le sirviera.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar algo más, como una gaseosa (COP 5.000) o un jugo natural (COP 7.000) para acompañar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No ofrecemos descuentos ni promociones en este momento. Sin embargo, la Hamburguesa Sencilla es una excelente opción. ¿Te gustaría pedirla sola o acompañarla con una bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida como gaseosa o jugo natural?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, disculpa si no fui claro. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una sola o para más personas? También puedo ofrecerte una bebida para acompañar.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. No logró entender la información sobre el precio y la cantidad del pedido. Pidió ser atendido por una persona del equipo.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento la confusión. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende las respuestas del asesor y ha manifestado su frustración por no recibir la ayuda que necesita.
