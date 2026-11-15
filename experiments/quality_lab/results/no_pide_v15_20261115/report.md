# Estándar del asesor: no_pide_v15_20261115

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
| ❌ no pide lo ya dado (juez) | 87 de 90 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ❌ no pide el dato de pago (juez) | 89 de 90 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 90 de 90 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 89 de 90 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 90 de 90 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 90 de 90 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ❌ nota fiel (juez) | 86 de 90 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.1061 · juez USD 0.0387. Llamadas al modelo por mensaje: 2.08. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 44.

Por cada mensaje del cliente: responde en 3.2 s (el 5 % más lento, 5.3 s o más) · USD 0.37 por cada 1.000 mensajes · fuera de formato: 0 de 288 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ⏎  ⏎ Por favor, indícame tu nombre completo y los detalles para completar la activación. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 10: El cliente ya dio su teléfono.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito también tu teléfono y qué día y hora te gustaría agendar la cita. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, compárteme tu nombre, teléfono y los detalles de la cita que deseas agendar. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide el dato de pago** · restaurant · pregunta a dónde consigna · turno 2: El asesor no debe pedir el medio de pago, sino dar los datos.
  - Cliente: «¿A qué número te consigno?»
  - Asesor: «¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: El asesor no explica qué significa 'cómo así', solo repite.
  - Cliente: «Cómo así»
  - Asesor: «Te envié los datos para pagar por Nequi arriba, pero puedo enviarlos de nuevo. Solo necesito que me confirmes tu teléfono y dirección para completar el pedido.»
- **nota fiel** · restaurant · reclama · turno 2: El cliente no pidió que lo pasaran con una persona.
  - Cliente: «Me cobraron dos veces y nadie me responde, estoy muy molesto»
  - Asesor: «Lamento mucho la situación que estás viviendo. Voy a pasar tu reclamo al equipo para que puedan ayudarte con esto. ¿Puedes darme más detalles sobre tu pedido?»
  - Nota para el equipo: «El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Quiere que lo pasen con una persona para resolver su situación.»
- **nota fiel** · clinic · el chat de producción · turno 13: inventa que el cliente es dueño de una tienda de ropa
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «Juan Camilo, dueño de una tienda de ropa, está interesado en coordinar una cita y le interesa el producto Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.»
- **nota fiel** · clinic · el chat de producción · turno 13: Inventa que el cliente es dueño de una tienda de ropa.
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «Juan Camilo, dueño de una tienda de ropa, está interesado en coordinar una cita para el producto Agenda Plus y prefiere pagar por Nequi. Informó que ya realizó el pago.»
- **nota fiel** · clinic · el chat de producción · turno 13: La nota inventa que el cliente es dueño de una tienda de ropa.
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «El cliente, Juan Camilo, dueño de una tienda de ropa, está interesado en gestionar citas y le interesa Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! Para activar el Plan Básico, necesito que me confirmes con cuál de los siguientes medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, para la transferencia a Bancolombia, necesito que me des tu nombre y teléfono para completar el proceso.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Te gustaría que te envíe los datos de pago para ese medio?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Para proceder con el pago, ¿prefieres Nequi o transferencia a Bancolombia? Te puedo enviar los datos de pago.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, confirma una vez realices el pago.  
  
Datos para pagar por Nequi: 3000XXXXXX - Nombre de la cuenta: Asesor Comercial  
  
¿Te gustaría que te ayude con algo más?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ahora solo necesitas hacer el pago por Nequi a los datos que te envié y luego me envías la captura del comprobante aquí. Así seguimos con la activación del servicio. ¿Listo para proceder?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez realices el pago y me envíes la captura del comprobante, procederemos a guiarte en la configuración inicial del sistema. Te explicaré paso a paso cómo integrar todo y empezar a usarlo. ¿Tienes alguna otra duda mientras tanto?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí tienes de nuevo los datos para pagar por Nequi:  
  
Datos para pagar por Nequi: 3000XXXXXX - Nombre de la cuenta: Asesor Comercial  
  
