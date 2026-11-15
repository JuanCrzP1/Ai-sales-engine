# Estándar del asesor: modelo_r2_gpt6luna_20261114

**NO PASA** · código `48d37ce + cambios` · modelo `openai/gpt-6-luna` · juez `google/gemini-2.5-flash` · 90 conversaciones (3 muestras por negocio: asesor_ai_prod, clinic, restaurant)

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
| ❌ responde lo que preguntan (juez) | 88 de 90 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 85 de 90 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 90 de 90 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ❌ no dice nada falso del pago (juez) | 88 de 90 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 87 de 90 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 90 de 90 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 90 de 90 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 90 de 90 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0570 · juez USD 0.0337. Llamadas al modelo por mensaje: 2.06. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 26.

Por cada mensaje del cliente: responde en 3.1 s (el 5 % más lento, 5.3 s o más) · USD 0.2 por cada 1.000 mensajes · fuera de formato: 0 de 288 · sin respuesta de la IA: 2 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **responde lo que preguntan** · asesor_ai_prod · pregunta a dónde consigna · turno 2: Ignora la pregunta del cliente sobre el número para consignar.
  - Cliente: «¿A qué número te consigno?»
  - Asesor: «¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?»
- **responde lo que preguntan** · restaurant · pregunta si tienen un medio · turno 2: No responde si tienen Nequi, que sí está en la ficha.
  - Cliente: «¿Tienen Nequi?»
  - Asesor: «Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre del cliente, que ya lo dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Sí! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, envíame tu nombre completo, teléfono y detalles de cómo atiendes tus ventas por WhatsApp. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 3: El asesor pide el nombre del cliente, que ya lo dio.
  - Cliente: «¿Y ahora qué sigue?»
  - Asesor: «Te explico: arriba, en este chat, tienes los datos para pagar por Nequi. Haz el pago y envíame aquí una captura del comprobante. También envíame tu nombre completo, teléfono y detalles de cómo atiendes tus ventas por WhatsApp para seguir con la configuración.»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre completo que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, compárteme tu nombre completo, teléfono y los detalles de cómo atiendes a tus clientes por WhatsApp. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 3: El asesor pide el nombre completo que el cliente ya dio.
  - Cliente: «¿Y ahora qué sigue?»
  - Asesor: «Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante. También envíame tu nombre completo, teléfono y los detalles de cómo atiendes a tus clientes por WhatsApp; con eso seguimos.»
- **no pide lo ya dado** · restaurant · pide el medio con un error de escritura · turno 2: El asesor vuelve a preguntar la cantidad y el tipo de entrega.
  - Cliente: «Pásame el nekui porfa»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local? ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 7: El asesor vuelve a preguntar por el negocio del cliente.
  - Cliente: «Mi teléfono es 3157778899»
  - Asesor: «Gracias, Juan Camilo. Como Agenda Plus está pensado para clínicas y consultorios, no parece ajustarse a tu tienda de ropa. ¿Tu negocio también ofrece algún servicio de salud?»
- **no pide lo ya dado** · clinic · da su teléfono antes de pagar · turno 3: El asesor vuelve a pedir el nombre del cliente.
  - Cliente: «Listo, por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para coordinar la agenda, ¿me compartes tu nombre y los detalles del servicio que necesitas? ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no dice nada falso del pago** · restaurant · el chat de producción · turno 11: El asesor dice que no se volvieron a enviar los datos, pero sí se enviaron.
  - Cliente: «Cómo así»
  - Asesor: «Perdón, me expliqué mal. Ya tienes los datos de Nequi en los mensajes anteriores del chat; no se volvieron a enviar. Busca el mensaje donde aparecen y, cuando pagues, mándame aquí la captura del comprobante.»
