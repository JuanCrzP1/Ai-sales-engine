# Estándar del asesor: no_pide_v15b_20261115

**NO PASA** · código `9936a3a + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 90 conversaciones (3 muestras por negocio: asesor_ai_prod, clinic, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 90 de 90 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 90 de 90 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 90 de 90 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 90 de 90 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 90 de 90 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 90 de 90 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 90 de 90 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 90 de 90 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 90 de 90 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 90 de 90 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 88 de 90 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 90 de 90 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 90 de 90 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 88 de 90 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ❌ coherente con los datos (juez) | 89 de 90 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 90 de 90 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ❌ nota fiel (juez) | 89 de 90 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.1065 · juez USD 0.0327. Llamadas al modelo por mensaje: 2.08. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 42.

Por cada mensaje del cliente: responde en 3.1 s (el 5 % más lento, 5.0 s o más) · USD 0.37 por cada 1.000 mensajes · fuera de formato: 0 de 288 · sin respuesta de la IA: 1 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **no pide lo ya dado** · clinic · el chat de producción · turno 10: El cliente ya dio su teléfono en el turno 7.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, envíame tu teléfono y qué días y horas te gustaría coordinar para la cita. ⏎  ⏎ Datos de pago: ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 10: El asesor pide el teléfono que el cliente ya dio.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ahora, necesito tu teléfono y qué día y hora te gustaría agendar la cita. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: El asesor repite la misma información sin explicarla.
  - Cliente: «Cómo así»
  - Asesor: «Te pido disculpas, parece que no he podido enviarte el método de pago. Te lo comparto de nuevo: arriba en el chat tienes los datos para pagar por Nequi. Haz el pago y luego envíame la captura del comprobante para seguir con la implementación. Si necesitas más ayuda, dime.»
- **explica cuando no entienden** · clinic · el chat de producción · turno 11: El asesor repite la misma información sin explicar de otra forma.
  - Cliente: «Cómo así»
  - Asesor: «Te compartí los datos para pagar por Nequi, que debes usar para completar el pago. Luego, me envías la captura del comprobante aquí. ¿Tienes ya el día y hora en mente para agendar la cita?»
- **coherente con los datos** · restaurant · pide los datos de otro medio · turno 2: Condiciona el envío de datos de pago que ya están en el mensaje.
  - Cliente: «listo, mándame los datos para pagar por transferencia»
  - Asesor: «Para finalizar tu pedido de una Hamburguesa Sencilla, necesito tu nombre, teléfono y dirección de entrega. Luego te envío los datos para la transferencia. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Bancolombia* ⏎ Cuenta de ahorros ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **nota fiel** · clinic · el chat de producción · turno 13: El cliente no dijo que era dueño de una tienda de ropa.
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «Juan Camilo, dueño de una tienda de ropa, está interesado en gestionar citas y le interesa Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Excelente decisión! El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 en el primer mes (incluye la implementación) y luego COP 110.000 mensuales. Para proceder, necesito tu nombre, teléfono y detalles. ¿Me los compartes?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes pagar por transferencia a Bancolombia. Comparte tu nombre, teléfono y detalles para continuar con la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Si prefieres pagar por ese medio, dime tu nombre, teléfono y detalles para avanzar.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, solo confírmame si necesitas algo más antes de proceder.  
  
Datos para pagar por Nequi:  
  
¿Hay algo más que necesites?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Perfecto, Juan Camilo. Realiza el pago por Nequi y envíame aquí la captura del comprobante. Así seguimos con la activación del Plan Básico.

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu nombre y teléfono. Ahora, solo falta que me envíes la captura del comprobante de pago por Nequi para continuar con la activación del Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando me envíes la captura del comprobante, procederemos a configurar el sistema. Te guiaré en los pasos para la integración con WhatsApp y te daré acceso al asistente conversacional inteligente. ¡Estamos cerca de comenzar!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Realiza el pago y envíame aquí la captura del comprobante para continuar con la activación del Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero la captura del comprobante para continuar con la activación del Plan Básico. ¡Estamos casi listos!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con la activación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puedes dar tu número de teléfono para comenzar con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito que me confirmes tu número de teléfono para completar el proceso.  
  
¡Gracias!  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ahora necesito tu nombre y detalles para completar la activación. Luego, te indico cómo realizar el pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, confirma tu nombre para completar la activación.  
  
Datos de pago:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con el pago?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dame tu nombre y teléfono para completar el registro.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Cuál de los medios de pago prefieres usar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y el asistente conversacional inteligente por COP 210.000 el primer mes (100.000 de implementación + 110.000 mensual). Luego, solo 110.000 al mes. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres usar?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, número de teléfono y algún detalle adicional para avanzar con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes y luego COP 110.000 mensuales. Para proceder, necesito tu nombre, teléfono y detalles para la activación.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude directamente.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, una guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te pasaré con el equipo para que puedan revisar tu caso y darte una solución. Por favor, espera un momento.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes (incluye la configuración inicial y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y los detalles que necesites para proceder con el pago?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, realiza la transferencia y comparte el comprobante cuando puedas.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 en el primer mes (incluye la implementación y el primer mes de servicio). Después, pagas COP 110.000 mensuales. Para continuar, necesito tu nombre, teléfono y detalles para la implementación. ¿Me los compartes?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes pagar por transferencia a Bancolombia. Solo necesito tu nombre, teléfono y detalles para la implementación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría usarlo como método de pago? Solo necesito tu nombre, teléfono y detalles para la implementación.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Solo necesito tu número de teléfono y detalles para la implementación. Así podemos activar tu Plan Básico y empezar a mejorar el seguimiento de tus clientes.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu número de teléfono para completar la implementación.  
  
Datos para Nequi:  
- Nombre: Asesor Comercial  
  
¿Me compartes tu número de teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora, por favor, realiza el pago por Nequi y envíame aquí la captura del comprobante. Así podremos activar tu Plan Básico y comenzar a mejorar el seguimiento de tus clientes.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me envíes la captura del comprobante, procederemos a activar tu Plan Básico. Luego, te guiaré en el proceso de configuración inicial para que puedas comenzar a usar el sistema. ¡Espero tu comprobante!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo los datos para pagar por Nequi nuevamente.  
  
Datos para Nequi:  
- Nombre: Asesor Comercial  
  
Cuando hagas el pago, no olvides enviarme la captura del comprobante.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y me envías aquí la captura del comprobante. Así podremos activar tu Plan Básico.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la activación de tu Plan Básico. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Informó que ya realizó la consignación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, una guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu número de teléfono para empezar con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame también los detalles que faltan, como tu número de teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Cómo deseas pagar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, solo necesito tu nombre para completar los datos. Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu nombre para completar el registro.  
  
¿Qué nombre te gustaría que registre?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye configuración inicial y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Recuerda darme tu nombre y teléfono para continuar con la activación.  
  
Datos para Nequi:  
  
- **Nombre:** Asesor Comercial  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer pago mensual) y luego COP 110.000 cada mes. Este plan incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 por la implementación y COP 110.000 mensuales. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál de estos métodos prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Listo para continuar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para iniciar?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Voy a pasarte con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y solicitó hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que estés pasando por esto. Te voy a pasar con el equipo para que puedan revisar el tema de tus cobros y responderte lo más pronto posible.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para la transferencia a Bancolombia (ahorros). Por favor, realiza la transferencia y comparte el comprobante cuando lo tengas. ¿Te gustaría que te envíe los detalles de la implementación también?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y los detalles que quieras agregar.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes transferir. Ahora, por favor, dame tu nombre y teléfono.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Ahora, por favor, dame tu nombre y teléfono para continuar con el proceso.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Para finalizar, por favor compárteme tu número de teléfono y procedemos con el pago.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu número de teléfono para completar el registro.  
  
Datos para Nequi:  
- Nombre: Asesor Comercial  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Una vez realices el pago por Nequi, por favor envíame la captura del comprobante y comenzaremos con la implementación. ¡Estoy aquí para ayudarte!

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago, solo envíame la captura del comprobante aquí en el chat. Luego, te guiaré en el proceso de implementación para que tu sistema esté listo. ¡Espero tu comprobante!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí tienes de nuevo los datos para pagar por Nequi:  
- Nombre: Asesor Comercial  
  
Recuerda enviarme la captura del comprobante una vez realices el pago. ¡Estoy aquí para ayudarte!  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te pido disculpas, parece que no he podido enviarte el método de pago. Te lo comparto de nuevo: arriba en el chat tienes los datos para pagar por Nequi. Haz el pago y luego envíame la captura del comprobante para seguir con la implementación. Si necesitas más ayuda, dime.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la implementación. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en el Plan Básico y mencionó que ya realizó el pago.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Te gustaría que te envíe los datos para proceder con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu número de teléfono y detalles adicionales que quieras agregar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 al mes). ¿Me puedes dar tu nombre, teléfono y algún detalle adicional para avanzar con la activación?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias por tu número. ¿Cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, confirma tu nombre y cualquier detalle adicional que falte para completar la activación.  
  
Datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. Para comenzar, ¿me puedes dar tu nombre, teléfono y detalles para la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, necesito tu nombre, teléfono y detalles. ¿Me los puedes proporcionar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres usar?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para proceder?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que hables directamente con ellos.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer pago mensual), y luego COP 110.000 cada mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia y lamento lo sucedido. Voy a pasar tu reclamo al equipo para que puedan verificar lo del cobro y responderte a la brevedad.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para empezar, necesito tu nombre, teléfono y detalles. ¿Me los puedes proporcionar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí están los datos para hacer la transferencia a Bancolombia (ahorros). Por favor, realiza el pago y confirma una vez lo hayas hecho. ¿Necesitas algo más?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Genial, entonces confirmo tu pedido: una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida? Si es así, ¿cuál prefieres?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría agregar una bebida a tu pedido antes de proceder con el pago?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Entonces, confirmo tu pedido: una Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar una bebida antes de proceder?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu número de teléfono y la dirección de entrega para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo necesito la dirección de entrega para completar tu pedido.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, envíame aquí la captura del comprobante. Con eso seguimos con tu pedido y te confirmo el tiempo de entrega.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí te dejo nuevamente los datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅  
  
Cuando hagas el pago, envíame la captura del comprobante.

**[11] Cliente:** Cómo así

**[11] Asesor:** Disculpa la confusión. Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y envíame aquí la captura del comprobante. Así seguimos con tu pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu captura del comprobante para continuar con tu pedido. ¡Gracias!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y está interesado en una hamburguesa sencilla. Mencionó que ya realizó un pago por Nequi y está esperando la confirmación para continuar con su pedido.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto, Laura! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu teléfono, dirección y detalles para confirmar el pedido.  
  
**Datos para Nequi:**  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, necesito saber con qué medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia o Bre-B.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre y la dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para completar tu pedido, necesito tu teléfono, dirección y si deseas agregar una bebida.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y te gustaría agregar alguna bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría continuar con tu pedido de la Hamburguesa Sencilla y algún complemento?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que puedan ayudarte.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y quieres agregar algo más, como una gaseosa o un jugo natural?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que estés pasando por esto. Voy a pasarlo al equipo para que te ayuden con tu situación. ¿Hay algo más que quieras agregar sobre tu pedido?

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde. Quiere que lo atiendan para resolver su situación.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, entonces tu pedido es una Hamburguesa Sencilla. Ahora, necesito tu nombre, teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Para cuántas personas es el pedido? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Genial, entonces te confirmo la Hamburguesa Sencilla. ¿Te gustaría agregar una gaseosa o un jugo natural? También necesito tu nombre, teléfono y dirección para completar el pedido.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Entonces, ¿quieres agregar una gaseosa o un jugo natural a tu Hamburguesa Sencilla? Además, necesito tu nombre, teléfono y dirección para completar el pedido.

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Ahora, ¿me puedes dar tu teléfono y dirección para completar el pedido? Y si quieres, también puedes agregar una gaseosa o un jugo natural.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu teléfono y dirección para completar el pedido de la Hamburguesa Sencilla. ¿Te gustaría agregar una gaseosa o un jugo natural?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo falta tu dirección para completar el pedido. ¿Te gustaría agregar una gaseosa o un jugo natural?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez que hagas el pago por Nequi, me envías aquí la captura del comprobante. Con eso seguimos con el pedido. ¿Te gustaría agregar algo a tu Hamburguesa Sencilla?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo los datos para pagar por Nequi. Recuerda enviarme la captura del comprobante cuando lo hagas. Solo necesito tu dirección para completar el pedido de la Hamburguesa Sencilla.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero la captura del comprobante. También necesito tu dirección para completar el pedido de la Hamburguesa Sencilla. ¿Cuál es?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y está interesado en una Hamburguesa Sencilla. Mencionó que ya realizó el pago por Nequi.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu número de teléfono, dirección y cualquier detalle adicional para hacer el pedido. ¿Me los puedes dar?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa a tu pedido por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Con cuál medio de pago prefieres realizar la transacción? Tenemos Nequi, Daviplata, transferencia a Bancolombia o Bre-B.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, confírmame tu nombre y dirección de entrega para finalizar el pedido.  
  
Datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, solo necesito tu teléfono, dirección y detalles para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una Gaseosa por COP 5.000 o un Jugo Natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi. ¿Te gustaría que te envíe los datos para el pago?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y qué más te gustaría agregar, como una gaseosa o un jugo natural?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento que estés pasando por esto. Te paso con el equipo para que puedan ayudarte con tu situación.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Para finalizar tu pedido de una Hamburguesa Sencilla, necesito tu nombre, teléfono y dirección de entrega. Luego te envío los datos para la transferencia.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, entonces llevamos la Hamburguesa Sencilla por COP 18.000. ¿Cuál es tu nombre, teléfono y dirección de entrega?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Cuál es tu nombre, teléfono y dirección de entrega para completar el pedido?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Perfecto, Juan Camilo. ¿Cuál es tu número de teléfono y dirección de entrega?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Necesito tu número de teléfono y dirección de entrega para completar el pedido. ¿Me los puedes dar?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo falta tu dirección de entrega para finalizar el pedido.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago por Nequi, envíame aquí la captura del comprobante. Así podremos continuar con tu pedido y enviarlo a la cocina.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Recuerda enviarme la captura del comprobante después de hacer el pago.  
  
Por favor, también necesito tu dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu captura del comprobante. También necesito tu dirección de entrega para completar tu pedido. ¿Cuál es?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita una hamburguesa sencilla. Está interesado en pagar por Nequi y ya realizó la consignación.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial, Laura! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Perfecto! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para continuar, necesito tu teléfono y la dirección de entrega. ¿Me los puedes dar?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, necesito saber con cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, dirección y detalles de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa o un jugo natural?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, solo necesito tu dirección y número de teléfono para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago disponibles prefieres hacerlo: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría confirmar tu pedido de la Hamburguesa Sencilla y alguna bebida?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que puedan ayudarte mejor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla a COP 18.000. ¿Te gustaría añadir una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Voy a pasar tu reclamo al equipo para que te ayuden con esto de inmediato.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar algo más, como una gaseosa o jugo natural?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto. Para la Hamburguesa Sencilla a COP 18.000, necesito tu nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para comenzar, necesito tu nombre, teléfono y qué días y horas te gustaría coordinar. ¿Cuándo te viene bien?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te enviara los datos de pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para cualquiera de los dos métodos?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero Agenda Plus está diseñado para clínicas y consultorios. Si necesitas ayuda con la gestión de citas para tu tienda de ropa, puedo averiguar más con el equipo. ¿Te gustaría que lo hiciera?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, envíame tu teléfono y qué días y horas te gustaría coordinar para la cita.  
  
Datos de pago:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿qué día y hora te gustaría coordinar para la cita? Así podemos avanzar con la agenda.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez realices el pago, envíame aquí la captura del comprobante. Luego, confirmaremos el día y la hora de tu cita. ¿Tienes ya una fecha en mente?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, envíame tu teléfono y qué días y horas te gustaría coordinar para la cita.  
  
Datos de pago:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, realiza el pago y envíame la captura del comprobante cuando lo tengas. Luego, coordinaremos el día y la hora de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en gestionar citas y le interesa Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Agenda Plus es ideal para gestionar y confirmar citas de manera eficiente. Tiene un costo de COP 140.000 por implementación y COP 170.000 al mes. Incluye la gestión de agenda y la confirmación de citas. ¿Te gustaría saber más sobre cómo agendar una cita para implementar este servicio?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame tu número de teléfono y el día y hora en que te gustaría agendar la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita. ¿Qué día y hora tienes en mente?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, solo necesito tu nombre y los detalles de la cita, y luego te puedo enviar los datos de pago. ¿Qué día y hora prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu nombre y los detalles de la cita para finalizar. ¿Qué día y hora prefieres?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye la gestión y confirmación de citas. Su costo es de COP 140.000 por implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieras. ¿Qué día te gustaría empezar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu nombre y teléfono, y el día y hora que prefieras para comenzar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, número de teléfono y la fecha y hora en que te gustaría iniciar. ¿Cuándo te gustaría empezar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres realizar la consignación: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Cómo te gustaría proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o a través de un link de pago. ¿Cuál de estos medios prefieres usar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita. ¿Qué día y hora te gustaría?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. Si te sirve, puedo enviarte los datos para realizar el pago. ¿Listo para continuar con la agenda?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría que confirmemos.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Solicita hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. El equipo te confirmará la disponibilidad.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te pasaré con el equipo para que puedan revisar lo que ocurrió y te den una solución.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto porque nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión de agenda y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieras. ¿Cuándo te gustaría iniciar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, puedes realizar la transferencia a Bancolombia (ahorros). Ahora, por favor, dime tu nombre y teléfono para continuar con la agendación.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes alguna preferencia?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia, entre otros medios. ¿Te gustaría que te envíe los datos de pago una vez cerremos la cita?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos pagos a través de Nequi. ¿Te gustaría coordinar la cita primero y luego te envío los datos de pago?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero en Agenda Clínica Pro nos especializamos en ayudar a clínicas y consultorios a gestionar sus citas. Si necesitas asistencia con la agenda para tu tienda de ropa, puedo pasarte con el equipo para que te ayuden mejor.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ahora, necesito tu teléfono y qué día y hora te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿qué día y hora te gustaría agendar la cita para que el equipo te confirme?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez hagas el pago, me envías aquí la captura del comprobante. Con eso, el equipo podrá confirmar tu cita. ¿Ya tienes en mente el día y hora para la cita?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ahora, necesito tu teléfono y qué día y hora te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te compartí los datos para pagar por Nequi, que debes usar para completar el pago. Luego, me envías la captura del comprobante aquí. ¿Tienes ya el día y hora en mente para agendar la cita?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez hagas el pago, envíame aquí la captura del comprobante. Así podremos continuar con la programación de tu cita. ¿Ya tienes el día y la hora pensados?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en el producto Agenda Plus y prefiere pagar por Nequi. Informó que ya realizó la consignación.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus te ayudará a gestionar y confirmar citas de manera eficiente, evitando que pierdas pacientes por demoras. ¿Te gustaría saber más sobre cómo funciona y su costo?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para agendar, necesito tu número de teléfono, y el día y hora que prefieres para la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. El costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes alguna fecha en mente?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ¿con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre y qué día y hora te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y preferencia de día y hora. ¿Cuándo te gustaría comenzar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu nombre, teléfono y preferencia de día y hora para agendar tu cita.  
  
Datos para pagar por Nequi:  
Nombre: Agenda Clinica Pro  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial elección. Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y un día y hora que te funcionen. ¿Cuál prefieres?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres realizar la consignación? Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. El costo es COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría comenzar.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál de estos métodos prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, la Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y preferencia de día y hora. ¿Qué día te gustaría empezar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. Si decides continuar, puedo enviarte los datos para el pago. ¿Te gustaría agendar ya la cita?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, la Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles sobre el día y hora que prefieres. ¿Cuál sería la mejor opción para ti?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere la Agenda Plus y solicitó hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora prefieres.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación que estás enfrentando. Te voy a pasar con el equipo para que puedan ayudarte con tu reclamo.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus es ideal para gestionar y confirmar citas. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Cuál es tu información?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, puedes realizar el pago por transferencia a Bancolombia (ahorros). Necesito tu nombre, teléfono y detalles del día y hora que deseas agendar para continuar.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para avanzar, necesito tu nombre, teléfono y los detalles de la cita que deseas agendar. ¿Qué día y hora te gustaría?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te envíe los datos de pago o prefieres coordinar primero la cita?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos de pago o prefieres coordinar primero la cita?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero nuestra agenda está enfocada en clínicas y consultorios. Si necesitas ayuda para agendar citas para tu tienda, puedo pasarte con el equipo para que te brinden más información.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ahora, necesito que me confirmes el día y la hora en que te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo falta que me confirmes el día y la hora en que te gustaría agendar la cita y así podemos continuar.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, me envías la captura del comprobante aquí. Luego, confirmaré tu cita con el equipo y te daré los detalles del día y la hora.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo los datos para pagar por Nequi nuevamente. Recuerda enviarme la captura del comprobante cuando lo hagas.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y luego me envías aquí la captura del comprobante; así seguimos con la agenda.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que realices el pago, envíame la captura del comprobante aquí y avanzaremos con la confirmación de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en coordinar una cita y le interesa el producto Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus es un servicio que te ayuda a gestionar y confirmar citas para tu tienda. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. ¿Te gustaría saber más sobre cómo puede ayudarte a organizar tu agenda?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito que me compartas tu número de teléfono y el día y hora en que te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye la gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita: día y hora que prefieres.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, solo necesito tu nombre y los detalles de la cita: día y hora que prefieres. Luego te ayudo con el pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame tu nombre y los detalles de la cita: día y hora que prefieres.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Para agendar Agenda Plus, necesito tu nombre, teléfono y qué día y hora te gustaría. El costo es de COP 140.000 de implementación y COP 170.000 al mes. ¿Cuál sería un buen día para ti?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Después, solo necesito tu nombre, teléfono y qué día y hora te gustaría agendar Agenda Plus.  
  
Datos de Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y qué día y hora prefieres. El equipo te confirmará la disponibilidad.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B y link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y preferencia de día y hora. ¿Cuándo te gustaría comenzar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál medio prefieres utilizar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Perfecto! Agenda Plus tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para avanzar, necesito tu nombre, teléfono y el día y hora en que te gustaría agendar la cita. ¿Te gustaría que te enviara los datos de pago?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos pagos a través de Nequi. ¿Te gustaría que te enviara los datos de pago para continuar con la Agenda Plus?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial elección. Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar. ¿Tienes un día y hora en mente?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te asesore mejor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres. ¿Cuándo te gustaría empezar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora prefieres. ¿Me los puedes compartir?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, confirma tu nombre, teléfono, día y hora para agendar tu cita.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