Cuando realices el pago, me envías la captura del comprobante. ¿Listo para proceder?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y luego me envías aquí la captura del comprobante. Con eso seguimos con la activación del servicio. ¿Te quedó claro?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, realiza el pago y luego envíame la captura del comprobante para continuar con la activación del servicio. Estoy aquí para ayudarte en lo que necesites.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y prefiere pagar por Nequi. Confirmó que ya realizó el pago.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Genial, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Cuesta COP 100.000 de implementación y COP 110.000 al mes. ¿Te gustaría que te envíe los datos para realizar el pago?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu número de teléfono y algún detalle adicional que quieras compartir.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre y teléfono para proceder con la activación?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, solo necesito tu nombre para completar la activación. Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, solo necesito tu nombre para completar la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Genial! El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para empezar, necesito tu nombre, teléfono y detalles. ¿Te gustaría que te envíe los datos de pago?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre y teléfono para completar el registro.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, ¿me puedes dar tu nombre, teléfono y los detalles que necesitemos?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente para responder automáticamente. El primer mes cuesta 210.000 COP (100.000 de implementación + 110.000 mensual). ¿Me podrías dar tu nombre, teléfono y detalles para continuar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y los detalles que necesites para activar el servicio?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para realizar el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que puedan ayudarte. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes compartir tu nombre, teléfono y detalles para comenzar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación que estás viviendo. Te pasaré con el equipo para que puedan revisar tu caso y ayudarte con la solución.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye configuración inicial y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y algún detalle adicional para cerrar la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, realiza la transferencia y confirma cuando lo hayas hecho.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. Para avanzar, necesito tu nombre, teléfono y los detalles para la activación.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia. Para continuar, por favor, compárteme tu nombre y teléfono.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos para el pago?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora, por favor, indícame tu número de teléfono para completar la activación del Plan Básico.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, asegúrate de incluir tu nombre en la referencia del pago.  
  
Para completar la activación, necesito tu número de teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ya tengo tus datos. Haz el pago por Nequi y envíame la captura del comprobante aquí. Así podremos activar tu Plan Básico y empezar a mejorar la atención en tu tienda de ropa.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que me envíes la captura del comprobante, procederemos a activar tu Plan Básico. Te guiaré en la configuración inicial y en la integración con WhatsApp. ¡Estamos a un paso de que empieces a mejorar tus ventas!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí te dejo de nuevo los datos para pagar por Nequi. Asegúrate de incluir tu nombre en la referencia del pago.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la activación de tu Plan Básico. ¡Estamos cerca de empezar!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Informó que ya realizó la consignación.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** ¡Genial, Laura! El Plan Básico cuesta COP 210.000 el primer mes, que incluye la configuración inicial y el sistema mensual. Luego, pagarás COP 110.000 cada mes. Esto te ayudará a responder rápidamente y hacer un seguimiento constante de tus clientes. Para avanzar, necesito tu nombre completo y número de teléfono.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu número de teléfono para completar el registro.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensualmente. ¿Me puedes dar tu nombre, teléfono y los detalles para proceder con el pago?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, confírmame tu nombre para completar el registro.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 en el primer mes (que incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, ¿me compartes tu nombre y teléfono para completar la activación?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. Esto te dará acceso a la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Necesito tu nombre, teléfono y detalles para proceder con el pago.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y el medio de pago que prefieres.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes (incluye la implementación y el sistema mensual) y luego COP 110.000 cada mes. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos pagos por Nequi. ¿Te gustaría que te envíe los datos de pago para proceder con el Plan Básico?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y si prefieres pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo ahora mismo para que puedan ayudarte.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluso la implementación) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que estés pasando por esto. Te voy a pasar con el equipo para que puedan revisar lo que sucedió y ayudarte con tu reclamo.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y menciona que le cobraron dos veces. Está muy molesto porque nadie le responde sobre su situación.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y los detalles que necesites para avanzar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros):  
  
- Valor: COP 210.000  
  
