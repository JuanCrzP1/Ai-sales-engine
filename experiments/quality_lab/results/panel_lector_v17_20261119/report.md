# Estándar del asesor: panel_lector_v17_20261119

**NO PASA** · código `933110d + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 18 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

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
| ❌ trato y tono (juez) | 14 de 18 | El asesor trata al cliente como dice «trato» en la ficha: «formal» es siempre de usted (nunca «tú», «te», «tu», «quieres», «cuéntame»…); «informal» es de tú; «neutral», amable y respetuoso. |
| ✅ horario del negocio (juez) | 18 de 18 | Cuando el cliente pregunta por el horario o por un día, el asesor da el de la ficha («horario»): los días y las horas correctos; si pregunta por un día que no está en el horario, le dice que ese día no atienden. |
| ✅ cierra como el negocio (juez) | 18 de 18 | Cuando el cliente decide comprar («lo quiero»), el asesor cierra como dice «estrategia_de_cierre» en la ficha. |

Gasto de la corrida: asesor USD 0.0198 · juez USD 0.0075. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 0.

Por cada mensaje del cliente: responde en 3.0 s (el 5 % más lento, 3.5 s o más) · USD 0.37 por cada 1.000 mensajes · fuera de formato: 0 de 54 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **respeta el largo** · asesor_ai_prod · decide comprar · turno 1: la IA escribió 44 palabras y el máximo es 40
  - Cliente: «Hola, me interesa Plan Basico»
  - Asesor: «Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes.»
- **respeta el largo** · asesor_ai_prod · pide que le cuente todo · turno 1: la IA escribió 42 palabras y el máximo es 40
  - Cliente: «Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía para integrar con WhatsApp y un asistente conversacional inteligente.»
- **trato y tono** · asesor_ai_prod · decide comprar · turno 2: El asesor usa 'te' en lugar de 'usted' siendo el trato formal.
  - Cliente: «¿Cuánto cuesta Plan Basico?»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y un asistente conversacional inteligente. ¿Te gustaría avanzar con la compra?»
- **trato y tono** · asesor_ai_prod · pide que le cuente todo · turno 1: el asesor usa 'te' en vez de 'le' o 'a usted'
  - Cliente: «Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene»
  - Asesor: «El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Te ayuda a responder rápido y mantener seguimiento constante, evitando que pierdas ventas. Es ideal para no depender del tiempo humano y recuperar oportunidades.»
- **trato y tono** · asesor_ai_prod · pide que le cuente todo · turno 2: el asesor usa 'te' en vez de 'le' o 'a usted'
  - Cliente: «¿Y qué más tienen?»
  - Asesor: «Además del Plan Básico, tenemos el Plan Pro, que ofrece prioridad en el soporte. Sin embargo, el Plan Básico es el más adecuado si buscas automatizar respuestas y seguimiento desde ya. ¿Te gustaría avanzar con el Plan Básico?»
- **trato y tono** · asesor_ai_prod · pide que le cuente todo · turno 1: El asesor usa 'te' en lugar de 'usted'
  - Cliente: «Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Te conviene porque automatiza respuestas y seguimiento, evitando que pierdas ventas por demoras.»
- **trato y tono** · asesor_ai_prod · pide que le cuente todo · turno 2: El asesor usa 'te' en lugar de 'usted'
  - Cliente: «¿Y qué más tienen?»
  - Asesor: «Además del Plan Básico, ofrecemos el Plan Pro, que incluye soporte prioritario. Sin embargo, el Plan Básico es ideal si buscas empezar a automatizar respuestas y seguimiento. ¿Te gustaría saber más sobre cómo el Plan Básico puede ayudarte?»
- **trato y tono** · asesor_ai_prod · decide comprar · turno 2: El asesor usa 'te' en lugar de 'usted'.
  - Cliente: «¿Cuánto cuesta Plan Basico?»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Es una inversión que se recupera fácilmente con solo unas pocas ventas. ¿Te gustaría avanzar con la activación?»

## Las conversaciones

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, por favor, indíqueme su nombre y teléfono.

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico? Necesito su nombre y teléfono para continuar.

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico? Necesito su nombre y teléfono para continuar.

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puede proporcionar su nombre y teléfono para continuar con el proceso?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y un asistente conversacional inteligente. ¿Te gustaría avanzar con la compra?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Por favor, indícame tu nombre y teléfono para que el equipo pueda contactarte y comenzar el proceso.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Por favor, indícame tu número de teléfono para que el equipo pueda contactarte y avanzar con el Plan Básico.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Te ayuda a responder rápido y mantener seguimiento constante, evitando que pierdas ventas. Es ideal para no depender del tiempo humano y recuperar oportunidades.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, tenemos el Plan Pro, que ofrece prioridad en el soporte. Sin embargo, el Plan Básico es el más adecuado si buscas automatizar respuestas y seguimiento desde ya. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes, y luego COP 110.000 mensuales. ¿Me podría dar su nombre y número de teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes (incluye la implementación y el primer mes de uso) y luego COP 110.000 mensuales. ¿Me puede compartir su nombre y teléfono para continuar?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 210.000 en el primer mes (implementación + primer mes) y luego COP 110.000 al mes. Lo que suele salir caro es perder conversaciones que ya estaban interesadas. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Excelente decisión. Para continuar, por favor, compártame su nombre y teléfono.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. ¿Me puede proporcionar su número de teléfono para finalizar el proceso de activación?

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Te conviene porque automatiza respuestas y seguimiento, evitando que pierdas ventas por demoras.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye soporte prioritario. Sin embargo, el Plan Básico es ideal si buscas empezar a automatizar respuestas y seguimiento. ¿Te gustaría saber más sobre cómo el Plan Básico puede ayudarte?

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Cuál es su nombre y número de contacto para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes.

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Es una inversión que se recupera fácilmente con solo unas pocas ventas. ¿Te gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Excelente decisión. Por favor, indícame tu nombre y número de teléfono para que el equipo te contacte y te ayude con la activación del Plan Básico.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Por favor, indícame tu número de teléfono para que el equipo te contacte y complete la activación del Plan Básico.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía para integrar con WhatsApp y un asistente conversacional inteligente.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye prioridad en soporte. Si te interesa, puedo explicarte cómo se adapta a tus necesidades.

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** No, el lunes estamos cerrados. Pero de martes a domingo estamos listos para atenderte. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una o añadir algo más para acompañarla?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** ¡Genial! Para confirmar tu pedido de una Hamburguesa Sencilla, necesito que me des tu nombre, teléfono y dirección de entrega. 😊

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora necesito tu teléfono y dirección de entrega para completar el pedido.

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es perfecta si buscas algo rico y ligero. Además, está recién hecha, así que la recibirás caliente en tu casa. Te conviene porque es una opción deliciosa y rápida para satisfacer tu hambre. ¿Te gustaría pedir una? 😊

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne, doble queso y salsa especial, y también puedes acompañarlas con una gaseosa o un jugo natural. ¿Te gustaría probar alguna de estas opciones?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir algo para acompañarla, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** No abrimos los lunes. Solo atendemos de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedirla junto con una bebida?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto, para confirmar tu pedido de una Hamburguesa Sencilla, necesito tu nombre, número de teléfono y dirección de entrega. ¿Me puedes ayudar con eso?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora, ¿puedes darme tu número de teléfono y dirección de entrega para completar tu pedido?

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es perfecta si buscas algo delicioso y no tan grande. Además, la hacemos al momento, así que llega caliente a tu casa. Es una opción rica y rápida para satisfacer tu hambre. ¿Te gustaría pedir una?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne, doble queso y salsa especial. También ofrecemos bebidas como gaseosa y jugo natural. ¿Te gustaría saber más sobre alguna opción en particular?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** No, el lunes no abrimos. Solo atendemos de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una o agregar algo más para acompañarla?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto, has elegido la Hamburguesa Sencilla. Para completar tu pedido, necesito tu nombre, teléfono y dirección de entrega. ¿Me los puedes proporcionar?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. ¿Me puedes dar tu teléfono y dirección de entrega para finalizar el pedido?

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es perfecta si buscas algo delicioso y no muy pesado. Te conviene porque es recién hecha y llega caliente a tu casa, ideal para satisfacer ese antojo. Además, su precio es de COP 18.000. ¿Te gustaría pedir una o necesitas más información?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne, doble queso y salsa especial, por COP 24.000. También ofrecemos gaseosas a COP 5.000 y jugos naturales a COP 7.000 para acompañar tu pedido. ¿Te interesa alguna de estas opciones?