- **no dice nada falso del pago** · restaurant · pregunta si tienen un medio · turno 2: Dice que no puede responder, pero Nequi sí está en la ficha.
  - Cliente: «¿Tienen Nequi?»
  - Asesor: «Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: No explica qué debe hacer, solo repite la instrucción.
  - Cliente: «Cómo así»
  - Asesor: «Perdón, me expliqué mal. Ya te envío de nuevo los datos de Nequi aquí debajo. Cuando hagas el pago, envíame la captura del comprobante por este chat.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: No explica qué debe hacer, solo repite que ya le envió los datos.
  - Cliente: «Cómo así»
  - Asesor: «Perdón, me expresé mal. Ya te había enviado los datos de Nequi arriba en el chat; busca ese mensaje para hacer el pago y luego envíame aquí la captura del comprobante.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 11: No explica qué debe hacer, solo repite que enviará los datos.
  - Cliente: «Cómo así»
  - Asesor: «Perdón, me expliqué mal: no te llegó ningún dato nuevo. Te los envío de nuevo por Nequi aquí debajo.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Perfecto! Para iniciar con el Plan Básico, el primer mes es COP 210.000 por la configuración y el primer mes; luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para dejar listo el arranque, envíame tu nombre, teléfono y algunos detalles de tu negocio.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). El primer mes es COP 210.000 y luego COP 110.000 al mes. Cuando quieras avanzar con el pago, te comparto los datos.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también recibimos Nequi. Si vas a pagar por ese medio, te comparto los datos.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Anoto que es una tienda de ropa. Para completar el arranque, compárteme tu teléfono y algunos detalles de cómo venden por WhatsApp; después seguimos con el pago por Nequi.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar el arranque, envíame tu teléfono y cuéntame qué pasa después del primer mensaje: ¿hacen seguimiento o las conversaciones se quedan ahí?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono y que tienes una tienda de ropa. Haz el pago con los datos de Nequi que te dejé arriba y envíame aquí la captura del comprobante; con eso seguimos con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, envíame por aquí la captura del comprobante. El equipo verificará el pago y te guiará con el siguiente paso para activar el servicio.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, te dejo de nuevo los datos para pagar por Nequi aquí abajo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expresé mal. Los datos de Nequi te aparecerán debajo de este mensaje. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hagas el pago envíame por aquí la captura del comprobante para continuar con la activación.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa, le interesa el Plan Básico y eligió pagar por Nequi. Dice que ya consignó.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, compárteme tu teléfono y algunos detalles de cómo atiendes tus conversaciones.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, compárteme tu teléfono y algunos detalles de cómo atiendes tus conversaciones.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos de Nequi. Haz el pago con esos datos y envíame aquí la captura del comprobante. También compárteme tu teléfono y algunos detalles de cómo atiendes las conversaciones para seguir con la activación.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes pagas COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio. Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias, ya tengo tu número. Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. También me falta tu nombre y los detalles de tu negocio para iniciar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 (configuración + mensualidad); luego COP 110.000 al mes. No incluye costos de Meta ni de tokens de IA. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, confirmamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes pagas COP 210.000; luego, COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes; el primer mes son COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para arrancar, envíame tu nombre, teléfono y los detalles de tu negocio. Luego puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. Dime cuál medio prefieres y te comparto los datos.

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, confirmamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes pagas COP 210.000 y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, envíame tu nombre, teléfono y detalles de tu negocio. Luego eliges el medio de pago disponible.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. Si te sirve, te envío los datos para pagar por ese medio.

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes pagas COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, envíame tu nombre, teléfono y detalles de tu negocio. También dime cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat para que te acompañe con el Plan Básico.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes queda en COP 210.000 y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio; después eliges el medio de pago.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia; lamento que te hayan cobrado dos veces y no hayas recibido respuesta. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y reclama que le cobraron dos veces y nadie le responde. Indica que está muy molesto.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes son COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y un detalle de cómo usarías el asistente. Luego te indico cómo pagar.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para completar el inicio, compárteme tu nombre, teléfono y un detalle de cómo usarías el asistente.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Perfecto. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; puedes cancelar mensualmente. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio. Después te indico cómo pagar.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). También tienes Nequi, Daviplata, Bre-B y link de pago. ¿Cuál medio prefieres para avanzar?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar por Nequi. Si te sirve, te envío los datos para que puedas avanzar.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Para dejar listo el arranque del Plan Básico, me falta tu teléfono y los detalles de tu tienda.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ya tengo tu nombre y que es una tienda de ropa; compárteme tu teléfono para continuar con el arranque.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono y que tienes una tienda de ropa. Cuando hagas el pago por Nequi, envíame aquí el comprobante para continuar con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, envíame aquí una captura del comprobante. Con eso el equipo verifica el pago y seguimos con la activación.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal: los datos de Nequi deberían aparecer debajo de mi mensaje. Si no los ves, te los reenvío por aquí.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hagas el pago envíame aquí la captura del comprobante para que el equipo lo verifique y podamos seguir con la activación.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa el Plan Básico, con pago por Nequi. Dice que ya consignó.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico cuesta COP 100.000 de implementación + COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente; no incluye costos de Meta, tokens de IA ni personalización avanzada. El primer mes pagas COP 210.000 y luego COP 110.000 mensuales, sin permanencia obligatoria. Para arrancar, envíame tu nombre completo, teléfono y detalles de cómo atiendes tus ventas por WhatsApp.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Sí! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, envíame tu nombre completo, teléfono y detalles de cómo atiendes tus ventas por WhatsApp.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, tienes los datos para pagar por Nequi. Haz el pago y envíame aquí una captura del comprobante. También envíame tu nombre completo, teléfono y detalles de cómo atiendes tus ventas por WhatsApp para seguir con la configuración.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: el primer mes cuesta COP 210.000 (COP 100.000 de implementación + COP 110.000 del mes) y luego COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio. ¿Con qué medio de pago prefieres continuar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias, ya tengo tu número. Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. Dime cuál prefieres y te comparto los datos para continuar.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Envíame también tu nombre y los detalles de tu negocio para iniciar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: el primer mes cuesta COP 210.000 (COP 100.000 de implementación + COP 110.000 del mes) y luego COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego eliges el medio de pago: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. También compárteme tu nombre, teléfono y los detalles de tu negocio para iniciar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: el primer mes cuesta COP 210.000 (COP 100.000 de implementación + COP 110.000 del mes) y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio; después eliges el medio de pago.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes pagas COP 210.000; incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes son COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para arrancar, compárteme tu nombre, teléfono y algunos detalles de tu negocio; luego te indico cómo pagar.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. Si te sirve, te envío los datos para pagar por ese medio.

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes pagas COP 210.000 y luego COP 110.000 mensuales; incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para arrancar, envíame tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat para continuar con el Plan Básico.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes son COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego eliges el medio de pago.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia; que te hayan cobrado dos veces y no recibas respuesta es muy frustrante. Te paso con el equipo por este mismo chat para que revisen el cobro contigo.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y reclama que le cobraron dos veces y nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: el primer mes cuesta COP 210.000 (COP 100.000 de implementación + COP 110.000 del mes) y luego COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Envíame también tu nombre, teléfono y los detalles de tu negocio para avanzar con la activación.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Perfecto, arrancamos con el Plan Básico. El primer mes cuesta COP 210.000: COP 100.000 de implementación y COP 110.000 del sistema mensual; después pagas COP 110.000 al mes. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio. Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). Para arrancar con el Plan Básico, envíame tu nombre, teléfono y los detalles de tu negocio.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Si te sirve, puedo enviarte los datos de pago.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ya tengo tu nombre y que es una tienda de ropa. Para dejar listo el inicio, envíame tu teléfono y un poco más de detalle sobre cómo atienden y hacen seguimiento por WhatsApp.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Cuando hagas el pago, envíame tu teléfono y el comprobante para continuar con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono. Cuando hagas el pago por Nequi, envíame aquí la captura del comprobante y seguimos con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago por Nequi, envíame aquí una captura del comprobante. El equipo verificará el pago y seguimos con la activación.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, te lo envío de nuevo; los datos de Nequi te quedan debajo. Cuando hagas el pago, envíame aquí la captura del comprobante.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal. Ya te envío de nuevo los datos de Nequi aquí debajo. Cuando hagas el pago, envíame la captura del comprobante por este chat.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto. Cuando completes el pago por Nequi, envíame aquí la captura del comprobante para que el equipo lo verifique y podamos seguir con la activación.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa el Plan Básico, que eligió pagar por Nequi. Dice que ya consignó.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Claro, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000: COP 100.000 de implementación y COP 110.000 del mes; después, COP 110.000 mensuales. No incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, compárteme tu nombre completo, teléfono y los detalles de cómo atiendes a tus clientes por WhatsApp.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, compárteme tu nombre completo, teléfono y los detalles de cómo atiendes a tus clientes por WhatsApp.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante. También envíame tu nombre completo, teléfono y los detalles de cómo atiendes a tus clientes por WhatsApp; con eso seguimos.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: el primer mes cuesta COP 210.000 e incluye la configuración inicial y el asistente conversacional; luego son COP 110.000 al mes. No incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, envíame tu nombre, teléfono y detalles de tu negocio. ¿Con qué medio de pago prefieres continuar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias, ya tengo tu número. Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. Dime cuál medio prefieres y te envío los datos para continuar.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, envíame también tu nombre y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes son COP 210.000 e incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego eliges el medio de pago.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar el arranque del Plan Básico, envíame tu nombre, teléfono y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes, sin permanencia obligatoria. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio. ¿Con qué medio de pago prefieres continuar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 (configuración + primer mes); luego COP 110.000 mensuales, sin permanencia obligatoria. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio. Luego te indico cómo pagar.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. Si te sirve, te envío los datos para que puedas pagar.

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes; puedes cancelar mensualmente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes; el primer mes queda en COP 210.000 y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego te paso las opciones de pago.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia; que te hayan cobrado dos veces y no recibas respuesta es muy frustrante. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y reclama que le cobraron dos veces y nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes son COP 210.000 y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para iniciar, compárteme también tu nombre, teléfono y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Claro. La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y la prefieres a domicilio en El Poblado o Laureles, o para recoger?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio o recoger en el local?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. ¿Cuántas Hamburguesas Sencillas quieres y cuál es la dirección de entrega? El domicilio está disponible en El Poblado y Laureles.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago por Nequi, envíame aquí una captura del comprobante. Con eso seguimos con tu pedido.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando estés listo, seguimos con tu pedido.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expresé mal. Ya te había enviado los datos de Nequi arriba en el chat; busca ese mensaje para hacer el pago y luego envíame aquí la captura del comprobante.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando hagas el pago envíame aquí la captura del comprobante y seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en empezar con una Hamburguesa Sencilla y eligió pagar por Nequi. Dice que ya consignó.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro, Laura! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Te confirmo 1 Hamburguesa Sencilla por COP 18.000. Para completar el pedido, compárteme tu teléfono y, si es a domicilio, la dirección. El domicilio cuesta COP 4.000 en El Poblado y Laureles.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago y envíame aquí la captura del comprobante. También compárteme tu teléfono y, si quieres domicilio, la dirección; si prefieres recoger, dime eso.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar el pedido, dime cuántas Hamburguesas Sencillas quieres y si prefieres domicilio en El Poblado o Laureles, o recoger en el local.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, ¿cuántas Hamburguesas Sencillas quieres y en qué zona estás: El Poblado o Laureles, para domicilio; o prefieres recoger en el local?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Claro, la Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y sería a domicilio o para recoger?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. ¿Quieres que te envíe los datos para pagar con ese medio?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Listo, una Hamburguesa Sencilla por COP 18.000. ¿La quieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Claro, una Hamburguesa Sencilla por COP 18.000. ¿La quieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Qué mal, entiendo tu molestia. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quería una Hamburguesa Sencilla y reclama que le cobraron dos veces y nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla — COP 18.000. ¿La quieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para completar el pedido, dime tu nombre, teléfono y si lo quieres a domicilio o para recoger. Si es a domicilio, envíame también la dirección.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Claro! La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio o recoger en el local?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio o recoger en el local?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Mucho gusto, Juan Camilo. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar el pedido, dime cuántas Hamburguesas Sencillas quieres y si prefieres domicilio en El Poblado o Laureles, o recoger en el local.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago por Nequi, envíame aquí la captura del comprobante. Con eso seguimos con tu pedido.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal. Ya tienes los datos de Nequi en los mensajes anteriores del chat; no se volvieron a enviar. Busca el mensaje donde aparecen y, cuando pagues, mándame aquí la captura del comprobante.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando termines el pago envíame aquí la captura del comprobante y seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en empezar con Hamburguesa Sencilla y eligió pagar por Nequi. Dice que ya consignó.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro, Laura! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio o recoger en el local?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y me compartes tu teléfono y, si es domicilio, la dirección?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago y envíame aquí la captura del comprobante. También confírmame cuántas Hamburguesas Sencillas quieres y si prefieres domicilio o recoger.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Claro. La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres para enviarte los datos de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar el pedido de la Hamburguesa Sencilla, ¿cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Claro, una Hamburguesa Sencilla por COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Listo, Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y la prefieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿La quieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿La quieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. ¿La Hamburguesa Sencilla la quieres a domicilio o para recoger?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y la prefieres a domicilio en El Poblado o Laureles, o para recoger?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat para ayudarte con el pedido.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia, qué mal que te hayan cobrado dos veces y no te respondan. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quería una Hamburguesa Sencilla y reclama que le cobraron dos veces y nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y sería a domicilio en El Poblado o Laureles, o para recoger?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). También recibimos Nequi, Daviplata y Bre-B. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio o recoger?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Si quieres, te envío los datos cuando estés listo para pagar. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio o recoger?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar el pedido, ¿cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono. ¿Cuántas hamburguesas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago por Nequi, envíame aquí la captura del comprobante. Con eso seguimos con tu pedido.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando tengas el comprobante, envíamelo por aquí.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal: no te llegó ningún dato nuevo. Te los envío de nuevo por Nequi aquí debajo.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto. Cuando hagas el pago, envíame aquí la captura del comprobante para seguir con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en empezar con una Hamburguesa Sencilla y pagar por Nequi. Dice que ya consignó.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Claro, Laura! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y envíame aquí la captura del comprobante; con eso seguimos.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Claro, una Hamburguesa Sencilla por COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. Para dejar listo el pedido, ¿cuántas Hamburguesas Sencillas quieres y prefieres domicilio o recoger?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, ¿cuántas Hamburguesas Sencillas quieres? Cada una cuesta COP 18.000.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Cuántas Hamburguesas Sencillas quieres? Cada una cuesta COP 18.000.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Te dejo abajo los datos para pagar por transferencia a Bancolombia. ¿Me confirmas cuántas Hamburguesas Sencillas quieres y si prefieres domicilio o recoger en el local?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! La Hamburguesa Sencilla cuesta COP 18.000 e incluye carne artesanal, queso y vegetales frescos. ¿Cuántas quieres y las prefieres a domicilio o para recoger?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál medio prefieres para seguir con tu pedido?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y sería a domicilio en El Poblado o Laureles, o para recoger?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! La Hamburguesa Sencilla cuesta COP 18.000. ¿Cuántas quieres y prefieres domicilio en El Poblado o Laureles, o recoger en el local?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con alguien del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Listo! Hamburguesa Sencilla — COP 18.000. ¿Cuántas quieres y la prefieres a domicilio en El Poblado o Laureles, o para recoger?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Qué mal que te hayan cobrado dos veces y no te respondan; entiendo tu molestia. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quería una Hamburguesa Sencilla y reclama que le cobraron dos veces y nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿La prefieres a domicilio en El Poblado o Laureles, o para recoger en el local?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para completar el pedido, dime tu nombre, teléfono y si lo quieres a domicilio o para recoger.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Claro! Agenda Plus incluye gestión y confirmación de citas. La implementación cuesta COP 140.000 y luego son COP 170.000 al mes; los costos de plataformas externas no están incluidos. Para avanzar, compárteme tu nombre, teléfono, detalles de la clínica y qué día y hora te convienen. El equipo te confirma la disponibilidad.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). ¿Quieres que te comparta los datos?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Quieres que te comparta los datos para pagar por ese medio?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Agenda Plus está pensado para clínicas y consultorios, así que no parece ajustarse a una tienda de ropa. ¿Buscas gestionar citas para algún servicio de salud?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para orientarte bien: Agenda Plus está pensado para clínicas y consultorios, no para tiendas de ropa. ¿La tienda también ofrece algún servicio de salud?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Como Agenda Plus está pensado para clínicas y consultorios, no parece ajustarse a tu tienda de ropa. ¿Tu negocio también ofrece algún servicio de salud?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, envíame aquí la captura del comprobante. Ten en cuenta que Agenda Plus está pensado para clínicas y consultorios; no parece ajustarse a una tienda de ropa.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal. Los datos de Nequi te aparecen debajo de este mensaje. Cuando hagas el pago, envíame por aquí la captura del comprobante.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto. Cuando hagas el pago, envíame aquí la captura del comprobante y seguimos.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa empezar con Agenda Plus; dijo que pagaría por Nequi. Afirma que ya consignó.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola, Laura. Agenda Plus está pensado para clínicas y consultorios; incluye gestión y confirmación de citas, con un costo de COP 140.000 de implementación + COP 170.000 al mes. ¿Tu tienda también ofrece servicios que se agendan con cita?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para avanzar, ¿me compartes tu teléfono y qué servicio con cita quieres gestionar?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago y envíame aquí la captura del comprobante; con eso seguimos. También compárteme tu teléfono y qué servicio con cita quieres gestionar.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus gestiona y confirma citas; cuesta COP 140.000 de implementación + COP 170.000 al mes. Para coordinar la cita y que el equipo confirme día y hora, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para coordinar la cita, compárteme tu nombre y los detalles de tu clínica.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes e incluye gestión y confirmación de citas. Para coordinar el inicio, ¿me compartes tu nombre y teléfono, y qué días y horarios te sirven?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes e incluye gestión y confirmación de citas. Para avanzar, ¿me compartes tu nombre, teléfono y los detalles de la clínica? Luego coordinamos día y hora para que el equipo confirme la agenda.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Agenda Plus incluye gestión y confirmación de citas: COP 140.000 de implementación + COP 170.000 al mes. Para avanzar, compárteme tu nombre, teléfono y los detalles de tu clínica; el equipo coordina contigo el día y la hora.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. También ofrecen financiación con Addi o Sistecrédito. ¿Qué medio prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes e incluye gestión y confirmación de citas. Para coordinar la agenda, ¿me compartes tu nombre, teléfono y los días y horarios que te funcionan?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. ¿Quieres que te envíe los datos para pagar Agenda Plus?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Agenda Plus incluye gestión y confirmación de citas. La implementación cuesta COP 140.000 y luego COP 170.000 al mes; no incluye costos de plataformas externas. Para avanzar, compárteme tu nombre, teléfono y los detalles de tu clínica. ¿Qué día y hora te gustaría coordinar?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes. Incluye gestión y confirmación de citas; los costos de plataformas externas no están incluidos. Para coordinar el día y la hora, ¿me compartes tu nombre, teléfono y los detalles de la clínica?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho el cobro duplicado y que no hayas recibido respuesta. Te paso con el equipo por este mismo chat para que revisen lo ocurrido.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Reclama que le cobraron dos veces y que nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación + COP 170.000 al mes. Para coordinar día y hora, ¿me compartes tu nombre, teléfono y los detalles de la agenda que necesitas?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para coordinar la agenda, compárteme tu nombre, teléfono y los detalles que necesitas.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación + COP 170.000 al mes, con pago mensual. Para avanzar, compárteme tu nombre, teléfono y qué día y hora te convienen; el equipo te confirma la disponibilidad.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). ¿Quieres que coordinemos el inicio de Agenda Plus?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Quieres que te enviemos los datos de pago por ese medio?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Agenda Plus está pensado para clínicas y consultorios, así que una tienda de ropa no corresponde al servicio que ofrecemos. ¿Tu negocio también tiene una clínica o consultorio?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para continuar, ¿me compartes tu teléfono y qué día y hora te convienen? El servicio está pensado para clínicas y consultorios.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Como me comentaste que tienes una tienda de ropa, Agenda Plus no corresponde a tu negocio: está pensado para clínicas y consultorios. No sigas con el pago; puedo consultarlo con el equipo si tienen alguna opción para tiendas.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, envíame aquí una captura del comprobante para que el equipo lo revise. Pero como tienes una tienda de ropa, Agenda Plus está pensado para clínicas y consultorios; mejor no pagues hasta confirmar con el equipo si aplica para tu negocio.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí quedo pendiente.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Sí, te lo envío de nuevo. Solo ten presente que Agenda Plus está pensado para clínicas y consultorios; como tienes una tienda de ropa, no pagues hasta confirmar con el equipo si aplica para tu negocio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: Agenda Plus está diseñado para clínicas y consultorios, así que no está confirmado que aplique para una tienda de ropa. Por eso te recomendé esperar antes de pagar. ¿Quieres que lo consulte con el equipo?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Entiendo. Antes de pagar, te recomiendo confirmar con el equipo si Agenda Plus aplica para tu tienda de ropa, porque está pensado para clínicas y consultorios. ¿Quieres que te pase con el equipo?

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa Agenda Plus; eligió pagar por Nequi. Dice que ya consignó.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola, Laura. Agenda Plus está pensado para clínicas y consultorios: incluye gestión y confirmación de citas por COP 140.000 de implementación + COP 170.000 al mes. ¿Qué te gustaría resolver con tu tienda de ropa?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para avanzar, ¿me compartes tu teléfono y qué día y hora te quedarían bien para coordinar la cita?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, ya te dejé los datos de Nequi. Haz el pago con esos datos y envíame aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes e incluye gestión y confirmación de citas. Para coordinar el día y la hora, ¿me compartes tu nombre, teléfono y los detalles de la agenda que necesitas?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias. Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para coordinar la agenda, ¿me compartes tu nombre y los detalles del servicio que necesitas?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación + COP 170.000 al mes. Para coordinar día y hora, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para coordinar la agenda, compárteme tu nombre, teléfono y los detalles de tu clínica.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes e incluye gestión y confirmación de citas. Para coordinar el inicio, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. ¿Cuál medio prefieres?

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión de agenda y confirmación de citas: COP 140.000 de implementación + COP 170.000 al mes. Para coordinar el día y la hora, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. ¿Cuál medio prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus gestiona y confirma citas; cuesta COP 140.000 de implementación + COP 170.000 al mes. Para avanzar, coordinamos día y hora y el equipo confirma la disponibilidad. ¿Me compartes tu nombre, teléfono y los detalles de la clínica?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. ¿Quieres que te comparta los datos para pagar por ese medio?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas por COP 140.000 de implementación + COP 170.000 al mes. Para coordinar día y hora, ¿me compartes tu nombre, teléfono y qué día y horario te convienen? El equipo te confirma la disponibilidad.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Incluye gestión y confirmación de citas; no incluye costos de plataformas externas. Para avanzar, ¿me compartes tu nombre, teléfono y los detalles de la agenda que necesitas? El equipo coordina y confirma día y hora.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia; que te cobren dos veces y no te respondan es muy frustrante. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Reclama que le cobraron dos veces y que nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Agenda Plus incluye gestión de agenda y confirmación de citas. Cuesta COP 140.000 de implementación + COP 170.000 al mes; no incluye costos de plataformas externas. Para avanzar, ¿me compartes tu nombre, teléfono y qué días y horarios te sirven para coordinar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. También compárteme tu nombre, teléfono y los días y horarios que te sirven para coordinar.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Agenda Plus incluye gestión y confirmación de citas. La implementación cuesta COP 140.000 y luego COP 170.000 al mes. Para avanzar, compárteme tu nombre, teléfono y los días y horarios que te sirven; el equipo te confirma la disponibilidad.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). También aceptamos Nequi, Daviplata, Bre-B y link de pago. ¿Prefieres transferencia para avanzar?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también recibimos Nequi. ¿Te sirve pagar por ese medio para avanzar?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Agenda Plus está pensado para clínicas y consultorios. Como tienes una tienda de ropa, voy a consultar con el equipo si también pueden ayudarte.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Perfecto, Juan Camilo. Te paso los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono. Para avanzar con la agenda, compárteme qué necesitas y qué día y hora te sirven; el equipo te confirma la disponibilidad.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, envíame aquí una captura del comprobante. El equipo lo verifica y te guía con el siguiente paso.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí estaré.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, te dejo de nuevo los datos para pagar por Nequi aquí abajo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal: los datos de Nequi deberían aparecer aquí debajo de mi mensaje. Si no los ves, dime y lo reviso con el equipo.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto. Cuando completes el pago, envíame aquí la captura del comprobante y seguimos con el proceso.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa Agenda Plus; eligió pagar por Nequi. Dice que ya consignó.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** Hola, Laura. Agenda Plus está pensado para clínicas y consultorios: gestiona y confirma citas, y cuesta COP 140.000 de implementación + COP 170.000 al mes. ¿Buscas organizar citas para tu tienda o trabajas también con una clínica?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para avanzar, ¿me compartes también tu teléfono y los detalles de la agenda que necesitas?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago y me envías aquí la captura del comprobante; después, compárteme tu teléfono y los detalles de la agenda que necesitas.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus cuesta COP 140.000 de implementación + COP 170.000 al mes e incluye gestión y confirmación de citas. Para coordinar la agenda, ¿me compartes tu nombre, teléfono y qué día y hora te convienen?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias. Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál medio prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Me compartes tu nombre y qué día y hora te convienen para coordinar la agenda?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus gestiona la agenda y confirma las citas; cuesta COP 140.000 de implementación + COP 170.000 al mes. Para coordinar el día y la hora, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para coordinar la cita de Agenda Plus, compárteme también tu nombre, teléfono y los detalles de tu clínica.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión de agenda y confirmación de citas. La implementación cuesta COP 140.000 y luego COP 170.000 al mes; no incluye costos de plataformas externas. Para coordinar, ¿me compartes tu nombre, teléfono y qué día y hora te convienen? El equipo te confirma la disponibilidad.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas: COP 140.000 de implementación + COP 170.000 al mes. Para coordinar día y hora, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Agenda Plus incluye gestión y confirmación de citas. La implementación cuesta COP 140.000 y luego son COP 170.000 al mes; no incluye costos de plataformas externas. Para coordinar día y hora, ¿me compartes tu nombre, teléfono y los detalles de tu clínica?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. ¿Te envío los datos para que puedas pagar?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus gestiona y confirma citas; cuesta COP 140.000 de implementación + COP 170.000 al mes. Para avanzar, coordinamos día y hora y el equipo te confirma la disponibilidad. ¿Me compartes tu nombre, teléfono y qué día y hora prefieres?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente está interesado en Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas: cuesta COP 140.000 de implementación + COP 170.000 al mes. Para coordinar la agenda, ¿me compartes tu nombre, teléfono y qué día y hora te sirven? El equipo te confirma la disponibilidad.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia; lamento que te hayan cobrado dos veces y no hayas recibido respuesta. Te paso con el equipo por este mismo chat para que revisen el caso.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Reclama que le cobraron dos veces y que nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Claro. Agenda Plus incluye gestión y confirmación de citas; cuesta COP 140.000 de implementación + COP 170.000 al mes. Para coordinar la agenda, ¿me compartes tu nombre, teléfono y los días y horarios que te sirven?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para coordinar la agenda, compárteme tu nombre, teléfono y los días y horarios que te sirven.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