¿Tienes alguna duda con el proceso?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico tiene un costo de COP 210.000 el primer mes, que incluye la configuración y el sistema mensual. Luego, se paga COP 110.000 mensualmente. Para avanzar, necesito tu nombre, teléfono y si prefieres pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, para la transferencia a Bancolombia, por favor comparte tu nombre y teléfono para proceder con la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Si prefieres ese medio, solo necesito tu nombre y teléfono para continuar con la activación.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ahora, por favor, comparte tu número de teléfono para activar el Plan Básico y proceder con el pago por Nequi.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Una vez que realices el pago, confirma aquí y procederemos con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Entonces, realiza el pago por Nequi y envíame la captura del comprobante cuando lo tengas. Así procedemos con la activación de tu Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que realices el pago, simplemente envíame aquí la captura del comprobante. Luego, te guiaré para configurar el sistema y comenzar a usarlo.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi de nuevo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hayas hecho el pago, envíame la captura del comprobante y seguimos con la configuración.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, necesita activar el Plan Básico y le interesa pagar por Nequi. Ya realizó el pago y está esperando la confirmación para continuar con la configuración.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Excelente elección, Laura. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre completo, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre completo y los detalles para completar la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ya tengo tu número. ¿Con qué medio de pago prefieres realizar la transacción? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre para completar la activación del servicio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, comparte tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye configuración y el primer pago mensual) y luego COP 110.000 cada mes. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 al mes). ¿Me puedes dar tu nombre y teléfono para proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál de estos métodos prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Me los puedes compartir?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos pagos a través de Nequi. ¿Te gustaría que te envíe los datos para el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles para la activación del servicio.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 al mes). Luego, pagas COP 110.000 mensuales. Necesito tu nombre, teléfono y detalles para proceder con la activación.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te voy a pasar con el equipo para que puedan revisar tu caso y resolverlo. Un momento, por favor.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Me los puedes dar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Para activar el Plan Básico, realiza el pago de COP 210.000 (configuración + primer mes) a la cuenta de Bancolombia. ¿Me puedes proporcionar tu nombre y teléfono para completar el registro?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, entonces vamos con la Hamburguesa Sencilla a COP 18.000. ¿Qué bebida prefieres, la gaseosa o el jugo natural? También necesito tu nombre, teléfono y dirección para el envío.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos pagos con Nequi. ¿Te gustaría agregar una bebida y compartir tus datos para completar el pedido?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Solo necesito tu teléfono y dirección para el envío. ¿Qué bebida prefieres, la gaseosa o el jugo natural?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora necesito tu teléfono y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo falta tu dirección para completar el pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez que hagas el pago por Nequi, me envías aquí la captura del comprobante. Con eso seguimos y te confirmo el pedido.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora necesito tu teléfono y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos para pagar por Nequi arriba, pero puedo enviarlos de nuevo. Solo necesito que me confirmes tu teléfono y dirección para completar el pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que realices el pago, envíame la captura del comprobante. Así continuamos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y desea hacer un pedido de comida, específicamente una Hamburguesa Sencilla a COP 18.000. Mencionó que ya realizó un pago por Nequi.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para completar tu pedido, necesito tu teléfono y dirección de entrega. ¿Me los compartes?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Genial, ya tengo tu número. ¿Con cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, dirección y si vas a recoger o quieres que te lo llevemos a domicilio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dame tu nombre, teléfono y dirección para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla te costará COP 18.000. ¿Cuántas quieres pedir y a dónde te las envío?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, ¿cuántas Hamburguesas Sencillas te gustaría pedir? También puedo ofrecerte una gaseosa o un jugo natural para acompañar.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría agregar algo más a tu pedido, como una gaseosa o un jugo natural?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te voy a pasar con una persona del equipo para que te atiendan. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación que estás viviendo. Voy a pasar tu reclamo al equipo para que puedan ayudarte con esto. ¿Puedes darme más detalles sobre tu pedido?

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido. Quiere que lo pasen con una persona para resolver su situación.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, para tu pedido de una Hamburguesa Sencilla y una gaseosa, necesito tu nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y a nombre de quién hacemos el pedido?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Cuántas hamburguesas sencillas quieres y a nombre de quién hacemos el pedido?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como medio de pago. ¿Cuántas hamburguesas sencillas quieres y a nombre de quién hacemos el pedido?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Cuántas hamburguesas sencillas deseas pedir?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuál es la dirección de entrega y tu número de teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora necesito la dirección de entrega para completar tu pedido.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago por Nequi, envíame aquí la captura del comprobante. Con eso procederemos a preparar tu pedido y a enviarlo a la dirección que me des.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo los datos para pagar por Nequi de nuevo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅  
  
