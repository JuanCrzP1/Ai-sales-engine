# Estándar del asesor: modelo_r2_gemini25flash_reglas_20261114

**NO PASA** · código `48d37ce + cambios` · modelo `google/gemini-2.5-flash` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ❌ pasa al equipo cuando debe (exacta) | 21 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 19 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 24 de 24 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 24 de 24 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 24 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ❌ sigue las reglas para pasar (juez) | 21 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 24 de 24 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0595 · juez USD 0.0087. Llamadas al modelo por mensaje: 2.41. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 6.

Por cada mensaje del cliente: responde en 2.2 s (el 5 % más lento, 2.9 s o más) · USD 0.9 por cada 1.000 mensajes · fuera de formato: 3 de 66 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **pasa al equipo cuando debe** · asesor_ai_prod · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico y pidió hablar con una persona.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla y pidió hablar con una persona.»
- **pasa al equipo cuando debe** · restaurant · pide una persona y luego insiste · turno 2: el chat pasó al equipo sin motivo (primero debía ofrecerle ayuda)
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla y pidió hablar con una persona.»
- **no repite la respuesta** · asesor_ai_prod · pide una persona y luego insiste · turno 3: repitió la respuesta anterior
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico y pidió hablar con una persona.»
- **no repite la respuesta** · asesor_ai_prod · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico. No entiende la explicación del asistente y se cansó de preguntar lo mismo.»
- **no repite la respuesta** · restaurant · pide una persona y luego insiste · turno 3: repitió la respuesta anterior
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Pidió hablar con una persona.»
- **no repite la respuesta** · restaurant · pide una persona y luego insiste · turno 3: repitió la respuesta anterior
  - Cliente: «No, gracias, prefiero que me atienda una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Pidió hablar con una persona.»
- **no repite la respuesta** · restaurant · la conversación se estanca · turno 4: repitió la respuesta anterior
  - Cliente: «Esto no me sirve, ya me cansé de preguntar lo mismo»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende lo que el asistente le dice y que ya se cansó de preguntar lo mismo.»
- **sigue las reglas para pasar** · asesor_ai_prod · pide una persona y luego insiste · turno 2: Debió ofrecer ayuda antes de pasar el chat.
  - Cliente: «Quiero hablar con una persona»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en el Plan Básico y pidió hablar con una persona.»
- **sigue las reglas para pasar** · restaurant · la conversación se estanca · turno 3: No ofrece ayuda antes de pasar el chat.
  - Cliente: «Sigo sin entender, ya te lo pregunté y no me ayudas»
  - Asesor: «Te paso con alguien del equipo por este mismo chat. En un momento te escriben.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende lo que el asistente le dice y que no lo ayuda.»
- **sigue las reglas para pasar** · restaurant · pregunta por un tema del equipo · turno 2: Debió ofrecer ayuda antes de pasar el chat, según 'offer_help_first'.
  - Cliente: «Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?»
  - Asesor: «Te paso con alguien del equipo por este mismo chat para que te ayuden con el tema del reembolso.»
  - Nota para el equipo: «El cliente está interesado en la Hamburguesa Sencilla. Pregunta sobre el proceso de reembolso y si le devuelven el dinero en caso de que el producto no le sirva.»

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a transformar tus conversaciones en ventas. Con él, tendrás la configuración inicial, la guía de integración con WhatsApp y tu asistente conversacional inteligente. Para activar tu Plan Básico, ¿cuál de nuestros medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y pidió hablar con una persona.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y pidió hablar con una persona.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. Con este plan, el primer mes pagas COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. ¿Te gustaría que avancemos con la activación?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat para que te ayuden con tus dudas sobre reembolsos y devoluciones. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Pregunta por la política de reembolso y si le devuelven el dinero en caso de que el servicio no le sirva.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Con este plan, recuperas tu inversión con solo 3 ventas al mes.  
  
