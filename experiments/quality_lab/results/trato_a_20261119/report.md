# Estándar del asesor: trato_a_20261119

**NO PASA** · código `00df467 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 18 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

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
| ❌ respeta el largo (exacta) | 17 de 18 | Lo que escribe la IA no pasa del máximo de palabras del negocio, sin que el motor tenga que recortarlo. |
| ✅ sin emojis si no van (exacta) | 18 de 18 | Si el negocio no quiere emojis, el asesor no usa ninguno (el mensaje con los datos de pago es de la plataforma). |
| ✅ respeta el trato (exacta) | 18 de 18 | Con trato formal el asesor no tutea («tú», «te», «ti», «contigo», «tu», «tus»); con informal no dice «usted». |
| ✅ trato y tono (juez) | 18 de 18 | El asesor trata al cliente como dice «trato» en la ficha: «formal» es siempre de usted (nunca «tú», «te», «tu», «quieres», «cuéntame»…); «informal» es de tú; «neutral», amable y respetuoso. |
| ✅ horario del negocio (juez) | 18 de 18 | Cuando el cliente pregunta por el horario o por un día, el asesor da el de la ficha («horario»): los días y las horas correctos; si pregunta por un día que no está en el horario, le dice que ese día no atienden. |
| ❌ cierra como el negocio (juez) | 17 de 18 | Cuando el cliente decide comprar («lo quiero»), el asesor cierra como dice «estrategia_de_cierre» en la ficha. |

Gasto de la corrida: asesor USD 0.0198 · juez USD 0.0056. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 0.

Por cada mensaje del cliente: responde en 2.8 s (el 5 % más lento, 4.0 s o más) · USD 0.37 por cada 1.000 mensajes · fuera de formato: 0 de 54 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **respeta el largo** · asesor_ai_prod · pide que le cuente todo · turno 1: la IA escribió 42 palabras y el máximo es 40
  - Cliente: «Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene»
  - Asesor: «El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente.»
- **cierra como el negocio** · restaurant · decide comprar · turno 3: No ofrece medios de pago ni indica cómo pagar.
  - Cliente: «Me convence, lo quiero»
  - Asesor: «¡Perfecto! Solo necesito algunos datos para completar tu pedido: tu nombre, teléfono y dirección de entrega. ¿Me los puedes dar, por favor?»

## Las conversaciones

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puede proporcionar su nombre y teléfono para continuar con el proceso?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes y luego COP 110.000 mensuales. ¿Me puede proporcionar su nombre y teléfono para continuar?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 210.000 el primer mes (que incluye la configuración inicial) y luego COP 110.000 mensuales. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Excelente decisión. Por favor, compártame su nombre y teléfono para que el equipo lo contacte y pueda activar el servicio.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. ¿Me podría proporcionar su número de teléfono para continuar con la activación del Plan Básico?

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque automatiza respuestas y asegura seguimiento, evitando que pierda clientes.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye soporte prioritario y más opciones de personalización. ¿Le gustaría saber cómo el Plan Pro podría beneficiarlo aún más?

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (implementación más mensual). ¿Me puede compartir su nombre y teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados. Solo estamos disponibles de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, ¿me podría dar su nombre y número de teléfono?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial y el sistema mensual. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Para continuar, por favor proporcione su nombre y número de teléfono.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Solo necesito su número de teléfono para finalizar el proceso de activación.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque automatiza respuestas y el seguimiento, ayudando a no perder oportunidades de venta y a ahorrar tiempo.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, tenemos el Plan Pro, que ofrece prioridad en soporte. Sin embargo, el Plan Básico es ideal si busca empezar con automatización de respuestas y seguimiento.

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial y un asistente conversacional inteligente. Para avanzar, necesito su nombre y teléfono.

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes, de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico? Para ello, necesito su nombre y teléfono.

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico? Para ello, necesito su nombre y teléfono.

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Podría darme su nombre y teléfono para que el equipo lo contacte y comencemos con la implementación?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Le gustaría avanzar con la implementación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Para continuar, por favor, proporcióname su nombre y teléfono para que el equipo lo contacte y arranquemos con la implementación.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Por favor, compártame su número de teléfono para que el equipo lo contacte y podamos iniciar con la implementación del Plan Básico.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye prioridad en soporte. Si está interesado, puedo ayudarle a ver cuál se adapta mejor a sus necesidades.

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** El lunes no abrimos, solo atendemos de martes a domingo. ¿Quieres hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido? También puedo sugerirte una gaseosa o un jugo natural para acompañar.

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una o tal vez agregar una bebida para acompañar?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** ¡Perfecto! Para confirmar tu pedido, necesito tu nombre, teléfono y dirección de entrega. ¿Me los puedes proporcionar?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Solo necesito tu teléfono y dirección de entrega para completar el pedido de la Hamburguesa Sencilla.

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es una opción deliciosa y ligera, perfecta si no quieres algo muy pesado. Además, la hacemos al momento, así que siempre llega caliente a tu casa. Te conviene porque es una opción sabrosa y rápida para saciar tu hambre. ¿Te gustaría pedir una?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne y doble queso, y también ofrecemos bebidas como gaseosa y jugo natural. ¿Te gustaría probar alguna de estas opciones?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** No, el lunes estamos cerrados. Solo atendemos de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo más, como una gaseosa o un jugo natural?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una o necesitas ayuda con algo más?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** ¡Perfecto! Solo necesito algunos datos para completar tu pedido: tu nombre, teléfono y dirección de entrega. ¿Me los puedes dar, por favor?

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora, ¿me puedes dar tu número de teléfono y la dirección de entrega para completar tu pedido de la Hamburguesa Sencilla?

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es perfecta si buscas algo delicioso y no muy pesado. Funciona así: la pides por chat y la recibes caliente en casa o la puedes recoger en nuestro local. Te conviene porque es una opción sabrosa y rápida para satisfacer tu hambre sin complicaciones. ¿Te gustaría pedir una?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne y doble queso por COP 24.000. También ofrecemos bebidas como gaseosa por COP 5.000 y jugo natural por COP 7.000. ¿Te interesa alguna de estas opciones?

### restaurant · pregunta el horario

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de martes a domingo, de 12:00 a 22:00. ¿Te gustaría hacer tu pedido ahora?

**[3] Cliente:** ¿Y el lunes abren?

**[3] Asesor:** No, el lunes estamos cerrados. Pero estamos listos para atenderte de martes a domingo. ¿Te gustaría hacer tu pedido para otro día?

### restaurant · decide comprar

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Cuánto cuesta Hamburguesa Sencilla?

**[2] Asesor:** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedirla ahora?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** ¡Perfecto! Para completar tu pedido, necesito tu nombre, teléfono y dirección de entrega. 😊

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora necesito tu número de teléfono y dirección de entrega para finalizar el pedido.

### restaurant · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Hamburguesa Sencilla: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** La Hamburguesa Sencilla incluye carne artesanal, queso y vegetales frescos. Es perfecta si buscas algo delicioso y rápido para saciar el hambre. Te conviene porque es una opción sabrosa y a un buen precio: solo COP 18.000. Además, llega caliente a tu casa si pides a domicilio. ¿Te gustaría ordenar una? 😊

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además de la Hamburguesa Sencilla, tenemos la Hamburguesa Doble, que lleva doble carne, doble queso y salsa especial, por COP 24.000. También ofrecemos bebidas como Gaseosa a COP 5.000 y Jugo Natural a COP 7.000. ¿Te interesa alguna de estas opciones?
