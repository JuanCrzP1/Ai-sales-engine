# Estándar del asesor: sin_reglas_pagos_b_20261120

**NO PASA** · código `66adbb9 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 60 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 60 de 60 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 60 de 60 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 60 de 60 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 60 de 60 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 60 de 60 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 60 de 60 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 60 de 60 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 60 de 60 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 60 de 60 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ❌ responde lo que preguntan (juez) | 58 de 60 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 59 de 60 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 60 de 60 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 60 de 60 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 56 de 60 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 60 de 60 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 60 de 60 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 60 de 60 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0769 · juez USD 0.0264. Llamadas al modelo por mensaje: 2.08. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 26.

Por cada mensaje del cliente: responde en 3.2 s (el 5 % más lento, 4.9 s o más) · USD 0.4 por cada 1.000 mensajes · fuera de formato: 0 de 192 · sin respuesta de la IA: 1 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **responde lo que preguntan** · restaurant · el chat de producción · turno 3: Ignora la pregunta del cliente sobre si puede transferir.
  - Cliente: «Y puedo trasferir»
  - Asesor: «Perfecto, entonces vamos con la Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar una bebida? Te recuerdo que la gaseosa cuesta COP 5.000 y el jugo natural COP 7.000.»
- **responde lo que preguntan** · restaurant · da su teléfono antes de pagar · turno 2: El asesor no respondió cómo pagar, que fue la pregunta del cliente.
  - Cliente: «Mi número es 3157778899, ¿cómo hago para pagarte?»
  - Asesor: «Genial, solo necesito que me digas la dirección de entrega y si quieres añadir algo más, como una gaseosa o un jugo natural.»
- **no pide lo ya dado** · restaurant · el chat de producción · turno 10: El asesor pide el teléfono que el cliente ya dio.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame tu dirección de entrega y tu número de teléfono para completar el pedido. ⏎  ⏎ Datos para Nequi: ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: No explica qué debe hacer, solo repite que enviará los datos.
  - Cliente: «Cómo así»
  - Asesor: «Te compartí los datos para pagar por Nequi, pero parece que no están visibles. Si quieres, puedo enviarte los datos nuevamente para que puedas realizar el pago. ¿Te gustaría que lo haga?»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: El asesor repite la misma información sin explicar con otras palabras.
  - Cliente: «Cómo así»
  - Asesor: «Te envié los datos para pagar por Nequi arriba. Solo necesitas hacer el pago y enviarme la captura del comprobante. ¿Cuántas Hamburguesas Sencillas deseas pedir y quieres añadir alguna bebida?»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: El asesor no explica, solo repite que los datos están arriba.
  - Cliente: «Cómo así»
  - Asesor: «Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: Repite la misma información sin explicar 'cómo así'.
  - Cliente: «Cómo así»
  - Asesor: «Te envié los datos para pagar por Nequi, pero si necesitas que te los repita, no dudes en decirme. Solo necesito que me confirmes tu dirección de entrega para seguir con el pedido.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el primer mes de servicio. Luego, se paga COP 110.000 mensualmente. Para avanzar, necesito tu nombre, teléfono y detalles para la implementación.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes pagar por transferencia. Ahora, por favor, compárteme tu nombre, teléfono y detalles para la implementación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Ahora, por favor, compárteme tu nombre, teléfono y detalles para la implementación.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Para finalizar, ¿prefieres pagar con Nequi o transferencia? Así te envío los detalles.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Una vez realices el pago, avísame para activar tu Plan Básico y comenzar con la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Te dejo los datos para pagar por Nequi. Una vez realices el pago, avísame con la captura del comprobante para activar tu Plan Básico y comenzar con la implementación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez realices el pago, me envías aquí la captura del comprobante. Con eso, procederemos a activar tu Plan Básico y comenzaremos con la implementación.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí tienes de nuevo los datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅  
  
Recuerda enviarme la captura del comprobante una vez realices el pago.

**[11] Cliente:** Cómo así

**[11] Asesor:** Te compartí los datos para pagar por Nequi, pero parece que no están visibles. Si quieres, puedo enviarte los datos nuevamente para que puedas realizar el pago. ¿Te gustaría que lo haga?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, haz el pago y luego envíame aquí la captura del comprobante. Así procederemos con la activación de tu Plan Básico.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en el Plan Básico y desea pagar por Nequi. Dijo que ya realizó la consignación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu teléfono y los detalles para completar la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también necesito que me compartas tu teléfono para completar la activación.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, por favor, dame tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, confirma tu nombre y detalles de tu negocio para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Para proceder, necesito tu nombre, teléfono y un correo electrónico. ¿Me los puedes proporcionar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre, teléfono y correo electrónico para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El costo es de COP 210.000 para el primer mes (implementación + primer mes) y luego COP 110.000 mensuales. ¿Me puedes proporcionar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos medios prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el sistema mensual. Luego, se paga COP 110.000 cada mes. ¿Me puedes compartir tu nombre, teléfono y cualquier detalle adicional necesario para continuar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos de pago para continuar con el Plan Básico?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo ahora mismo para que puedan ayudarte.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles para la implementación. ¿Me los compartes?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Mencionó que le interesa el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer pago mensual. Luego, son COP 110.000 cada mes. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Para la transferencia a Bancolombia, puedes hacerla con los siguientes datos:  
  
- Nombre: Asesor Comercial  
  
¿Me puedes confirmar tu nombre, teléfono y detalles para completar el proceso?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico es una excelente elección. Incluye configuración inicial y un asistente conversacional inteligente. Para continuar, necesito tus datos: nombre, teléfono y detalles de tu negocio. ¿Me los puedes compartir?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Ahora, por favor, comparte tu nombre, teléfono y detalles de tu negocio para completar la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos de pago para que puedas proceder con la transferencia?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. El primer mes cuesta COP 210.000 (incluye la implementación y el primer mes). ¿Te gustaría que te envíe los datos de pago para que puedas hacer la transferencia?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora, por favor, realiza el pago a través de Nequi y envíame la captura del comprobante para continuar con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago y me envíes la captura del comprobante, procederemos a activar tu servicio y te guiaré en la configuración inicial. ¡Así podrás empezar a aprovecharlo de inmediato!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Aquí tienes nuevamente los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, Juan Camilo. Una vez realices el pago y me envíes la captura del comprobante, activaremos tu servicio y te guiaré en la configuración inicial. ¡Espero tu mensaje!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Informó que ya realizó la consignación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Excelente elección, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 en el primer mes. Luego, solo COP 110.000 mensuales. ¿Me puedes compartir tu número de teléfono para continuar con el proceso?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, confirma el número de teléfono que quieres usar para el registro.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Perfecto! El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Son COP 100.000 de implementación y COP 110.000 al mes. Para avanzar, necesito tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Cuál es tu nombre y los detalles de tu negocio para completar el registro antes de enviarte los datos de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Recuerda enviarme el nombre y los detalles de tu negocio para completar el registro.  
  
Datos de pago:  
- Nombre: Asesor Comercial  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes (incluye implementación y sistema) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para empezar con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Recuerda que el primer mes es COP 210.000.  
  
¿Cuál es tu nombre y teléfono para continuar con la activación?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer mes de servicio. Luego, pagas COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para proceder?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 al mes). Para continuar, necesito tu nombre, teléfono y un correo electrónico.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 al mes). ¿Me puedes dar tu nombre y número de teléfono para continuar con la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí están los datos para hacer la transferencia a Bancolombia (ahorros). Cuando realices el pago, confirma para activar tu servicio.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer pago mensual. Luego, son COP 110.000 al mes. Para continuar, necesito tus datos: nombre, teléfono y detalles. ¿Me los compartes?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes pagar por transferencia a Bancolombia. Ahora, por favor, dime tu nombre, teléfono y detalles para avanzar con la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos de pago por ese medio? También necesito tu nombre, teléfono y detalles para continuar.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora que tengo tus datos, procederé a enviarte los datos de pago para Nequi. ¿Listo para iniciar?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, realiza el pago y avísame cuando lo hayas hecho para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora, por favor, realiza el pago por Nequi y envíame la captura del comprobante para continuar con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez realices el pago, solo envíame la captura del comprobante aquí. Con eso, procederemos a activar tu sistema y te guiaré en la configuración inicial.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Aquí te dejo de nuevo los datos para pagar por Nequi. Por favor, realiza el pago y avísame cuando lo hayas hecho para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, hazlo cuando estés listo. Avísame cuando hayas realizado el pago y me envías la captura del comprobante.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con la activación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Esto te ayudará a responder rápido y mantener el seguimiento con tus clientes. ¿Me puedes dar tu número de teléfono para avanzar con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, confirma tu número de teléfono para completar la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes, que incluye la implementación y el primer pago mensual. Luego, pagarás COP 110.000 al mes. ¿Me puedes dar tu nombre y número de teléfono para continuar con la activación?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ¿con cuál de los siguientes medios de pago prefieres hacerlo: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer mes de servicio. Luego, pagas COP 110.000 mensuales. Para continuar, necesito tu nombre, teléfono y detalles sobre tu negocio.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre, teléfono y detalles sobre tu negocio para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes, que incluye la configuración inicial y el sistema mensual. Luego, pagarás COP 110.000 cada mes. ¿Me puedes dar tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer mes de servicio. Luego, se paga COP 110.000 mensualmente. ¿Me puedes dar tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos pagos por Nequi. ¿Te gustaría que te envíe los datos para el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que puedan atenderte directamente.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente. El primer mes cuesta COP 210.000, que incluye la implementación y el primer mes de servicio. Para avanzar, necesito tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Me los puedes dar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Para proceder con la transferencia, aquí tienes los datos:  
- Monto total: COP 210.000 (implementación + primer mes)  
  
¿Me puedes confirmar tu nombre y teléfono para completar el registro?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te envíe los datos de pago? También necesito saber cuántas hamburguesas quieres.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría pagar con ese medio? Y, ¿cuántas Hamburguesas Sencillas te gustaría pedir?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Cuántas Hamburguesas Sencillas quieres pedir? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me confirmes cuántas Hamburguesas Sencillas deseas y si quieres añadir una gaseosa o un jugo natural.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. ¿Cuántas Hamburguesas Sencillas deseas pedir y quieres añadir alguna bebida?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: primero haces el pago con los datos que te envié arriba y luego me envías aquí la captura del comprobante. Después de eso, confirmamos tu pedido y te pido la dirección de entrega.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí están los datos para pagar por Nequi. Solo recuerda que necesito que me confirmes cuántas Hamburguesas Sencillas deseas y si quieres añadir una bebida.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos para pagar por Nequi arriba. Solo necesitas hacer el pago y enviarme la captura del comprobante. ¿Cuántas Hamburguesas Sencillas deseas pedir y quieres añadir alguna bebida?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando realices el pago, por favor envíame la captura del comprobante. También necesito que me confirmes cuántas Hamburguesas Sencillas quieres y si deseas añadir una bebida.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita hacer un pedido de Hamburguesa Sencilla. Está interesado en pagar por Nequi y ya realizó el pago.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto, Laura! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu dirección de entrega y tu teléfono para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante. Con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida, como gaseosa o jugo natural?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago, puedes usar Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál prefieres? También necesito tu nombre y dirección para completar el pedido.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también necesito tu nombre y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial elección, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo como una gaseosa o un jugo natural?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, dime tu nombre, teléfono y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la enviamos?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Antes de enviarte los datos de pago, ¿con cuál de los medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Genial! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál de estos métodos prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como forma de pago. ¿Te gustaría confirmar tu pedido de la Hamburguesa Sencilla y agregar alguna bebida?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres recibirlo: a domicilio o para recoger en el local?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te voy a pasar con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia y lamento lo que ha pasado. Voy a pasar tu reclamo al equipo para que puedan ayudarte con esto.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). ¿Me puedes dar tu nombre, teléfono y dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido? También puedes agregar una bebida si lo deseas.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Claro, puedes pagar por transferencia. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 a tu pedido?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como medio de pago. ¿Te gustaría agregar una bebida a tu pedido de la Hamburguesa Sencilla?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 a tu Hamburguesa Sencilla?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame tu dirección de entrega y tu número de teléfono para completar el pedido.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo falta tu dirección de entrega para completar el pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: después de que hagas el pago por Nequi, solo envíame aquí la captura del comprobante. Así seguimos con tu pedido. ¿Listo para darme tu dirección?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame tu dirección de entrega y tu número de teléfono para completar el pedido.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, avísame cuando hayas hecho el pago y me envíes la captura del comprobante. También necesito tu dirección de entrega para completar el pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en pedir una Hamburguesa Sencilla y prefiere pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con su pedido.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar tu pedido, necesito tu dirección de entrega y tu teléfono. ¿Me los compartes?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la enviamos?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Genial, solo necesito tu nombre y la dirección de entrega para confirmar el pedido. Luego te digo cómo puedes pagar.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu nombre y la dirección de entrega para completar el pedido.  
  
Datos para Nequi:  
- **Cantidad:** COP 18.000 (Hamburguesa Sencilla)  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre, teléfono y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo como una gaseosa o un jugo natural?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres hacerlo: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos pagos por Nequi. ¿Te gustaría confirmar tu pedido y te envío los datos para el pago?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con alguien del equipo para que te ayude.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento que estés pasando por esto. Te paso con el equipo para que puedan ayudarte con tu reclamo y resolverlo lo antes posible.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde. Quiere que lo atiendan para resolver su reclamo.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la enviamos?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). ¿Me puedes dar tu nombre, teléfono y dirección para el envío?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, entonces vamos con la Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar una bebida? Te recuerdo que la gaseosa cuesta COP 5.000 y el jugo natural COP 7.000.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría agregar una bebida a tu pedido antes de continuar?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Te gustaría agregar una bebida a tu Hamburguesa Sencilla? La gaseosa cuesta COP 5.000 y el jugo natural COP 7.000.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
- Monto: COP 18.000 (Hamburguesa Sencilla)  
  
Por favor, confírmame tu dirección de entrega y tu número de teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿me puedes confirmar tu dirección de entrega para completar el pedido?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me confirmes tu dirección, te explicaré el siguiente paso. Haces el pago por Nequi y me envías la captura del comprobante. Así podremos continuar con tu pedido.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** ¡Claro! Tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
- Monto: COP 18.000 (Hamburguesa Sencilla)  
  
Por favor, confírmame tu dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos para pagar por Nequi, pero si necesitas que te los repita, no dudes en decirme. Solo necesito que me confirmes tu dirección de entrega para seguir con el pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, haz el pago por Nequi y, cuando lo tengas, envíame la captura del comprobante. Así seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y está interesado en hacer un pedido de una Hamburguesa Sencilla por COP 18.000. Ha mencionado que ya realizó el pago por Nequi.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir algo para beber, como una gaseosa o un jugo natural?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me confirmes tu dirección de entrega y tu teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Genial, solo necesito que me digas la dirección de entrega y si quieres añadir algo más, como una gaseosa o un jugo natural.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito la dirección de entrega y confirmamos el pedido.  
  
Datos para Nequi:  
- Nombre: Mesa Activa  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la envío?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu dirección y teléfono para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres hacer la consignación: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y deseas agregar alguna bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres recibirlo: a domicilio o recogiendo en el local?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos de pago para tu pedido?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo más, como una gaseosa o un jugo natural?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te voy a pasar con el equipo para que puedan ayudarte con el cobro y resolver tu inquietud.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Quiere que lo ayuden con el cobro.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). ¿Me puedes dar tu nombre, teléfono y dirección para la entrega?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