Para avanzar con la activación, ¿me podrías dar tu nombre y número de teléfono?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tenemos descuentos o promociones en el Plan Básico, pero te aseguro que la inversión se recupera muy rápido. Con solo 3 ventas al mes, ya estás ganando.  
  
¿Te gustaría que te envíe los datos para la activación?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Incluye la configuración inicial y el asistente conversacional inteligente para que no pierdas más oportunidades. ¿Quieres que avancemos con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** ¡Claro! Te explico de forma sencilla: con el Plan Básico, tu WhatsApp se convierte en un vendedor automático que responde al instante y da seguimiento a tus clientes, incluso cuando no estás disponible. Así no pierdes ventas por no responder a tiempo.  
  
¿Te gustaría que te cuente cómo funciona en tu negocio?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. No entiende la explicación del asistente y pide ayuda.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. No entiende la explicación del asistente y se cansó de preguntar lo mismo.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Con él, tu WhatsApp se convierte en un vendedor que responde al instante y da seguimiento. ¿Quieres que activemos tu Plan Básico ahora mismo?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, con gusto te ayudo. ¿Qué duda tienes sobre el Plan Básico o qué necesitas para avanzar?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y pidió hablar con una persona.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico te ayuda a responder al instante y mantener el seguimiento de tus prospectos. Para empezar, ¿me confirmas tu nombre y un número de teléfono?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat para que te ayuden con lo del reembolso.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Pregunta sobre el reembolso si el plan no le sirve.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. Con este plan, el primer mes pagas COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales.  
  
¿Quieres que activemos tu Plan Básico ahora mismo?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tenemos descuentos o promociones en el Plan Básico. Sin embargo, con solo 3 ventas que recuperes al mes, el sistema se paga solo. ¿Te gustaría que te cuente cómo funciona para que veas el valor que te puede generar?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Con este plan, tu WhatsApp se convierte en un vendedor automático 24/7. ¿Te gustaría que activemos tu Plan Básico ahora mismo?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo. No te preocupes, te explico de forma sencilla. El Plan Básico te ayuda a que tu negocio no pierda ventas por no responder a tiempo. Tu WhatsApp responderá automáticamente a tus clientes, incluso cuando no estés disponible.   
  
