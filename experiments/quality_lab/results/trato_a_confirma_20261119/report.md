# Estándar del asesor: trato_a_confirma_20261119

**NO PASA** · código `00df467 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 15 conversaciones (5 muestras por negocio: asesor_ai_prod)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 15 de 15 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 15 de 15 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 15 de 15 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 15 de 15 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 15 de 15 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 15 de 15 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 15 de 15 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 15 de 15 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 15 de 15 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ respeta el largo (exacta) | 15 de 15 | Lo que escribe la IA no pasa del máximo de palabras del negocio, sin que el motor tenga que recortarlo. |
| ✅ sin emojis si no van (exacta) | 15 de 15 | Si el negocio no quiere emojis, el asesor no usa ninguno (el mensaje con los datos de pago es de la plataforma). |
| ❌ respeta el trato (exacta) | 14 de 15 | Con trato formal el asesor no tutea («tú», «te», «ti», «contigo», «tu», «tus»); con informal no dice «usted». |
| ❌ trato y tono (juez) | 14 de 15 | El asesor trata al cliente como dice «trato» en la ficha: «formal» es siempre de usted (nunca «tú», «te», «tu», «quieres», «cuéntame»…); «informal» es de tú; «neutral», amable y respetuoso. |
| ✅ horario del negocio (juez) | 15 de 15 | Cuando el cliente pregunta por el horario o por un día, el asesor da el de la ficha («horario»): los días y las horas correctos; si pregunta por un día que no está en el horario, le dice que ese día no atienden. |
| ✅ cierra como el negocio (juez) | 15 de 15 | Cuando el cliente decide comprar («lo quiero»), el asesor cierra como dice «estrategia_de_cierre» en la ficha. |

Gasto de la corrida: asesor USD 0.0182 · juez USD 0.0047. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 0.

Por cada mensaje del cliente: responde en 3.0 s (el 5 % más lento, 4.1 s o más) · USD 0.4 por cada 1.000 mensajes · fuera de formato: 0 de 45 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **respeta el trato** · asesor_ai_prod · decide comprar · turno 4: el trato es formal y dijo «tu»
  - Cliente: «Me llamo Ana»
  - Asesor: «Gracias, Ana. Ahora, por favor, compárteme tu número de teléfono para completar el registro.»
- **trato y tono** · asesor_ai_prod · decide comprar · turno 4: Cambia de trato formal a informal al usar 'tu'.
  - Cliente: «Me llamo Ana»
  - Asesor: «Gracias, Ana. Ahora, por favor, compárteme tu número de teléfono para completar el registro.»

## Las conversaciones

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puede proporcionar su nombre y teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No, solo atendemos de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, ¿me puede proporcionar su nombre y teléfono?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Este costo incluye la configuración inicial y el sistema mensual. ¿Le gustaría proceder con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Para proceder, por favor, compártame su nombre y número de teléfono.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora necesito su número de teléfono para completar el proceso de activación.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque le permite responder rápidamente y mantener seguimiento constante, evitando que se enfríen las oportunidades de venta.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye prioridad en soporte. Si desea, puedo ayudarle a determinar cuál se adapta mejor a sus necesidades.

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes y luego COP 110.000 mensuales. ¿Me puede proporcionar su nombre y teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, por favor compárteme su nombre y teléfono.

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y un asistente conversacional inteligente. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Para proceder, por favor compárteme su nombre y teléfono.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora, por favor, compárteme tu número de teléfono para completar el registro.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque automatiza respuestas y seguimiento, ayudando a no perder ventas.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, tenemos el Plan Pro, que ofrece soporte prioritario. Si está interesado, puedo ayudarle a ver cuál se adapta mejor a sus necesidades.

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes, y luego COP 110.000 mensuales. ¿Me puede proporcionar su nombre y teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes, de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados. Solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puede compartir su nombre y teléfono para continuar con la activación?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial y un asistente conversacional inteligente. ¿Le gustaría proceder con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Excelente decisión. Por favor, compártame su nombre y teléfono para continuar con la activación del Plan Básico.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Por favor, también compártame su número de teléfono para completar el proceso de activación.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque automatiza respuestas y seguimiento, evitando que pierda clientes por demoras.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, también ofrecemos el Plan Pro, que incluye soporte prioritario. Si está interesado, puedo ayudarle a ver cuál se adapta mejor a sus necesidades.

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Me puede dar su nombre y teléfono para continuar?

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes, de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados, solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Me puede dar su nombre y número de teléfono para continuar con el proceso?

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Este plan incluye configuración inicial y asistente conversacional inteligente. ¿Le gustaría avanzar con la activación?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Excelente decisión. Por favor, indíqueme su nombre y número de teléfono para continuar con el proceso de activación.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. ¿Cuál es su número de teléfono para completar el proceso de activación?

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque automatiza respuestas y seguimiento, ayudando a no perder clientes por demoras.

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, tenemos el Plan Pro, que ofrece prioridad en soporte y más funcionalidades. ¿Le gustaría saber más sobre cómo el Plan Pro puede ayudarle?

### asesor_ai_prod · pregunta el horario

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye la configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes. Para avanzar, por favor, indíqueme su nombre y teléfono.

**[2] Cliente:** ¿En qué horario atienden?

**[2] Asesor:** Atendemos de lunes a viernes de 08:00 a 17:00. ¿Le gustaría avanzar con el Plan Básico?

**[3] Cliente:** ¿Y el sábado abren?

**[3] Asesor:** No atendemos los sábados. Solo de lunes a viernes. ¿Le gustaría avanzar con el Plan Básico?

### asesor_ai_prod · decide comprar

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, necesito su nombre y teléfono.

**[2] Cliente:** ¿Cuánto cuesta Plan Basico?

**[2] Asesor:** El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Esto incluye la configuración inicial y el asistente conversacional inteligente. ¿Le gustaría proceder?

**[3] Cliente:** Me convence, lo quiero

**[3] Asesor:** Perfecto. Para proceder, por favor, compártame su nombre y teléfono.

**[4] Cliente:** Me llamo Ana

**[4] Asesor:** Gracias, Ana. Ahora necesito su número de teléfono para continuar con el proceso de activación.

### asesor_ai_prod · pide que le cuente todo

**[1] Cliente:** Hola, cuéntame todo sobre Plan Basico: qué incluye, cómo funciona y por qué me conviene

**[1] Asesor:** El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Le conviene porque automatiza respuestas y seguimiento, ayudando a recuperar ventas perdidas. ¿Cuántos mensajes recibe normalmente?

**[2] Cliente:** ¿Y qué más tienen?

**[2] Asesor:** Además del Plan Básico, ofrecemos el Plan Pro, que incluye prioridad en soporte. Si busca más funcionalidades, el Plan Pro podría ser una buena opción. ¿Le gustaría saber más sobre este plan?
