# Estándar del asesor: sin_reglas_pagos_c_20261120

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
| ✅ no pide lo ya dado (juez) | 60 de 60 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 60 de 60 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 60 de 60 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 57 de 60 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 60 de 60 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 60 de 60 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 60 de 60 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0762 · juez USD 0.0224. Llamadas al modelo por mensaje: 2.09. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 21.

Por cada mensaje del cliente: responde en 3.3 s (el 5 % más lento, 5.2 s o más) · USD 0.4 por cada 1.000 mensajes · fuera de formato: 0 de 192 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **responde lo que preguntan** · restaurant · el chat de producción · turno 3: Ignora la pregunta del cliente sobre transferencia.
  - Cliente: «Y puedo trasferir»
  - Asesor: «Perfecto, entonces llevas una Hamburguesa Sencilla por COP 18.000. ¿Me puedes dar tu nombre, teléfono y dirección para la entrega?»
- **responde lo que preguntan** · restaurant · el chat de producción · turno 3: Ignora la pregunta del cliente sobre si puede transferir.
  - Cliente: «Y puedo trasferir»
  - Asesor: «Perfecto, entonces confirmamos tu pedido de una Hamburguesa Sencilla. ¿Cuál es tu nombre, teléfono y dirección de entrega?»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: Repite la misma frase sin explicar con otras palabras.
  - Cliente: «Cómo así»
  - Asesor: «Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: Repite la misma información sin explicar qué significa 'cómo así'.
  - Cliente: «Cómo así»
  - Asesor: «Te envié los datos para pagar por Nequi. Solo necesito que me confirmes tu dirección para poder hacer el pedido. ¿Cuál es?»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: Repite la misma información sin explicar con otras palabras.
  - Cliente: «Cómo así»
  - Asesor: «Te envié los datos para pagar por Nequi, solo necesitas hacer el pago y luego enviarme la captura del comprobante. ¿Te gustaría que te los repita?»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Excelente decisión con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y un correo electrónico. ¿Me los puedes compartir?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Ahora, por favor, dame tu nombre, teléfono y correo electrónico para continuar con la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Ahora, por favor, compárteme tu nombre, teléfono y correo electrónico para continuar con la activación.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Tu tienda de ropa es un gran lugar para implementar el Plan Básico. Para activar, el primer mes es de COP 210.000 (incluyendo la implementación). ¿Te gustaría que te envíe los datos de pago ahora?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, completa el pago y avísame cuando lo hayas hecho para activar tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ya tengo tus datos. Completa el pago por Nequi y envíame la captura del comprobante para activar tu Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago y me envíes la captura del comprobante, procederemos a configurar tu sistema. Te guiaré en cada paso para que todo quede listo. ¡Espero tu comprobante!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí tienes de nuevo los datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante una vez completes el pago. Así avanzamos con la configuración de tu sistema.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Informó que ya realizó la consignación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el primer mes del servicio. Luego, se paga COP 110.000 mensualmente. ¿Cuáles son tus datos de contacto para continuar con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu número de teléfono y algún detalle adicional que quieras agregar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación y COP 110.000 de mensualidad). ¿Me puedes dar tu nombre, teléfono y correo para continuar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Genial, para el pago puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Recuerda que el primer mes es de COP 210.000.  
  
Por favor, dime tu nombre y correo para completar tus datos.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Perfecto! El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 en el primer mes (COP 100.000 de implementación + COP 110.000 al mes). Luego, solo pagas COP 110.000 mensuales. Para avanzar, necesito tu nombre, teléfono y detalles para la configuración. ¿Me los puedes proporcionar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Datos de pago:  
  
Por favor, compárteme tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes (incluye implementación y primer mes), y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y detalles de tu negocio para continuar con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B, o por un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para que puedas realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en total el primer mes, que incluye la implementación y el primer pago mensual. Luego, pagarás COP 110.000 cada mes. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Me los puedes compartir?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo ahora mismo para que puedan ayudarte.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Para avanzar, necesito tu nombre y teléfono. ¿Listo para continuar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y no ha recibido respuesta. Está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye la configuración inicial y el sistema mensual por COP 210.000 el primer mes, y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para la transferencia a Bancolombia:  
- Monto: COP 210.000  
- Cuenta: Ahorros  
Una vez que realices la transferencia, por favor confirma para seguir con la activación.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer pago mensual) y luego COP 110.000 al mes. Para activar el servicio, necesito tu nombre, teléfono y un correo electrónico. ¿Me los puedes proporcionar?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Claro, puedes pagar por transferencia a Bancolombia. Solo necesito tu nombre, teléfono y correo electrónico para continuar con la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Si prefieres ese medio de pago, puedo enviarte los datos cuando me des tu nombre, teléfono y correo electrónico.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Listo, Juan Camilo! Ahora te dejo los datos para pagar por Nequi.  
  
