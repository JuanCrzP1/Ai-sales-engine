# Estándar del asesor: sin_reglas_pagos_20261120

**NO PASA** · código `66adbb9 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 90 conversaciones (3 muestras por negocio: asesor_ai_prod, clinic, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 90 de 90 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 90 de 90 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 90 de 90 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 90 de 90 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 90 de 90 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 90 de 90 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 89 de 90 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 90 de 90 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 90 de 90 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ❌ responde lo que preguntan (juez) | 89 de 90 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 90 de 90 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 90 de 90 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ❌ no dice nada falso del pago (juez) | 88 de 90 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 86 de 90 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 90 de 90 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 90 de 90 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 90 de 90 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.1113 · juez USD 0.0384. Llamadas al modelo por mensaje: 2.07. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 45.

Por cada mensaje del cliente: responde en 3.0 s (el 5 % más lento, 4.5 s o más) · USD 0.39 por cada 1.000 mensajes · fuera de formato: 0 de 288 · sin respuesta de la IA: 4 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **no repite la respuesta** · restaurant · el chat de producción · turno 4: repitió la respuesta anterior
  - Cliente: «Y Nequi no»
  - Asesor: «Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.»
- **responde lo que preguntan** · restaurant · el chat de producción · turno 3: Ignora la pregunta del cliente sobre transferencia.
  - Cliente: «Y puedo trasferir»
  - Asesor: «Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.»
- **responde lo que preguntan** · restaurant · el chat de producción · turno 4: Ignora la pregunta del cliente sobre Nequi.
  - Cliente: «Y Nequi no»
  - Asesor: «Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.»
- **no dice nada falso del pago** · restaurant · el chat de producción · turno 11: El asesor dice que no puede enviar los datos de pago.
  - Cliente: «Cómo así»
  - Asesor: «Te pido disculpas, pero no puedo enviar los datos de pago de nuevo. Te los dejé arriba en el chat. ¿Cuántas Hamburguesas Sencillas deseas pedir y cuál es tu dirección de entrega?»
- **no dice nada falso del pago** · restaurant · el chat de producción · turno 11: El asesor dice que no puede enviar los datos de pago.
  - Cliente: «Cómo así»
  - Asesor: «Lo siento, no puedo enviar los datos de pago de nuevo. Pero si quieres, puedo guiarte en el proceso de pago. ¿Te gustaría que te explique cómo hacerlo?»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: El cliente dice que no entendió y el asesor no explica.
  - Cliente: «Cómo así»
  - Asesor: «Te pido disculpas, pero no puedo enviar los datos de pago de nuevo. Te los dejé arriba en el chat. ¿Cuántas Hamburguesas Sencillas deseas pedir y cuál es tu dirección de entrega?»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: Repite la misma frase sin explicar con otras palabras.
  - Cliente: «Cómo así»
  - Asesor: «Te explico: arriba, en este chat, te dejé los datos para pagar. Haz el pago y me envías aquí la captura del comprobante; con eso seguimos.»
- **explica cuando no entienden** · restaurant · se presenta al empezar · turno 3: El cliente no entendió y el asesor no le explicó.
  - Cliente: «¿Y ahora qué sigue?»
  - Asesor: «Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: El cliente dice que no entendió y el asesor no explica.
  - Cliente: «Cómo así»
  - Asesor: «Lo siento, no puedo enviar los datos de pago de nuevo. Pero si quieres, puedo guiarte en el proceso de pago. ¿Te gustaría que te explique cómo hacerlo?»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico incluye la configuración inicial y el asistente conversacional inteligente por COP 210.000 el primer mes, que cubre la implementación y el primer pago mensual. ¿Me puedes compartir tu nombre y número de teléfono para avanzar con la activación?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Solo necesito tu nombre y número de teléfono para completar el proceso de activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Si prefieres ese medio, sólo necesito tu nombre y número de teléfono para avanzar con la activación.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora, para completar la activación del Plan Básico, ¿prefieres pagar por Nequi o por transferencia a Bancolombia?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, realiza la transferencia y confirma cuando lo hayas hecho para activar tu servicio. ¡Gracias!  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ya tengo tu información. Realiza el pago por Nequi y envíame la captura del comprobante para activar tu servicio. ¡Espero tu confirmación!

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que me envíes la captura del comprobante, procederé a activar tu servicio y te enviaré la guía de configuración para que empieces a usarlo. ¡Espero tu confirmación!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi nuevamente.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la activación del servicio. ¡Gracias!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó la consignación y está esperando la confirmación para continuar con la activación del servicio.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 (implementación + suscripción) y luego COP 110.000 mensuales. ¿Te gustaría que te envíe los datos de pago para comenzar?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, envíame tu número de teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración inicial y el sistema mensual) y luego COP 110.000 cada mes. Para proceder, necesito tu nombre, teléfono y detalles. ¿Me los puedes proporcionar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ¿con cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Una vez que realices el pago, por favor confírmame. También necesito tu nombre y cualquier detalle adicional que quieras agregar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 en el primer mes (100.000 de implementación + 110.000 mensual). Luego, solo son COP 110.000 al mes. ¿Me puedes dar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dame tu nombre y teléfono para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Para proceder, necesito tu nombre, teléfono y detalles que consideres importantes.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres hacer la consignación: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial elección! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Me los puedes compartir?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o con un link de pago. ¿Cuál de estos prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes, que cubre la implementación y el primer pago mensual, y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Me los puedes proporcionar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Mencionó que le interesa el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial y el sistema mensual. Son COP 100.000 de implementación y COP 110.000 al mes. Para continuar, necesito tu nombre, teléfono y detalles de tu negocio. ¿Cómo te gustaría pagar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Si tienes alguna duda, no dudes en preguntar. ¿Te gustaría que te ayude con algo más?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (implementación + primer mes). Luego, pagarás COP 110.000 mensualmente. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder con la activación?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes transferir. Solo necesito tu nombre, teléfono y detalles para activar el servicio.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como medio de pago. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Para activar el Plan Básico, ¿prefieres pagar por Nequi o transferencia?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, realiza el pago de COP 210.000 (implementación + primer mes) y me avisas cuando lo hayas hecho.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora solo espera la captura del comprobante del pago para continuar con la activación del servicio. ¡Estoy aquí para ayudarte!

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando me envíes la captura del comprobante, procederemos a configurar tu sistema. Te guiaré paso a paso para que todo quede listo para que empieces a aprovecharlo.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** ¡Claro! Tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Aquí tienes de nuevo los datos para pagar por Nequi:  
  
Realiza el pago de COP 210.000 (implementación + primer mes) y me avisas cuando lo hayas hecho.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Para activar el Plan Básico, debes realizar un pago de COP 210.000, que incluye la implementación y el primer mes. Después, me envías la captura del comprobante de pago, y yo te guío con la configuración del sistema.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu captura del comprobante para continuar con la configuración del sistema.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con la configuración del sistema.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Te gustaría que te envíe los datos para el pago?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu número de teléfono y un correo electrónico. ¿Me los puedes compartir?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Me compartes tu nombre y teléfono para proceder con la activación?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ¿con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial elección! El Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, dame tu nombre y teléfono para completar el proceso.  
  
Datos para Nequi:  
- Nombre: Asesor Comercial  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 en el primer mes (implementación + primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Listo para comenzar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál de estos prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para que puedas realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial y el asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Para comenzar, necesito tu nombre, teléfono y detalles para la implementación. ¿Me los puedes proporcionar?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con alguien del equipo para que puedan ayudarte. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial elección! El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta 210.000 COP (100.000 COP de implementación + 110.000 COP del primer mes) y luego 110.000 COP mensuales. ¿Me puedes dar tu nombre y teléfono para avanzar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y algunos detalles para continuar con la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para realizar la transferencia a Bancolombia (ahorros). ¿Me compartes tu nombre y teléfono para completar la activación?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (implementación + primer mes), luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes transferir. Solo necesito tu nombre y teléfono para completar la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Me das tu nombre y teléfono para continuar con la activación?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora, ¿prefieres pagar con Nequi o transferencia? Te ayudo a completar el proceso.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Una vez que realices el pago, confírmame para activar tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Una vez realices el pago por Nequi, envíame aquí la captura del comprobante y procederemos con la activación de tu Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, solo envíame aquí la captura del comprobante. Con eso, procederemos a activar tu Plan Básico y te guiaré en la configuración.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi nuevamente.  
  
Una vez que realices el pago, confírmame para activar tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la activación del Plan Básico. ¡Quedo atento!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con la activación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico cuesta COP 210.000 en total el primer mes, que incluye la implementación y el primer mes de servicio. Luego, se paga COP 110.000 mensualmente. ¿Me puedes dar tu teléfono para continuar con el proceso?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu teléfono para finalizar la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000, que incluye la configuración inicial y el primer mes. Luego, pagarás COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para activar el servicio?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Cuál medio de pago prefieres? Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Me los compartes?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente elección! El Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y algún detalle adicional para avanzar con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye configuración y primer mes) y luego COP 110.000 mensuales. Este plan te ayudará a automatizar respuestas y mantener seguimiento constante con tus clientes. Para proceder, necesito tu nombre, teléfono y el medio de pago que prefieres.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente para automatizar tus respuestas. El primer mes cuesta 210.000 COP, que incluye la implementación y el primer mes de servicio. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para proceder con el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial y el asistente conversacional inteligente por COP 210.000 el primer mes (que incluye la implementación y el primer mes de servicio). Luego, se paga COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Voy a pasarte con una persona del equipo que te podrá ayudar.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Para avanzar, necesito tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el primer mes de servicio. Luego, se paga mensualmente COP 110.000. Para avanzar, necesito tu nombre, teléfono y detalles de tu negocio.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, confirma tu nombre, teléfono y detalles de tu negocio para completar el registro.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Genial! Para empezar con Agenda Plus, necesito algunos datos. ¿Cuál es tu nombre y número de teléfono? También, ¿qué día y hora te gustaría agendar?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. Ahora, solo necesito tu nombre y número de teléfono, y el día y hora que prefieres para agendar.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te enviara los datos de pago por ese medio?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora necesito que me digas qué día y hora te gustaría agendar para comenzar con Agenda Plus.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame también qué día y hora te gustaría agendar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo necesito que me digas qué día y hora te gustaría agendar para comenzar con Agenda Plus.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: después de hacer el pago, me envías aquí la captura del comprobante. Con eso, coordinamos el día y hora para agendarte en Agenda Plus. ¿Qué día y hora te gustaría agendar?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Cuando hagas el pago, envíame la captura del comprobante y podemos coordinar el día y hora para agendarte.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hagas el pago, envíame la captura del comprobante. Luego coordinamos el día y hora para tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en coordinar una cita para empezar con Agenda Plus. Mencionó que ya realizó un pago por Nequi.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Agenda Plus te ayuda a gestionar y confirmar citas con tus pacientes. Tiene un costo de COP 140.000 por implementación y COP 170.000 al mes. ¿Te gustaría agendar una cita para hablar más sobre cómo funciona?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me confirmes el día y la hora que prefieres para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye la gestión y confirmación de citas. Su costo es de COP 140.000 de implementación más COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago, puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres utilizar?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito tu nombre y el día y hora que prefieres para agendar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Perfecto! Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, compárteme tu nombre, teléfono y cuándo te gustaría empezar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 mensuales. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres. ¿Cuál sería tu disponibilidad?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos medios prefieres utilizar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! La Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita: día y hora que prefieres.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos de pago cuando estemos listos para agendar?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude con Agenda Plus.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y solicitó hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Excelente elección con Agenda Plus. Para agendar tu cita, necesito tu nombre, teléfono y cuándo te gustaría que te contactemos para confirmar el día y la hora.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde. Está interesado en el producto Agenda Plus.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Excelente elección. Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres. ¡Vamos a coordinarlo!

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, puedes realizar la transferencia a Bancolombia (ahorros). Ahora, por favor, confírmame tu nombre y teléfono, así como el día y hora que prefieres para agendar.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Genial! Para empezar con Agenda Plus, necesito tus datos. ¿Cuál es tu nombre y número de teléfono? También cuéntame qué día y hora te gustaría coordinar.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes realizar el pago a través de transferencia a Bancolombia, Nequi, Daviplata, Bre-B o mediante un link de pago. ¿Cuál medio prefieres usar?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, puedes pagar con Nequi. ¿Te gustaría que te enviara los datos de pago para continuar con el proceso?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. ¿Qué día y hora te gustaría coordinar para empezar con Agenda Plus?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo falta que me envíes la captura del comprobante de pago por Nequi, y con eso seguimos.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me envíes la captura del comprobante, podemos coordinar el día y la hora para activar tu Agenda Plus. ¡Espero tu mensaje!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** ¡Claro, tómate tu tiempo!

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando termines, solo envíame la captura del comprobante y seguimos con la coordinación de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita coordinar una cita para empezar con Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Incluye gestión y confirmación de citas, lo que te ayudará a agendar más y ordenar tu disponibilidad. ¿Te gustaría agendar una cita para más detalles?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** Para agendar, necesito que me des tu teléfono y el día y la hora que prefieres para la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Perfecto! Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para continuar, necesito tu nombre, teléfono y qué día y hora prefieres para agendar.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago, puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre y qué día y hora prefieres para agendar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Excelente elección. La Agenda Plus tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieras. ¿Cuándo te gustaría empezar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también necesito tu nombre, teléfono y el día y hora que prefieras para la Agenda Plus.  
  
Datos de pago:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Cuál es tu disponibilidad?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios te gustaría pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Agenda Plus incluye la gestión y confirmación de citas. Para proceder, necesito tu nombre, número de teléfono y que me digas qué día y hora te gustaría agendar tu cita.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos medios prefieres utilizar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Me puedes dar esos datos?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos para pagar una vez que agendemos la cita?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación más COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres para la cita.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude con Agenda Plus. Ellos te atenderán enseguida por aquí.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y solicitó hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, la Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Te gustaría que te enviara los datos de pago?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Para activar Agenda Plus, necesito algunos datos: tu nombre, teléfono y qué día y hora te gustaría agendar la cita. ¿Me los puedes proporcionar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, puedes realizar la transferencia a Bancolombia (ahorros). Ahora, por favor, dame tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Perfecto! Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres. El servicio incluye gestión y confirmación de citas.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar mediante transferencia a Bancolombia. Ahora, dime tu nombre, teléfono y el día y hora que prefieres para agendar.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos de pago o prefieres continuar con la agenda?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora, por favor indícame tu número de teléfono y el día y hora que prefieres para agendar la cita.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame el día y hora que prefieres para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora necesito que me digas qué día y hora prefieres para agendar la cita.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez hagas el pago, me envías aquí la captura del comprobante. Con eso, podremos confirmar la cita. ¿Listo para avanzar?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo nuevamente los datos para pagar por Nequi. Por favor, indícame el día y hora que prefieres para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la agendación de la cita. ¿Tienes ya el día y la hora en mente?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita coordinar una cita para el servicio Agenda Plus. Está interesado en pagar por Nequi y ya realizó la consignación.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Incluye gestión y confirmación de citas, lo que te ayudará a organizar mejor tu agenda y no perder pacientes. ¿Te gustaría agendar una cita para más detalles?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me confirmes tu número de teléfono y el día y hora que prefieres para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente elección! Agenda Plus incluye gestión y confirmación de citas. Para agendar tu cita, necesito tu nombre, teléfono y qué día y hora prefieres. El equipo te confirmará la disponibilidad.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, para el pago puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ahora, por favor, indícame tu nombre y qué día y hora prefieres para que el equipo te confirme.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, la Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría que confirmemos la cita.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dame tu nombre, teléfono y cuándo te gustaría que confirmemos la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y una fecha y hora que te acomode. ¿Cuál prefieres?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Me puedes dar esos datos?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Excelente elección. La Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar. ¿Tienes ya un día y hora en mente?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. Si decides avanzar, puedo enviarte los datos para completar el pago. ¿Te gustaría continuar con la Agenda Plus?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su implementación cuesta COP 140.000 y el mensual COP 170.000. Para agendar, necesito tu nombre, teléfono y un día y hora que te acomoden. ¿Cuál prefieres?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y la fecha y hora que prefieres.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus te ayudará a gestionar y confirmar citas de manera efectiva. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar. ¿Tienes alguna fecha en mente?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia (ahorros). Ahora, por favor, compárteme tu nombre y número de teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres pedir y para cuántas personas es el pedido?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Cuántas Hamburguesas Sencillas deseas pedir?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como medio de pago. ¿Cuántas Hamburguesas Sencillas deseas pedir?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Cuántas Hamburguesas Sencillas deseas pedir?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas vas a pedir y cuál es tu dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. ¿Cuántas Hamburguesas Sencillas deseas pedir y cuál es tu dirección de entrega?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez realices el pago por Nequi, me envías aquí la captura del comprobante. Con eso, seguimos para confirmar tu pedido y organizar la entrega.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí te dejo nuevamente los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas vas a pedir y cuál es tu dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te pido disculpas, pero no puedo enviar los datos de pago de nuevo. Te los dejé arriba en el chat. ¿Cuántas Hamburguesas Sencillas deseas pedir y cuál es tu dirección de entrega?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que hagas el pago, envíame la captura del comprobante. También necesito saber cuántas Hamburguesas Sencillas deseas pedir y tu dirección de entrega para organizar todo.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en pedir Hamburguesa Sencilla y desea pagar por Nequi. Mencionó que ya realizó la consignación.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu dirección de entrega y tu teléfono para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla. ¿Para cuántas personas necesitas el pedido? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, para el pago, ¿prefieres usar Nequi, Daviplata, transferencia a Bancolombia o Bre-B? También necesito tu nombre y dirección para completar el pedido.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. También necesito tu nombre y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y prefieres que te la enviemos a domicilio o la recoges en el local?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, solo necesito tu número de teléfono y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla a COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la enviamos?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacerlo: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la enviamos?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría confirmar tu pedido de la Hamburguesa Sencilla y agregar una bebida?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla a COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la enviamos?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación que estás viviendo. Te voy a pasar con el equipo para que puedan ayudarte con el cobro doble. Ellos te atenderán aquí mismo.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde. Quiere que lo atiendan para resolver el problema del cobro doble.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida, como gaseosa o jugo natural?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, para la transferencia a Bancolombia (ahorros) te dejo los datos de pago a continuación:  
  
Por favor, confirma el nombre, teléfono y dirección de entrega para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar una bebida, como una gaseosa (COP 5.000) o un jugo natural (COP 7.000)?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Perfecto, Juan Camilo. Entonces, para tu pedido de la Hamburguesa Sencilla, ¿quieres agregar una bebida, como una gaseosa o un jugo natural?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Me podrías dar tu dirección de entrega y tu número de teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo me falta tu dirección de entrega para completar el pedido.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Haz el pago y me envías aquí la captura del comprobante.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haz el pago y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando tengas el comprobante, envíamelo aquí y seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo necesita hacer un pedido de Hamburguesa Sencilla y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con su pedido.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una bebida para acompañar tu pedido, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Me puedes dar tu dirección de entrega y tu teléfono para finalizar el pedido?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Te gustaría añadir una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Cuál de los siguientes medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. También necesito que me des tu nombre y la dirección de entrega para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde la enviamos?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes usar Nequi, Daviplata, transferencia a Bancolombia o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Excelente elección. ¿Te gustaría agregar una gaseosa (COP 5.000) o un jugo natural (COP 7.000) para acompañar tu hamburguesa?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría añadir algo más a tu pedido?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, ¿quieres agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa sencilla?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con alguien del equipo para que te ayude.

*[2] Nota para el equipo:* El cliente quiere una hamburguesa sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla a COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa a COP 5.000 o un jugo natural a COP 7.000?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia y lamento la situación. Voy a pasarlo con el equipo para que puedan ayudarte con tu reclamo.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Mencionó que le cobraron dos veces y está muy molesto por la situación.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y prefieres que te la enviemos a domicilio o la recoges en el local?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, para pagar por transferencia a Bancolombia (ahorros). ¿Me puedes dar tu nombre, teléfono y dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es tu pedido? También puedes agregar una gaseosa o un jugo natural si lo deseas.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). ¿Te gustaría agregar algo más a tu pedido o confirmar solo la hamburguesa sencilla?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Quieres confirmar solo la hamburguesa sencilla o agregar algo más?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Quieres confirmar solo la Hamburguesa Sencilla o agregar algo más a tu pedido?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Perfecto, Juan Camilo. ¿Me puedes dar tu teléfono y dirección de entrega para completar el pedido?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo me falta la dirección de entrega para completar tu pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Lo siento, no puedo enviar los datos de pago de nuevo. Pero si quieres, puedo guiarte en el proceso de pago. ¿Te gustaría que te explique cómo hacerlo?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hayas realizado el pago, envíame la captura del comprobante para que sigamos con tu pedido. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo necesita hacer un pedido de comida y le interesa la Hamburguesa Sencilla. Prefiere pagar por Nequi y ya realizó el pago.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me des tu dirección de entrega y tu número de teléfono para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Perfecto! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me digas tu nombre y la dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿La quieres acompañar con algo, como una gaseosa o un jugo natural?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu número de teléfono y la dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla a COP 18.000. ¿Para cuántas personas es el pedido y prefieres que te la enviemos a domicilio o la recoges en el local?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la envío?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál de estos medios prefieres usar?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría hacer tu pedido ahora?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa a tu pedido por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo que te atenderá.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te voy a pasar con el equipo para que puedan revisar tu caso y ayudarte. Un momento, por favor.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Quiere que se revise su caso.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la envío?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia:  
  
- Transferencia a Bancolombia (ahorros).  
  
¿Me puedes dar tu nombre, teléfono y dirección para completar el pedido?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