Cuando hagas el pago, envíame aquí la captura del comprobante.

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y luego envíame aquí la captura del comprobante; así seguimos con tu pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero la captura del comprobante cuando lo hayas hecho. Así podremos continuar con tu pedido. ¿A qué dirección te gustaría que lo enviemos?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y necesita hacer un pedido de Hamburguesa Sencilla. Está interesado en pagar por Nequi y ya realizó la consignación.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto, Laura! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu número de teléfono, dirección de entrega y cualquier detalle adicional que quieras agregar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Genial, para el pago, ¿prefieres hacerlo por Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, dirección y si deseas que te lo enviemos a domicilio o si prefieres recogerlo en el local.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla cuesta COP 18.000. ¿Para cuántas personas es el pedido y cuál es tu dirección de entrega?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dame tu nombre, teléfono y dirección de entrega para confirmar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! Te voy a preparar una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Antes de enviarte los datos de pago, ¿con cuál de los medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla a COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Quieres confirmar tu pedido de la Hamburguesa Sencilla? Si deseas, también podemos agregar una bebida.

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo ahora mismo.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que estés pasando por esto. Te voy a pasar con el equipo para que puedan ayudarte a resolverlo.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le ha respondido.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, para cerrar el pedido, necesito tu nombre, teléfono y dirección de entrega. ¿Me los puedes pasar?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas te gustaría pedir?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Cuántas hamburguesas sencillas deseas pedir?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría pedir más hamburguesas o algún complemento, como una gaseosa o jugo natural?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Perfecto, Juan Camilo. ¿Cuántas Hamburguesas Sencillas te gustaría pedir?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame cuántas Hamburguesas Sencillas deseas pedir y tu dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono. Solo falta que me digas cuántas Hamburguesas Sencillas deseas pedir y tu dirección de entrega.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago, envíame aquí la captura del comprobante. Con eso seguimos con tu pedido y lo enviamos a cocina. ¿Cuántas Hamburguesas Sencillas quieres pedir?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame cuántas Hamburguesas Sencillas deseas pedir y tu dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos con tu pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, haz el pago y envíame la captura del comprobante cuando lo tengas. También, dime cuántas Hamburguesas Sencillas quieres pedir y tu dirección de entrega.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente se llama Juan Camilo y está interesado en hamburguesas sencillas. Desea pagar por Nequi y ya realizó la consignación.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, Laura. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu hamburguesa? ¿Cuántas hamburguesas sencillas vas a pedir?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, por favor, dime tu teléfono, dirección y los detalles de tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar alguna bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Nombre: Mesa Activa  
Teléfono: 3157778899  
  
