# Estándar del asesor: modelo_r2_gpt6luna_reglas_20261114

**NO PASA** · código `48d37ce + cambios` · modelo `openai/gpt-6-luna` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 24 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 19 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 24 de 24 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 24 de 24 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 24 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 24 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 24 de 24 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0118 · juez USD 0.0056. Llamadas al modelo por mensaje: 2.36. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 3.

Por cada mensaje del cliente: responde en 3.6 s (el 5 % más lento, 5.5 s o más) · USD 0.18 por cada 1.000 mensajes · fuera de formato: 0 de 66 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **no repite la respuesta** · asesor_ai_prod · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Entiendo la frustración. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico. Dice que no entiende la información y que no ha recibido ayuda pese a preguntar varias veces.»
- **no repite la respuesta** · asesor_ai_prod · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico. Dice que sigue sin entender y que ya se cansó de preguntar lo mismo.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende las respuestas y que ya se cansó de preguntar lo mismo.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende las respuestas y que ya se cansó de preguntar lo mismo.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende las respuestas y que ya se cansó de preguntar lo mismo.»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; se puede cancelar mensualmente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo por aquí. ¿Qué necesitas resolver con una persona del equipo?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y prefiere que lo atienda una persona.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo para que te ayude con el tema del reembolso. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta si le devuelven el dinero cuando el plan no le sirve.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 (implementación + mes); luego COP 110.000 al mes. No incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, compárteme tu nombre, teléfono y qué tipo de negocio tienes.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tengo descuentos ni promociones informados. El Plan Básico cuesta COP 210.000 el primer mes y luego COP 110.000 mensuales, sin permanencia obligatoria. Si te sirve, avanzamos con la activación y me compartes tu nombre, teléfono y detalles de tu negocio.

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdón, te lo explico simple: el Plan Básico ayuda a responder y dar seguimiento a tus clientes por WhatsApp. El primer mes cuesta COP 210.000 y después COP 110.000 al mes. Para empezar, necesito tu nombre, teléfono y qué negocio tienes.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo la frustración. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y dice que sigue sin entender la información que recibió y que no le han ayudado.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo la frustración. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Dice que no entiende la información y que no ha recibido ayuda pese a preguntar varias veces.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no tiene permanencia obligatoria. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo por aquí. ¿Qué necesitas revisar del Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y prefiere que lo atienda una persona.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 mensuales; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, envíame tu nombre, teléfono y detalles de tu negocio, y te indico cómo pagar.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta si le devuelven el dinero si no le sirve.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tengo descuentos o promociones confirmados. El Plan Básico cuesta COP 100.000 de implementación + COP 110.000 al mes; el primer mes pagas COP 210.000 y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Avanzamos con esos datos para iniciar: nombre, teléfono y detalles de tu negocio.

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico encaja para automatizar respuestas y dar seguimiento en WhatsApp. El primer mes cuesta COP 210.000 (implementación + primer mes); luego COP 110.000 al mes. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdón, te lo explico simple: el Plan Básico configura un asistente que responde y hace seguimiento por WhatsApp. Cuesta COP 100.000 de implementación y COP 110.000 al mes; el primer mes pagas COP 210.000. Luego, COP 110.000 al mes. Si te sirve, avanzamos con la activación y me compartes tu nombre, teléfono y detalles del negocio.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Dice que sigue sin entender la explicación y que no le han ayudado.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Dice que sigue sin entender y que ya se cansó de preguntar lo mismo.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** El Plan Básico encaja para automatizar respuestas y dar seguimiento por WhatsApp. El primer mes cuesta COP 210.000 (COP 100.000 de implementación + COP 110.000 mensual); después, COP 110.000 al mes. Incluye configuración inicial, guía de integración y asistente conversacional. No incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, compárteme tu nombre, teléfono y detalles de tu negocio; luego eliges cómo pagar.

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo por aquí. ¿Qué necesitas resolver sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y pidió que lo atienda una persona.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** El Plan Básico encaja para automatizar respuestas y seguimiento en WhatsApp. El primer mes cuesta COP 210.000: COP 100.000 de implementación y COP 110.000 del mes; después, COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional. No incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, envíame tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pregunta si le devuelven el dinero si no le sirve.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; puedes cancelar mensualmente. Para arrancar, compárteme tu nombre, teléfono y un detalle de cómo usas WhatsApp para atender clientes.

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tengo descuentos o promociones registrados. El Plan Básico cuesta COP 210.000 el primer mes y luego COP 110.000 al mes, sin permanencia obligatoria. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Si te sirve, seguimos con la activación.

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no incluye costos de Meta, tokens de IA ni personalización avanzada. Si te sirve, arrancamos con la configuración. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdón, me enredé. El Plan Básico ayuda a responder y hacer seguimiento por WhatsApp automáticamente. ¿Qué pasa hoy con tus mensajes: no alcanzas a responderlos o se te pierden los seguimientos?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo la molestia. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Dice que no entiende la información recibida y que no le han ayudado.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico y dice que no entiende la información recibida. Reclama que ya preguntó lo mismo y no le ayudan.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería para domicilio en El Poblado o Laureles, o para recoger?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo por aquí. ¿Qué necesitas saber sobre tu pedido de Hamburguesa Sencilla?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pidió que lo atienda una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería para domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pregunta cómo funciona el reembolso si no le sirve.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería a domicilio en El Poblado o Laureles, o para recoger?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tengo descuentos ni promociones para ofrecerte. La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas te gustaría pedir?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdón, te lo explico fácil: la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres pedir una?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que sigue sin entender y que no le ayudan.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende las respuestas y que ya se cansó de preguntar lo mismo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería para domicilio o para recoger?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo por aquí. ¿Qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y prefiere que lo atienda una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería a domicilio o para recoger?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y preguntó cómo funciona el reembolso si no le sirve.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tengo promociones registradas. La Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres que sigamos con tu pedido?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdón, te lo digo más sencillo: la Hamburguesa Sencilla vale COP 18.000. ¿Quieres pedir una?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y dice que no entiende la información recibida y que no le han ayudado.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende las respuestas y que ya se cansó de preguntar lo mismo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería a domicilio o para recoger?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo por aquí. ¿Qué necesitas saber sobre tu pedido?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pidió que lo atienda una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería a domicilio o para recoger?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pregunta cómo funciona el reembolso si no le sirve.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio o recoger en el local?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tengo descuentos ni promociones informados. La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres pedir?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio o recoger en el local?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdón, te lo explico más claro: la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres pedir una?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y dice que sigue sin entender la información que recibió.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende las respuestas y que ya se cansó de preguntar lo mismo.
