# Estándar del asesor: panel_obedece_20261119

**NO PASA** · código `901f448` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 18 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 18 de 18 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 18 de 18 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 18 de 18 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 18 de 18 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 18 de 18 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 18 de 18 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 18 de 18 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 18 de 18 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 18 de 18 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ❌ respeta el largo (exacta) | 16 de 18 | Lo que escribe la IA no pasa del máximo de palabras del negocio, sin que el motor tenga que recortarlo. |
| ✅ sin emojis si no van (exacta) | 18 de 18 | Si el negocio no quiere emojis, el asesor no usa ninguno (el mensaje con los datos de pago es de la plataforma). |
| ❌ trato y tono (juez) | 16 de 18 | El asesor trata al cliente como dice «trato» en la ficha: «formal» es siempre de usted (nunca «tú», «te», «tu», «quieres», «cuéntame»…); «informal» es de tú; «neutral», amable y respetuoso. |
| ✅ horario del negocio (juez) | 18 de 18 | Cuando el cliente pregunta por el horario o por un día, el asesor da el de la ficha («horario»): los días y las horas correctos; si pregunta por un día que no está en el horario, le dice que ese día no atienden. |
| ❌ cierra como el negocio (juez) | 17 de 18 | Cuando el cliente decide comprar («lo quiero»), el asesor cierra como dice «estrategia_de_cierre» en la ficha. |

Gasto de la corrida: asesor USD 0.0193 · juez USD 0.0078. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 0.

Por cada mensaje del cliente: responde en 2.8 s (el 5 % más lento, 3.6 s o más) · USD 0.36 por cada 1.000 mensajes · fuera de formato: 0 de 54 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **respeta el largo** · asesor_ai_prod · pregunta el horario · turno 1: la IA escribió 46 palabras y el máximo es 40
  - Cliente: «Hola, me interesa Plan Basico»
  - Asesor: «Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente.»
- **respeta el largo** · asesor_ai_prod · pide que le cuente todo · turno 1: la IA escribió 43 palabras y el máximo es 40
  - Cliente: «Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente.»
- **trato y tono** · asesor_ai_prod · pregunta el horario · turno 2: El asesor cambia el trato de formal a informal ('Te gustaría').
  - Cliente: «¿En qué horario atienden?»
  - Asesor: «Atendemos de lunes a viernes, de 08:00 a 17:00. ¿Te gustaría avanzar con la activación del Plan Básico?»
- **trato y tono** · asesor_ai_prod · pide que le cuente todo · turno 1: El asesor usa 'te' en lugar de 'le' o 'a usted', rompiendo el trato formal.
  - Cliente: «Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Te conviene porque automatiza respuestas y seguimiento, ayudando a no perder ventas.»
- **trato y tono** · asesor_ai_prod · pide que le cuente todo · turno 2: El asesor usa 'te' en lugar de 'le' o 'a usted', rompiendo el trato formal.
  - Cliente: «¿Y qué más tienen?»
  - Asesor: «Además del Plan Básico, también ofrecemos el Plan Pro, que incluye soporte prioritario. Si buscas más funcionalidades, este plan podría ser una buena opción. ¿Te gustaría saber más sobre el Plan Pro?»
- **cierra como el negocio** · asesor_ai_prod · decide comprar · turno 2: Ofrece datos de pago antes de capturar el lead.
  - Cliente: «¿Cuánto cuesta Plan Basico?»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y el asistente conversacional. ¿Te gustaría que te enviara los datos de pago para comenzar?»
- **cierra como el negocio** · asesor_ai_prod · decide comprar · turno 3: Ofrece medios de pago en lugar de capturar el lead.
  - Cliente: «Me convence, lo quiero»
  - Asesor: «Para proceder, por favor indícame con cuál de los siguientes medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.»
- **cierra como el negocio** · asesor_ai_prod · decide comprar · turno 4: Pide datos para proceder con el pago, no para contactar.
  - Cliente: «Me llamo Ana»
  - Asesor: «Gracias, Ana. Ahora, ¿me puedes compartir tu número de teléfono para completar la información y proceder con el pago?»