Ahora, necesito tu nombre y dirección para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre, teléfono y dirección para completar tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación? Tenemos Nequi, Daviplata, transferencia a Bancolombia y Bre-B.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como método de pago. ¿Te gustaría confirmar tu pedido con la hamburguesa sencilla y alguna bebida?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Quieres agregar algo más, como una gaseosa o jugo natural? Si no, necesito tu nombre, teléfono y dirección para confirmar el pedido.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia, lamento la situación. Voy a pasarlo con el equipo para que te ayuden con el cobro. ¿Hay algo más que quieras agregar?

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría añadir una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, necesito tus datos para cerrar el pedido: tu nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para comenzar, necesito tu nombre, teléfono y qué día y hora te gustaría agendar la cita. ¿Cuál es tu disponibilidad?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Claro, puedes pagar por transferencia. Solo necesito que me des tu nombre, teléfono y la fecha y hora que prefieres para la cita.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también recibimos pagos por Nequi. ¿Te gustaría usarlo? Para avanzar, necesito tu nombre, teléfono y la fecha y hora que prefieres para la cita.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero Agenda Clinica Pro está enfocada en clínicas y consultorios. Si necesitas agendar citas para ese tipo de servicio, puedo ayudarte. ¿Te gustaría saber más sobre cómo funciona para clínicas?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, necesito tu teléfono y la fecha y hora que prefieres para la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, ahora solo falta que me digas la fecha y hora que prefieres para la cita, y así agendamos.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, envíame aquí la captura del comprobante. Con eso, podremos confirmar tu cita y seguir adelante. ¿Te gustaría elegir la fecha y hora ahora?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo de nuevo los datos para pagar por Nequi. Cuando hagas el pago, envíame aquí la captura del comprobante.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando termines, envíame aquí la captura del comprobante para que podamos continuar con la confirmación de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en coordinar una cita y le interesa el producto Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus es ideal para gestionar y confirmar las citas de tus clientes. Tiene un costo de COP 140.000 por implementación y COP 170.000 al mes. ¿Te gustaría saber más sobre cómo puede ayudarte a organizar tu agenda?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito tu número de teléfono y el día y hora en que te gustaría empezar con Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita. ¿Qué día y hora te gustaría?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ¿cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago? También puedo ofrecerte financiación con Addi o Sistecredito.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre completo y el día y hora que deseas agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial elección! Para agendar Agenda Plus, necesito tu nombre, teléfono y los detalles de la cita: día y hora que prefieres. El equipo te confirmará la agenda.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, por favor, comparte tu nombre, teléfono y los detalles de la cita: día y hora que prefieres.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora prefieres. ¿Qué datos me puedes dar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita que deseas. ¿Qué día y hora te gustaría?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál medio prefieres usar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles sobre el día y hora que prefieres.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos de pago para continuar?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus te ayudará a gestionar y confirmar citas de manera eficiente. Para agendar, necesito tu nombre, teléfono y los detalles de la cita que deseas. ¿Qué día y hora te gustaría?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude mejor. Un momento, por favor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y solicitó hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye la gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, ¿me puedes dar tu nombre, teléfono y las fechas y horas que prefieres?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia y lamento la situación. Te voy a pasar con el equipo para que puedan revisar tu caso y darte una solución.

*[2] Nota para el equipo:* El cliente está interesado en el producto Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus te ayudará a gestionar y confirmar citas de manera eficiente. Necesito tu nombre, teléfono y qué día y hora te gustaría agendar la cita. ¿Cuál es tu disponibilidad?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, te enviaré los datos para la transferencia. Por favor, indícame tu nombre y número de teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes algún horario en mente?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. Una vez tengamos tus datos y agendemos, te puedo enviar la información de pago. ¿Qué día y hora prefieres para tu cita?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también recibimos pagos por Nequi. Si prefieres usar ese medio, una vez agendemos tu cita, te puedo enviar los datos. ¿Qué día y hora te gustaría agendar?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero nosotros estamos enfocados en clínicas y consultorios para agendar citas. Si necesitas ayuda con la agenda de tu tienda de ropa, puedo pasarte con el equipo para que te orienten mejor.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito que me confirmes qué día y hora te gustaría agendar tu cita para Agenda Plus.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿qué día y hora te gustaría agendar tu cita para Agenda Plus?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez hagas el pago, me envías aquí la captura del comprobante. Luego, confirmaremos tu cita y te avisaremos el día y la hora. ¿Ya tienes el día y la hora en mente para agendar?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito que me confirmes qué día y hora te gustaría agendar tu cita para Agenda Plus.  
  
Datos para Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te dejo de nuevo los datos para pagar por Nequi. Una vez realices el pago, me envías aquí la captura del comprobante y coordinamos el día y la hora de tu cita para Agenda Plus.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez realices el pago, envíame la captura del comprobante. Luego coordinamos el día y la hora de tu cita. ¡Espero tu mensaje!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, dueño de una tienda de ropa, está interesado en coordinar una cita para el producto Agenda Plus y prefiere pagar por Nequi. Informó que ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus es ideal para gestionar y confirmar citas, ayudando a evitar que pierdas pacientes por demoras. Con su implementación y seguimiento, podrás organizar mejor tu agenda. ¿Te gustaría que agendemos una cita para que te cuente más sobre cómo funciona?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, necesito tu nombre, teléfono, y el día y hora que prefieres para la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita: día y hora. ¿Cuál sería tu preferencia?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, ya tengo tu número. Pero antes, necesito tu nombre y los detalles de la cita: día y hora. Una vez tengamos eso, te puedo enviar los datos de pago. ¿Qué día y hora prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito que me confirmes el día y la hora de tu cita para finalizar la agendación.  
  
Datos para pagar por Nequi:  
  