¿Te gustaría que te muestre cómo funcionaría en tu caso?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Entiendo que no estoy logrando explicarme bien. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. Dice que no entiende la explicación del asistente y pide ayuda.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. Expresó que no entiende la información que le da el asistente y se cansó de preguntar lo mismo.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. Con este plan, el primer mes te costaría COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. ¿Te gustaría que lo activemos de una vez?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, con gusto te ayudo. ¿Hay algo en particular sobre el Plan Básico que te gustaría que revisemos o alguna duda que tengas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico y pidió hablar con una persona.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico te ayuda a responder al instante y mantener el seguimiento de tus clientes para que no pierdas más ventas. ¿Quieres que te ayude a activarlo de una vez?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat para que te ayuden con tu pregunta sobre reembolsos.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Pregunta sobre el reembolso si el plan no le sirve.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! Con el Plan Básico vas a poder responder al instante y hacer seguimiento a tus prospectos. Para empezar, el primer mes pagas COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. ¿Te confirmo el Plan Básico para tu negocio?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tenemos descuentos o promociones. El Plan Básico tiene un costo de COP 100.000 de implementación y COP 110.000 mensuales. Con solo 3 ventas al mes, recuperas la inversión. ¿Te gustaría que te envíe los datos para el pago del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Con este plan, tu WhatsApp se convierte en un vendedor 24/7 que responde al instante y da seguimiento a tus clientes para que no pierdas ninguna oportunidad. El primer mes tiene un costo de COP 210.000 (COP 100.000 de implementación + COP 110.000 del primer mes). Después, solo pagarías COP 110.000 mensuales.

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** ¡Claro! Te lo explico de forma sencilla. Con el Plan Básico, configuramos un asistente inteligente en tu WhatsApp para que responda a tus clientes automáticamente y les dé seguimiento, incluso cuando tú no estás disponible. Así, no pierdes ventas por no responder a tiempo. El primer mes pagas un solo valor que incluye la configuración y el primer mes de servicio. Luego, solo pagas una mensualidad.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Disculpa si no he sido claro. Te paso con alguien del equipo por este mismo chat para que te ayude a resolver todas tus dudas de la mejor manera. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en el Plan Básico. No entiende la explicación del asistente sobre el plan y pide ayuda.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración. Te paso con alguien del equipo por este mismo chat para que te ayude a resolver todas tus dudas. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en el Plan Básico. No entiende la explicación del asistente y se cansó de preguntar lo mismo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Te gustaría añadirle algo más o así está bien?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pidió hablar con una persona.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Pidió hablar con una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Cuántas te gustaría pedir?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat para que te ayuden con lo del reembolso.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Pregunta por el proceso de reembolso y si le devuelven el dinero en caso de que el producto no le sirva.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla tiene carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle una bebida para acompañar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tenemos descuentos o promociones. Pero te aseguro que nuestras hamburguesas son deliciosas y las hacemos al momento para que lleguen calientes a tu casa.

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla tiene carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle alguna bebida?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Disculpa, ¿hay algo en particular que no entiendas? Así te puedo ayudar mejor.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Lamento que no te esté ayudando. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende lo que el asistente le dice y que no lo ayuda.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento mucho que te sientas así. Te paso con alguien del equipo por este mismo chat para que te ayuden. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información que le da el asistente y se cansó de preguntar lo mismo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla tiene carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle una bebida?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pidió hablar con una persona.

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Pidió hablar con una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle alguna bebida?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat para que te ayuden con lo del reembolso.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Pregunta por el proceso de reembolso si el producto no le sirve y si le devuelven el dinero.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle una bebida para acompañar?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tenemos descuentos o promociones activas. Pero te aseguro que nuestras hamburguesas artesanales valen la pena. ¿Te gustaría ordenar la Hamburguesa Sencilla?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000.  
  
¿Te gustaría añadir una bebida para acompañar tu pedido?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Disculpa, ¿hay algo en particular que no te queda claro? Con gusto te ayudo a resolver cualquier duda sobre la Hamburguesa Sencilla o lo que necesites.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende lo que el asistente le dice y que no lo ayuda.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende lo que el asistente le dice y que ya se cansó de preguntar lo mismo.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Hola! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle una bebida para acompañar?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Claro, con gusto te ayudo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla y pidió que lo atendiera una persona.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Quieres una o prefieres la Doble?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Te paso con alguien del equipo por este mismo chat para que te ayuden con el tema del reembolso.

*[2] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Pregunta sobre el proceso de reembolso y si le devuelven el dinero en caso de que el producto no le sirva.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Hola! Qué buena elección. La Hamburguesa Sencilla tiene carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle algo para acompañar, como una gaseosa o un jugo natural?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** Por ahora no tenemos descuentos o promociones en las hamburguesas. Pero te aseguro que la Hamburguesa Sencilla es deliciosa y recién hecha. ¿Te gustaría pedirla?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! La Hamburguesa Sencilla tiene carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle una bebida para acompañar?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Perdona, me enredé un poco. Te confirmo que la Hamburguesa Sencilla trae carne artesanal, queso y vegetales frescos y cuesta COP 18.000. ¿Te gustaría pedirla?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Disculpa si no he sido claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

*[3] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Dice que no entiende la información que le da el asistente y que no lo ayuda.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento mucho que te sientas así. Te paso con alguien del equipo por este mismo chat para que te ayuden. En un momento te escriben.

*[4] Nota para el equipo:* El cliente está interesado en la Hamburguesa Sencilla. Expresó que no entiende la información que se le ha dado y que ya se cansó de preguntar lo mismo.