Después de que realices el pago, procederemos con la activación. ¡Gracias por confiar en nosotros!  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Perfecto, Juan Camilo. Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias por el dato, Juan Camilo. Ahora solo falta que me envíes la captura del comprobante de pago por Nequi para continuar con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me envíes la captura del comprobante, procederemos a configurar tu sistema. Te guiaré en cada paso para que todo esté listo y puedas empezar a aprovechar el asistente comercial.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Haz el pago y me envías aquí la captura del comprobante. ¡Espero tu mensaje!  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero la captura del comprobante. Una vez la tengas, seguimos con la configuración de tu sistema.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y se interesa en pagar por Nequi. Informó que ya realizó el pago.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Excelente elección, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El costo es de COP 210.000 el primer mes y luego COP 110.000 mensuales. Para avanzar, necesito tu número de teléfono y algunos detalles para la implementación. ¿Cuál medio de pago prefieres?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también confírmame tu número de teléfono para completar la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Perfecto! El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y algún detalle para continuar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago, puedes hacerlo a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos medios prefieres utilizar?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por solo COP 210,000 el primer mes, y luego COP 110,000 mensuales. ¿Me puedes dar tu nombre y teléfono para iniciar el proceso?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre y teléfono para completar el proceso:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacerlo? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me podrías dar tu nombre, teléfono y detalles para continuar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos medios prefieres usar?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial y el asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación y COP 110.000 mensual). Después, solo COP 110.000 al mes. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Me los puedes compartir?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración inicial y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y los detalles que necesitemos para continuar?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te atienda. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes), y luego COP 110.000 mensuales. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde. Está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para iniciar el proceso?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros):  
  
Nombre: Asesor Comercial  
Tipo de cuenta: Ahorros  
  
Cuando lo hayas hecho, por favor avísame.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente para tus ventas. Necesito tus datos para continuar: nombre, teléfono y detalles de tu negocio.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Ahora, por favor, dame tu nombre, teléfono y detalles de tu negocio para completar el proceso.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos de pago para que puedas proceder?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. El primer mes cuesta COP 210.000, que incluye la configuración y el primer mes de servicio. ¿Prefieres pagar con Nequi o transferencia a Bancolombia?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, realiza el pago de COP 210.000 y confirma cuando lo hayas hecho.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Realiza el pago de COP 210.000 por Nequi y envíame la captura del comprobante. Con eso seguimos con la activación del servicio.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me envíes la captura del comprobante, procederemos a activar tu servicio y te guiaré en la configuración inicial. ¡Así podrás empezar a aprovechar todas las ventajas del sistema!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Realiza el pago de COP 210.000 y confirma cuando lo hayas hecho.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Realizas el pago de COP 210.000 con esos datos y luego me envías aquí la captura del comprobante. Así podremos continuar con la activación del servicio.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante de pago para continuar con la activación del servicio. ¡Gracias!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita el Plan Básico y le interesa pagar por Nequi. Dijo que ya realizó la consignación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu teléfono para continuar con el proceso?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, confírmame tu número de teléfono para completar el registro.  
  