¿Cuál sería tu preferencia para la cita?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres. ¿Cuál sería tu disponibilidad?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, teléfono y el día y hora que prefieres para agendar tu cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus te ayudará a gestionar y confirmar tus citas. Para agendar, necesito tu nombre, número de teléfono y qué día y hora te gustaría. ¿Tienes alguna preferencia?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría realizar la consignación? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B y link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar. ¿Cuál es tu disponibilidad?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál medio prefieres usar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar. ¿Qué día y hora tienes en mente?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. Si decides avanzar con Agenda Plus, puedo enviarte los datos para realizar el pago. ¿Te gustaría continuar?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con una persona del equipo para que te ayude mejor.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 por implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Cuál es tu disponibilidad?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te voy a pasar con el equipo para que puedan ayudarte a resolverlo. Un momento, por favor.

*[2] Nota para el equipo:* El cliente está interesado en el producto Agenda Plus. Mencionó que le cobraron dos veces y está muy molesto por la falta de respuesta.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Excelente elección. La Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Me puedes dar esos datos?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia (ahorros). Ahora, por favor, dame tu nombre, teléfono y el día y hora que prefieres para agendar.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes ya algo en mente?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia, entre otros medios. ¿Te gustaría que te envíe los datos de pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos de pago para que puedas proceder?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero Agenda Plus está diseñado para clínicas y consultorios. Si necesitas gestionar citas en tu tienda, podría no ser la mejor opción. ¿Te gustaría explorar alguna otra solución para tu negocio?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito también tu teléfono y qué día y hora te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿qué día y hora te gustaría agendar la cita?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: una vez que hagas el pago, me envías aquí la captura del comprobante. Con eso, agendamos tu cita y el equipo te confirmará el día y la hora. ¿Te parece bien?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí estaré cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito también tu teléfono y qué día y hora te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te dejé los datos para pagar por Nequi más arriba en el chat. Solo necesitas hacer el pago y enviarme la captura del comprobante. Luego, agendamos tu cita. Si necesitas que te los envíe de nuevo, dime y lo hago.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, una vez que hagas el pago, envíame la captura del comprobante. Así agendamos tu cita. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* El cliente, Juan Camilo, dueño de una tienda de ropa, está interesado en gestionar citas y le interesa Agenda Plus. Prefiere pagar por Nequi y ya realizó el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola Laura, Agenda Plus es ideal para gestionar y confirmar citas, ayudando a ordenar tu disponibilidad y evitar perder pacientes. ¿Te gustaría saber más sobre cómo funciona o cómo podría ayudarte específicamente en tu tienda?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, compárteme tu nombre, teléfono y los detalles de la cita que deseas agendar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial elección! Agenda Plus incluye gestión y confirmación de citas. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría que te contacte el equipo para confirmar el día y la hora.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, sólo falta tu nombre y la fecha que prefieres para que el equipo te contacte. Una vez tengamos esos datos, te puedo enviar los medios de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Solo necesito tu nombre para completar la agenda:  
  
¿Cuál es tu nombre?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación más COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de día y hora que prefieras. ¿Cuál día y hora te gustaría?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, también necesito tu nombre, teléfono y detalles de día y hora para agendar tu cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes alguna preferencia?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial elección! La Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita: día y hora que prefieres.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o mediante un link de pago. ¿Cuál medio prefieres usar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial elección! Agenda Plus incluye gestión de agenda y confirmación de citas. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Tienes ya alguna fecha en mente?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te enviara los datos de pago una vez agendemos la cita?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Agenda Plus incluye gestión y confirmación de citas. El costo de implementación es COP 140.000 y luego COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y cuándo te gustaría empezar.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Te paso con el equipo para que te atiendan.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y solicitó hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial! Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y qué día y hora te gustaría. ¿Me puedes dar esos datos?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho la situación. Te pasaré con el equipo para que puedan revisar tu caso y darte una solución.

*[2] Nota para el equipo:* El cliente está molesto porque le cobraron dos veces y nadie le responde. Mencionó que le interesa Agenda Plus.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y el día y hora que prefieres. ¿Cuándo te gustaría empezar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, te enviaré los datos para la transferencia a Bancolombia. Por favor, indícame tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