## Las conversaciones

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente.

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes y luego COP 110.000 mensuales. ¿Me puede compartir su nombre y teléfono para continuar?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial, y luego COP 110.000 mensuales. Recuerde que con solo tres ventas al mes recupera lo que paga. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Necesito que me comparta su nombre y teléfono para proceder con la activación.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Solo necesito su número de teléfono para continuar con la activación del Plan Básico.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye prioridad en soporte. Si buscas un seguimiento más avanzado, el Plan Pro podría ser una buena opción. ¿Te gustaría saber más sobre este plan?

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puede compartir su nombre y teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente para automatizar tus respuestas. Para avanzar, ¿me puedes compartir tu nombre y teléfono?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y el asistente conversacional. ¿Te gustaría que te enviara los datos de pago para comenzar?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Para proceder, por favor indícame con cuál de los siguientes medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora, ¿me puedes compartir tu número de teléfono para completar la información y proceder con el pago?

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Es ideal para automatizar respuestas y mantener seguimiento, ayudando a no perder ventas por demoras.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye soporte prioritario. Si te interesa más información sobre alguna opción, ¿qué necesitas resolver en tu negocio?

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Podría darme su nombre y teléfono para avanzar con la activación?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes, de 08:00 a 17:00. ¿Te gustaría avanzar con la activación del Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** Lo siento, no atendemos los sábados. Solo de lunes a viernes. ¿Te gustaría avanzar con la activación del Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes, y luego COP 110.000 mensuales. ¿Me puede brindar su nombre y teléfono para continuar?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 210.000 el primer mes (incluye configuración inicial) y luego COP 110.000 mensuales. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Para continuar, por favor compártame su nombre y teléfono.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. ¿Cuál es su número de teléfono para completar el proceso de activación?

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Te conviene porque automatiza respuestas y seguimiento, ayudando a no perder ventas.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, también ofrecemos el Plan Pro, que incluye soporte prioritario. Si buscas más funcionalidades, este plan podría ser una buena opción. ¿Te gustaría saber más sobre el Plan Pro?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** Lamentablemente, el lunes no abrimos. Solo atendemos de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una? También puedes añadir una bebida si lo deseas.

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** ¡Perfecto! Entonces, para confirmar tu pedido de una Hamburguesa Sencilla, necesito tu nombre, teléfono y dirección de entrega. ¿Me los puedes dar, por favor?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora necesito tu número de teléfono y la dirección de entrega para completar tu pedido.

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos, ¡todo recién hecho! Te conviene porque es perfecta para saciar el hambre sin complicaciones y llega caliente a tu casa. Además, es fácil de pedir por chat. ¿Te gustaría pedir una o necesitas más información?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne y doble queso, y también ofrecemos bebidas como gaseosas y jugos naturales. ¿Te gustaría probar alguna de estas opciones junto con tu hamburguesa?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y te gustaría agregar algo de beber, como una gaseosa o un jugo natural?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** El lunes no abrimos, solo atendemos de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedirla?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto, voy a tomar tu pedido de una Hamburguesa Sencilla. ¿Me puedes dar tu nombre, teléfono y dirección de entrega para completar el pedido?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. ¿Cuál es tu número de teléfono y dirección de entrega?

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos, todo recién hecho. Te conviene porque es una opción deliciosa y rápida para satisfacer tu hambre sin salir de casa. Además, te la llevamos caliente a tu puerta. ¿Te gustaría pedir una?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne, doble queso y salsa especial. También ofrecemos gaseosa y jugo natural para acompañar tu pedido. ¿Te gustaría probar alguna de estas opciones?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar algo más, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** El lunes no abrimos, solo atendemos de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido? También puedes agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 si te interesa.

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una o tal vez agregar algo más, como una gaseosa o un jugo natural?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto, entonces confirmemos tu pedido de una Hamburguesa Sencilla por COP 18.000. ¿Cuál es tu nombre, teléfono y dirección de entrega?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora, ¿cuál es tu número de teléfono y dirección de entrega?

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es perfecta si buscas algo delicioso y no muy grande. Además, la preparamos al momento para que la recibas caliente en tu casa. Te conviene porque es una opción rica y rápida para saciar el hambre. ¿Te gustaría pedir una o necesitas más información?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne, doble queso y salsa especial. También ofrecemos bebidas, como gaseosa y jugo natural. ¿Te gustaría probar alguna de estas opciones? 🍔