Datos para pagar por Nequi:  
- Nombre: Asesor Comercial  
- Monto: COP 210.000 (implementación + primer mes)  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye la configuración inicial y el asistente conversacional inteligente. Vamos a necesitar tu nombre, teléfono y detalles para proceder. ¿Me los puedes proporcionar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago del Plan Básico, puedes hacerlo a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos medios prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El costo es de COP 100.000 de implementación y COP 110.000 al mes. Para avanzar, necesito tu nombre, teléfono y un correo electrónico.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, compárteme tu nombre, teléfono y correo electrónico para completar el proceso.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles para activar el servicio.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer pago mensual. Luego, pagarás COP 110.000 mensuales. ¿Me puedes proporcionar tu nombre y teléfono para continuar con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Perfecto! El Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Para continuar, necesito tu nombre, teléfono y detalles. ¿Te gustaría que te envíe los datos de pago?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para que puedas realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes), y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te voy a pasar con una persona del equipo para que te atienda. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para empezar, necesito tu nombre, teléfono y detalles. ¿Me los puedes compartir?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y algún detalle adicional para activar el servicio?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto. Para pagar por transferencia a Bancolombia, puedes hacerlo a la cuenta que te envía el sistema. Tu inversión inicial es de COP 210.000 (implementación + primer mes). ¿Me confirmas tu nombre y teléfono para completar los datos?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, para confirmar tu pedido de una Hamburguesa Sencilla por COP 18.000, ¿quieres agregar una bebida? Si decides hacerlo, también te puedo ayudar con los datos de pago.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Para confirmar tu pedido de la Hamburguesa Sencilla, ¿quieres agregar una bebida?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Para confirmar tu pedido de la Hamburguesa Sencilla, ¿te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Tu pedido es una Hamburguesa Sencilla por COP 18.000. Si decides agregar una bebida, házmelo saber. Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, para completar tu pedido, ¿me puedes confirmar la dirección de entrega y si quieres agregar una bebida?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: después de que hagas el pago por Nequi, envíame aquí la captura del comprobante. Con eso seguimos con tu pedido. ¿Ya tienes la dirección de entrega?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** No hay problema. Aquí te dejo nuevamente los datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando lo hagas, envíame la captura del comprobante y seguimos con tu pedido. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita una hamburguesa sencilla. Está interesado en pagar por Nequi y ya realizó el pago.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me confirmes tu dirección de entrega y tu número de teléfono, por favor.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la envío?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Genial, ya tengo tu número. ¿Me puedes dar tu nombre y la dirección de entrega para completar el pedido? Luego, te digo cómo pagar.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, solo necesito tu nombre y la dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre, teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la enviamos?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál de estos medios prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y te gustaría agregar alguna bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para pagar?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo para beber, como una gaseosa o un jugo?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo que podrá ayudarte. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la enviamos?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia. Te voy a pasar con el equipo para que puedan revisar tu situación. Un momento, por favor.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde la enviamos?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, para la transferencia a Bancolombia (ahorros) te dejo los datos de pago abajo. También necesito tu nombre, teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa o un jugo natural para acompañarla?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, entonces llevas una Hamburguesa Sencilla por COP 18.000. ¿Me puedes dar tu nombre, teléfono y dirección para la entrega?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos pagos por Nequi. ¿Te gustaría que te envíe los datos de pago?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Ahora, por favor, ¿me puedes dar tu teléfono y dirección para completar el pedido?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también necesito tu teléfono y dirección para la entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo me falta tu dirección para completar el pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez que hagas el pago, me envías aquí la captura del comprobante. Con eso seguimos con tu pedido. ¿Tienes ya la dirección lista?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también necesito tu dirección para la entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos para pagar por Nequi. Solo necesito que me confirmes tu dirección para poder hacer el pedido. ¿Cuál es?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, haz el pago y envíame la captura del comprobante cuando lo tengas. Así seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita una hamburguesa sencilla. Está interesado en pagar por Nequi y ya realizó el pago.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito que me confirmes tu dirección de entrega y tu número de teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu nombre y la dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido? Y si quieres, puedes agregar una gaseosa o un jugo natural.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te lo enviamos?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría agregar algo más a tu pedido, como una gaseosa o un jugo natural?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Con gusto, te paso con una persona del equipo. Ellos te atenderán por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Solicita hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cuál es tu dirección de entrega?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia y lamento lo sucedido. Te voy a pasar con el equipo para que puedan ayudarte con tu reclamo.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí están los datos para pagar por transferencia a Bancolombia (ahorros). ¿Me puedes dar tu nombre, teléfono y dirección de entrega para confirmar el pedido?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Excelente elección con la Hamburguesa Sencilla, que cuesta COP 18.000. ¿La quieres acompañar con algo, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, entonces confirmamos tu pedido de una Hamburguesa Sencilla. ¿Cuál es tu nombre, teléfono y dirección de entrega?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Ahora, ¿me das tu nombre, teléfono y dirección de entrega para confirmar tu pedido de la Hamburguesa Sencilla?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Cuál es tu teléfono y dirección de entrega para completar el pedido?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame también tu teléfono y dirección de entrega para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿cuál es tu dirección de entrega para confirmar tu pedido de la Hamburguesa Sencilla?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez hagas el pago por Nequi, envíame aquí la captura del comprobante. Con eso, seguimos con tu pedido. ¿Listo para darme tu dirección de entrega?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi nuevamente.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅  
  
Cuando hagas el pago, envíame la captura del comprobante. ¿Cuál es tu dirección de entrega?

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos para pagar por Nequi, solo necesitas hacer el pago y luego enviarme la captura del comprobante. ¿Te gustaría que te los repita?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando termines de pagar, envíame la captura del comprobante. También necesito tu dirección de entrega para completar el pedido. ¿Cuál es?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita hacer un pedido de una Hamburguesa Sencilla. Está interesado en pagar por Nequi y ya realizó el pago.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu dirección de entrega y tu número de teléfono para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida, como gaseosa o jugo natural?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ¿con cuál de los medios de pago prefieres hacerlo? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, confirma también la dirección de entrega para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, solo necesito tu número de teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría agregar algo más, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Antes de enviarte los datos, ¿con cuál de los medios de pago prefieres hacer la consignación: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla a COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar alguna bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Quieres hacer tu pedido con la Hamburguesa Sencilla y alguna bebida?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te voy a pasar con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Para cuántas personas es el pedido y quieres agregar algo más, como una gaseosa o un jugo natural?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y dónde te la enviamos?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros):  
  
- Nombre del titular: Mesa Activa  
  
¿Me puedes dar tu nombre, teléfono y dirección para el envío?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
