# Estándar del asesor: no_pide_base_20261115

**NO PASA** · código `48d37ce + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 90 conversaciones (3 muestras por negocio: asesor_ai_prod, clinic, restaurant)

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
| ❌ no pide lo ya dado (juez) | 82 de 90 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ❌ no pide el dato de pago (juez) | 89 de 90 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 90 de 90 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 87 de 90 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 90 de 90 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 90 de 90 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ❌ nota fiel (juez) | 87 de 90 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.1027 · juez USD 0.0385. Llamadas al modelo por mensaje: 2.06. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 32.

Por cada mensaje del cliente: responde en 3.2 s (el 5 % más lento, 4.9 s o más) · USD 0.36 por cada 1.000 mensajes · fuera de formato: 0 de 288 · sin respuesta de la IA: 3 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu nombre y tu teléfono para completar la activación. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu nombre y teléfono. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · restaurant · el chat de producción · turno 10: El asesor pide el teléfono que el cliente ya dio.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ⏎  ⏎ Por favor, indícame tu teléfono y dirección de entrega para completar el pedido. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · restaurant · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «Genial, Laura. Para completar tu pedido, necesito que me des tu nombre, teléfono y dirección de entrega. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · restaurant · el chat de producción · turno 10: Pide el teléfono que el cliente ya dio.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ⏎  ⏎ Ahora, por favor, indícame tu número de teléfono y la dirección de entrega para completar el pedido. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 7: El asesor ya tenía el nombre del cliente.
  - Cliente: «Mi teléfono es 3157778899»
  - Asesor: «Gracias, Juan Camilo. Ahora necesito que me confirmes el día y la hora que prefieres para agendar Agenda Plus.»
- **no pide lo ya dado** · clinic · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ⏎  ⏎ Por favor, también necesito que me des tu nombre, número de teléfono y detalles para la cita. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 10: El cliente ya había dado su teléfono en el turno 7.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Además, necesito tu teléfono y qué día y hora te gustaría coordinar la cita para Agenda Plus. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide el dato de pago** · asesor_ai_prod · reclama · turno 1: El asesor no debe pedir detalles de pago al cliente.
  - Cliente: «Quiero Plan Basico»
  - Asesor: «Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (que incluye la implementación) y luego COP 110.000 mensuales. Para continuar, necesito tu nombre, teléfono y detalles de pago.»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: El asesor repite la misma explicación sin aclarar la duda del cliente.
  - Cliente: «Cómo así»
  - Asesor: «Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: No explica qué debe hacer, solo repite lo que ya dijo.
  - Cliente: «Cómo así»
  - Asesor: «Te envié los datos para pagar por Nequi. Necesito que me confirmes tu número de teléfono y la dirección de entrega para poder completar tu pedido de la Hamburguesa Sencilla.»
- **explica cuando no entienden** · clinic · el chat de producción · turno 11: El asesor no explica qué debe hacer, solo repite que ya envió los datos.
  - Cliente: «Cómo así»
  - Asesor: «Te dejé los datos para pagar por Nequi en el chat anterior. Necesito que me confirmes tu teléfono y el día y hora que prefieres para agendar la cita para Agenda Plus.»
- **nota fiel** · clinic · el chat de producción · turno 13: El cliente no dijo que era dueño de una tienda de ropa.
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «Juan Camilo, dueño de una tienda de ropa, está interesado en el producto Agenda Plus y prefiere pagar por Nequi. Informó que ya realizó el pago.»
- **nota fiel** · clinic · el chat de producción · turno 13: El cliente no dijo que era dueño de una tienda de ropa.
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «Juan Camilo, dueño de una tienda de ropa, necesita coordinar una cita para Agenda Plus y está interesado en pagar por Nequi. Mencionó que ya realizó una consignación.»
- **nota fiel** · clinic · reclama · turno 2: La nota inventa que el cliente está interesado en Agenda Plus.
  - Cliente: «Me cobraron dos veces y nadie me responde, estoy muy molesto»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Con cuál medio de pago prefieres realizar la transacción?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Necesito tus datos para activar el servicio: nombre, teléfono y detalles. ¿Me los puedes proporcionar?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Te gustaría que te envíe los datos de pago para ese medio?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Solo necesito tu número de teléfono y los detalles de tu tienda para completar la activación del servicio.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu número de teléfono para completar la activación del servicio.  
  
**Datos Nequi:**  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora, realiza el pago por Nequi y envíame la captura del comprobante aquí para que activemos tu servicio. ¡Estoy aquí para ayudarte!

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que me envíes la captura del comprobante, procederé a activar tu servicio. Te guiaré en la configuración inicial para que empieces a usarlo. ¡Espero tu comprobante!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
**Datos Nequi:**  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu captura del comprobante para activar tu servicio. ¡Avísame cuando estés listo!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con la activación del servicio.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu nombre y tu teléfono para completar la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, solo necesito tu nombre y detalles para completar el proceso. ¿Cómo prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre y teléfono para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio). Luego, pagarás COP 110.000 mensualmente. ¿Me puedes compartir tu nombre, teléfono y detalles para continuar con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes proporcionar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres usar?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Podrías darme tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que puedan ayudarte directamente.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con el pago?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación, entiendo tu molestia. Voy a pasar tu reclamo al equipo para que te ayuden con este tema y puedan verificar lo ocurrido. Ellos se pondrán en contacto contigo por este mismo chat.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. También está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para activar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, envíame tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Excelente decisión! El Plan Básico tiene un costo de COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para activar el servicio, necesito tu nombre, teléfono y detalles de pago. ¿Cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, para proceder con la transferencia a Bancolombia, necesito tu nombre y teléfono, y así te envío los datos de pago.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría usar ese medio de pago en lugar de la transferencia? Solo necesito tu nombre y teléfono para seguir.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, confirma cuando hayas realizado el pago.  
  
Datos de pago:  
  
Una vez que confirmes, activamos tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Perfecto, Juan Camilo. Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora solo falta que me envíes la captura del comprobante de Nequi una vez que realices el pago, y así activamos tu Plan Básico. ¡Espero tu mensaje!

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que me envíes la captura del comprobante, procederemos a activar tu Plan Básico. Te guiaré en la configuración inicial para que empieces a usar el sistema. ¡Espero tu comprobante!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Realiza el pago y me envías aquí la captura del comprobante. ¡Espero tu mensaje!  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante de pago para continuar con la activación de tu Plan Básico. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y se interesa por el medio de pago Nequi. Informó que ya realizó el pago y está esperando la confirmación para continuar con la activación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Te gustaría que te enviara los datos para proceder con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu nombre y teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, gracias por tu número. Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál de estos métodos prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre para completar el registro.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre y teléfono para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes e incluye la configuración inicial y el asistente conversacional inteligente. Luego, se paga COP 110.000 mensualmente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Este plan incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 en el primer mes (COP 100.000 de implementación + COP 110.000 mensual). Luego, se paga COP 110.000 mensualmente. ¿Me puedes compartir tu nombre, teléfono y detalles para comenzar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por solo COP 210.000 el primer mes, que incluye la implementación y el primer mes de servicio. Luego, pagarás COP 110.000 mensualmente. ¿Me puedes dar tu nombre, teléfono y algún detalle adicional para proceder?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con alguien del equipo para que te atiendan. ¡Un momento!

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (que incluye la implementación) y luego COP 110.000 mensuales. Para continuar, necesito tu nombre, teléfono y detalles de pago.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Está interesado en el Plan Básico.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para realizar la transferencia a Bancolombia (ahorros). Por favor, confírmame tu nombre y teléfono para completar el registro.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles para la implementación. ¿Me los puedes proporcionar?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Ahora, ¿me puedes dar tu nombre, teléfono y detalles para la implementación?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, puedes pagar con Nequi. ¿Te gustaría que te envíe los datos de pago?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora necesito tu número de teléfono y detalles de la tienda para completar la implementación del Plan Básico.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también comparte el número de teléfono y los detalles de tu tienda para finalizar la implementación.  
  
Datos de pago:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Tu teléfono es 3157778899. Ahora, por favor, realiza el pago por Nequi y envíame la captura del comprobante para que podamos activar tu servicio.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, simplemente envíame aquí la captura del comprobante. Con eso, procederemos a activar tu servicio y a guiarte en la configuración.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí te dejo de nuevo los datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅  
  
Recuerda enviarme la captura del comprobante una vez lo hagas.

**[11] Cliente:** Cómo así

**[11] Asesor:** Disculpa por la confusión. Los datos para pagar por Nequi están arriba, en el chat. Si no los ves, puedo describirte cómo hacer el pago. ¿Te gustaría que te explique el proceso?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que realices el pago, envíame la captura del comprobante y continuaremos con la activación de tu servicio.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en el Plan Básico y mencionó que ya realizó un pago por Nequi.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** ¡Perfecto, Laura! El Plan Básico incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Cuesta COP 100.000 de implementación y COP 110.000 al mes. Con este plan podrás responder rápido y hacer seguimiento a tus clientes. ¿Te gustaría que te envíe los datos para el pago?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dime tu nombre, teléfono y cualquier detalle adicional que quieras compartir.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 (incluye implementación más primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Cuál medio de pago prefieres? Puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B, o un link de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, indícame tu nombre y detalles para finalizar el proceso.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para empezar, necesito tu nombre, teléfono y detalles, y luego te indico cómo pagar.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Listo para seguir?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar? Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración inicial y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder con el pago?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B, o te puedo enviar un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, la guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos para que puedas realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye la configuración inicial y el asistente conversacional inteligente por COP 210.000 en el primer mes (incluye implementación y el primer mes de servicio). Luego, se paga mensualmente COP 110.000. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para comenzar, necesito tu nombre, teléfono y detalles. ¿Cómo deseas pagar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que le cobraron dos veces y está muy molesto porque nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí están los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, indícame tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido? ¿Te gustaría agregar una bebida, como una gaseosa o un jugo natural?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría agregar una bebida a tu pedido?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría añadir una bebida a tu pedido o prefieres solo la hamburguesa?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Solo para confirmar, ¿quieres una Hamburguesa Sencilla por COP 18.000 y agregar una bebida? ¿Cuál prefieres, gaseosa o jugo natural?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo falta tu dirección de entrega para completar el pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago, me envías aquí la captura del comprobante. Así puedo confirmar tu pedido y enviarlo a la cocina.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, avísame cuando hayas hecho el pago y me envías la captura del comprobante para continuar con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en una Hamburguesa Sencilla por COP 18.000 y desea pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con su pedido.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto, Laura! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para completar tu pedido, necesito tu nombre, teléfono y dirección de entrega. ¿Me los compartes, por favor?  
  
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

**[2] Asesor:** Perfecto, solo necesito saber con cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, ¿me confirmas tu nombre y dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres hacer la consignación? Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál de estos medios prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría confirmar tu pedido de la Hamburguesa Sencilla y decirme si agregarás una bebida?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo ahora mismo.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y cómo prefieres pagar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento que estés pasando por esto. Te voy a pasar con el equipo para que puedan ayudarte con tu situación.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Quiere que lo atiendan para resolver su situación.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, entonces llevas una Hamburguesa Sencilla y una bebida. Ahora, por favor, dime tu nombre, teléfono y dirección de entrega para cerrar el pedido.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Claro, puedes transferir. ¿Con qué medio prefieres pagar? Tenemos Nequi, Daviplata, transferencia a Bancolombia y Bre-B.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, aceptamos Nequi. ¿Te gustaría proceder con ese medio? Si es así, ¿me confirmas el pedido de la Hamburguesa Sencilla y si quieres agregar la bebida?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Perfecto, Juan Camilo. ¿Te gustaría confirmar el pedido de la Hamburguesa Sencilla y si quieres agregar una bebida? Así puedo tomar tus datos para el envío.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Confirma el pedido de la Hamburguesa Sencilla. Necesito tu teléfono, dirección y detalles para el envío.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora necesito tu dirección y detalles para completar el pedido. ¿Cuál es tu dirección?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me envíes la captura del comprobante de pago, seguiré con tu pedido. Así que asegúrate de hacer el pago primero y luego envíame la imagen. ¿Listo para proceder?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi:  
  
Cuando realices el pago, envíame la captura del comprobante para continuar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante. Así podremos continuar con tu pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hayas hecho el pago, envíame la captura del comprobante y continuamos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en hacer un pedido de una Hamburguesa Sencilla y prefiere pagar por Nequi. Informó que ya realizó el pago y está esperando la confirmación para continuar con su pedido.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** Genial, Laura. Para completar tu pedido, necesito que me des tu nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla te va a encantar. ¿Para cuántas personas es el pedido y a dónde te la envío?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre, dirección y cuántas hamburguesas sencillas quieres.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, te anoto una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre, teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios de pago prefieres hacerlo? Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál medio prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos para el pago?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Genial! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que puedan ayudarte mejor. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial elección. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te pasaré con el equipo para que puedan revisar lo que pasó y te ayuden con el cobro. Un momento, por favor.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, entonces llevas una Hamburguesa Sencilla por COP 18.000. Por favor, dame tu nombre, teléfono y dirección para completar tu pedido.  
  
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

**[3] Asesor:** Perfecto, solo necesito tus datos para confirmar el pedido: tu nombre, teléfono y dirección de entrega. Luego te puedo ayudar con el pago por transferencia.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Solo necesito tus datos para confirmar el pedido: tu nombre, teléfono y dirección de entrega.

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Ahora, por favor, indícame tu número de teléfono y la dirección de entrega para completar el pedido.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, por favor, indícame tu número de teléfono y la dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo falta la dirección de entrega para finalizar tu pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago por Nequi, me envías aquí la captura del comprobante. Con eso, seguimos con tu pedido y lo enviamos a la dirección que me diste.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, por favor, indícame tu número de teléfono y la dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos para pagar por Nequi. Necesito que me confirmes tu número de teléfono y la dirección de entrega para poder completar tu pedido de la Hamburguesa Sencilla.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que hagas el pago, envíame aquí la captura del comprobante y seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita hacer un pedido de Hamburguesa Sencilla. Está interesado en pagar por Nequi y ya realizó el pago.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría añadir una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dime tu nombre, teléfono y dirección de entrega.  
  
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

**[3] Asesor:** Genial, entonces tu pedido es una Hamburguesa Sencilla por COP 18.000. Por favor, necesito tu nombre, dirección de entrega y confirmar si deseas agregar algo más.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre, teléfono y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una Gaseosa por COP 5.000 o un Jugo Natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Tenemos Nequi, Daviplata, transferencia a Bancolombia (ahorros) y Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál medio prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla a COP 18.000. ¿Te gustaría agregar una gaseosa a COP 5.000 o un jugo natural a COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría confirmar tu pedido de la Hamburguesa Sencilla y algún complemento?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que te atiendan directamente.

*[2] Nota para el equipo:* El cliente quiere una hamburguesa sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que estés pasando por esto. Te pasaré con el equipo para que puedan ayudarte con tu situación.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Quiere que lo atiendan para resolver su situación.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Genial! Para confirmar tu pedido, necesitaría tu nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para empezar, necesito tu nombre, número de teléfono y qué día y hora te gustaría agendar.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te envíe los datos de pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos de pago para completar la compra?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero Agenda Plus está diseñado para clínicas y consultorios. Si necesitas ayuda con la gestión de citas para tu tienda de ropa, puedo pasar tu consulta al equipo. ¿Te gustaría que lo hiciera?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para agendar Agenda Plus, necesito también tu número de teléfono y qué día y hora te gustaría agendar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando vuelvas a escribir, solo indícame que ya hiciste el pago y comparte la captura del comprobante. Luego, coordinaré el día y la hora para tu cita.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo los datos para pagar por Nequi. Recuerda enviarme la captura del comprobante cuando lo hagas:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, haz el pago y cuando lo tengas, envíame la captura del comprobante para continuar con la coordinación de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente, Juan Camilo, dueño de una tienda de ropa, está interesado en gestionar citas y le interesa Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago, mencionando que ya consignó.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus es ideal para gestionar y confirmar citas en tu tienda. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Te ayudará a organizar la disponibilidad y a no perder pacientes por demora. ¿Te gustaría saber más sobre cómo agendar una cita?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu nombre, teléfono y detalles para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de día y hora que prefieras.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago, puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre y los detalles de día y hora que prefieres para agendar tu cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de cuándo te gustaría empezar.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre, teléfono y detalles de cuándo te gustaría empezar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para empezar, necesito tu nombre, teléfono y detalles sobre el día y la hora que te gustaría agendar.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus te ayudará a gestionar y confirmar tus citas. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para agendarlo, necesitaré tu nombre, teléfono y los detalles de la cita que deseas. ¿Qué día y hora tienes en mente?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál de estos medios prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría avanzar con la contratación de Agenda Plus?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles sobre el día y la hora que prefieres.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye la gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita que deseas. ¿Qué día y hora te gustaría?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto porque nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus te ayudará a gestionar y confirmar citas de manera más eficaz. Para agendar, necesito tu nombre, teléfono, y qué día y hora te gustaría. ¿Cuál es tu disponibilidad?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Para la transferencia a Bancolombia, por favor usa el monto de COP 140.000 de implementación y COP 170.000 al mes. ¿Me puedes dar tu nombre y número de teléfono para continuar?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono, y qué día y hora te gustaría. ¿Cuál es tu disponibilidad?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te envíe los datos para el pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también recibimos pagos por Nequi. Si quieres, puedo enviarte los datos para que realices el pago. ¿Te gustaría que lo haga?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero Agenda Plus está diseñado para clínicas y consultorios. Si necesitas ayuda con la gestión de citas para tu tienda de ropa, puedo averiguar más con el equipo. ¿Te gustaría eso?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito que me confirmes el día y la hora que prefieres para agendar Agenda Plus.  
  
Datos para Nequi:  
- Nombre: Agenda Clinica Pro  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora necesito que me confirmes el día y la hora que prefieres para agendar Agenda Plus.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez realices el pago, me envías aquí la captura del comprobante. Después, coordinamos el día y la hora de tu cita. ¿Te gustaría confirmar algún día en particular para agendar?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito que me confirmes el día y la hora que prefieres para agendar Agenda Plus.  
  
Datos para Nequi:  
- Nombre: Agenda Clinica Pro  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hayas hecho el pago, envíame la captura del comprobante y coordinamos el día y la hora para agendar tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en el producto Agenda Plus y prefiere pagar por Nequi. Informó que ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus es un servicio que te ayuda a gestionar y confirmar citas para tu negocio. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. ¿Te gustaría saber más sobre cómo podría ayudarte a organizar tu agenda?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito que me des tu nombre, número de teléfono y detalles para la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus te ayudará a gestionar y confirmar citas de manera eficiente. Para agendar, necesito tu nombre, teléfono y los detalles de la cita: día y hora. ¿Me los puedes proporcionar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Para el pago de Agenda Plus, puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos métodos prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre y los detalles de la cita: día y hora.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles sobre el día y hora que te gustaría.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también necesito tu nombre, teléfono y detalles sobre el día y hora que te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, la Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para empezar, necesito tu nombre, teléfono y los detalles de tu clínica. ¿Qué día y hora te gustaría agendar la cita?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacerlo? Puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles para coordinar el día y la hora. ¿Cuál sería tu preferencia?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar mediante Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál de estos medios prefieres utilizar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye la gestión y confirmación de citas. Cuesta COP 140.000 de implementación más COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes alguna preferencia?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para el pago o prefieres avanzar con los detalles de la cita?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita. ¿Qué día y hora tienes en mente?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que puedan ayudarte mejor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. El costo de implementación es COP 140.000 y luego COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita. ¿Qué día y hora tienes en mente?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Voy a pasar tu reclamo al equipo para que te ayuden con esto. Ellos se encargarán de verificar lo que ocurrió.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes alguna preferencia?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para la transferencia a Bancolombia (ahorros). ¿Me puedes dar tu nombre y teléfono para continuar con la agenda?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Excelente decisión. Para empezar con Agenda Plus, necesito tu nombre, teléfono y qué día y hora te gustaría coordinar la cita. ¡Vamos a agendar!

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te envíe los datos para realizar el pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Si te sirve, puedo enviarte los datos para que realices el pago.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero en Agenda Clinica Pro trabajamos específicamente con clínicas y consultorios para ayudar a gestionar citas. Si necesitas más información sobre cómo podemos ayudar a tu negocio, estaré encantado de ayudarte.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Además, necesito tu teléfono y qué día y hora te gustaría coordinar la cita para Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿qué día y hora te gustaría coordinar para la cita?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez que realices el pago, me envías aquí la captura del comprobante. Con eso, podemos continuar y confirmar la cita para Agenda Plus.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Además, necesito tu teléfono y qué día y hora te gustaría coordinar la cita para Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te dejé los datos para pagar por Nequi en el chat anterior. Necesito que me confirmes tu teléfono y el día y hora que prefieres para agendar la cita para Agenda Plus.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que realices el pago, envíame aquí la captura del comprobante y seguimos con la confirmación de la cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita coordinar una cita para Agenda Plus y está interesado en pagar por Nequi. Mencionó que ya realizó una consignación.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Agenda Plus es un servicio que gestiona y confirma citas, ideal para que no pierdas pacientes por demoras. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. ¿Te gustaría saber más sobre cómo agendarte?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu nombre, número de teléfono y detalles sobre el día y la hora en que te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. El costo es de COP 140.000 por implementación y COP 170.000 al mes. Para comenzar, necesito tu nombre, teléfono y detalles sobre el día y la hora que prefieres para agendar la cita.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos métodos prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre y los detalles del día y la hora que prefieres para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, la Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita. ¿Qué día y hora te gustaría?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para continuar, necesito tu nombre, teléfono y detalles de la cita. ¿Qué día y hora te gustaría?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Su costo es COP 140.000 de implementación y COP 170.000 mensuales. Para agendar, necesito tu nombre, teléfono y detalles de la cita: día y hora que prefieres. ¿Cuál es la información que deseas compartir?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono, y qué día y hora te gustaría. ¿Tienes algún momento específico en mente?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar mediante Nequi, Daviplata, transferencia a Bancolombia, Bre-B o a través de un link de pago. ¿Cuál de estos métodos prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus te ayudará a gestionar y confirmar tus citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesitaré tu nombre, teléfono y los detalles de la cita que deseas. ¿Qué día y hora tienes en mente?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. Si decides avanzar, puedo enviarte los datos para que realices el pago. ¿Te gustaría proceder?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles para la cita: día y hora. ¿Cuál sería tu preferencia?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te voy a pasar con una persona del equipo que podrá ayudarte mejor. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación más COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita (día y hora). ¿Cuál sería el día y hora que prefieres?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para avanzar, necesito tu nombre, teléfono y detalles sobre el día y la hora que prefieres para agendar la cita.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, proporciona tu nombre, teléfono y los detalles del día y la hora que prefieres para agendar la cita.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
