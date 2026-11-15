# Estándar del asesor: modelo_r2_gemini25flash_20261114

**NO PASA** · código `48d37ce + cambios` · modelo `google/gemini-2.5-flash` · juez `google/gemini-2.5-flash` · 90 conversaciones (3 muestras por negocio: asesor_ai_prod, clinic, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 90 de 90 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 90 de 90 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 90 de 90 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 90 de 90 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 90 de 90 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ❌ pasa al equipo cuando debe (exacta) | 89 de 90 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 90 de 90 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 90 de 90 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 90 de 90 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 90 de 90 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 85 de 90 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 90 de 90 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 90 de 90 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 89 de 90 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 90 de 90 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 90 de 90 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ❌ nota fiel (juez) | 89 de 90 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.2539 · juez USD 0.0277. Llamadas al modelo por mensaje: 2.13. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 23.

Por cada mensaje del cliente: responde en 2.0 s (el 5 % más lento, 3.2 s o más) · USD 0.88 por cada 1.000 mensajes · fuera de formato: 6 de 288 · sin respuesta de la IA: 1 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **pasa al equipo cuando debe** · clinic · el chat de producción · turno 5: el chat pasó al equipo sin motivo
  - Cliente: «Me llamo Juan Camilo y es una tienda de ropa»
  - Asesor: «Gracias, Juan Camilo. Entiendo que tu negocio es una tienda de ropa. Te comento que Agenda Clínica Pro está diseñado específicamente para clínicas y consultorios de salud, ayudándolos a gestionar sus citas de manera eficiente.»
  - Nota para el equipo: «Juan Camilo, de una tienda de ropa, está interesado en Agenda Plus y preguntó si podía pagar con Nequi. El cliente quiere empezar.»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Con el Plan Básico, la implementación y el primer mes te costarían COP 210.000. Después, solo COP 110.000 mensuales. ¿Me confirmas tu nombre y teléfono para terminar de activar tu servicio? ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · asesor_ai_prod · da su teléfono antes de pagar · turno 3: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, ¿me podrías dar tu nombre completo para la activación? ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 2: El asesor pide el nombre que el cliente ya dio.
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «¡Claro que sí, Laura! Te dejo los datos para pagar por Nequi justo aquí abajo. Una vez que hagas el pago, por favor envíame tu nombre y número de teléfono para activar el servicio. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 6: El cliente ya había dado su nombre en el turno 5.
  - Cliente: «Te pago por Nequi»
  - Asesor: «¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. ⏎  ⏎ Para poder agendar la implementación de Agenda Plus, ¿me podrías confirmar tu número de teléfono y el nombre de tu clínica o consultorio? ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · clinic · el chat de producción · turno 6: Pide nombre y teléfono que el cliente ya dio.
  - Cliente: «Te pago por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, por favor, envíanos tu nombre completo y un número de teléfono para coordinar la implementación de Agenda Plus. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: El cliente dice 'cómo así' y el asesor no explica, solo repite la acción.
  - Cliente: «Cómo así»
  - Asesor: «Disculpa, parece que hubo un error. Te vuelvo a enviar los datos para pagar por Nequi.»
- **nota fiel** · clinic · el chat de producción · turno 13: El cliente no dijo que pagó el plan Agenda Plus.
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
  - Nota para el equipo: «Juan Camilo, de una tienda de ropa, ya pagó por Nequi el plan Agenda Plus y quiere que le confirmen el pago.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Excelente! Para el Plan Básico, el primer mes pagas COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. Con este plan, tu WhatsApp se convierte en un vendedor automático que responde al instante y da seguimiento a cada prospecto. ¿Te parece si coordinamos la activación y me compartes tus datos?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, claro que puedes transferir. Aceptamos transferencias a Bancolombia. ¿Con qué medio de pago te gustaría seguir para activar tu plan?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Te envío los datos para que actives tu Plan Básico?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Perfecto, Juan Camilo. Entendido que es para tu tienda de ropa. Para activar el Plan Básico y que empieces a convertir más ventas, ¿prefieres pagar con Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez hagas el pago, ¿me compartes tu número de teléfono y algún detalle adicional para la activación de tu Plan Básico?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu número. Ahora solo falta que me envíes el comprobante de pago por aquí para activar tu Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, me envías la captura del comprobante por este mismo chat. Con eso, nuestro equipo verifica y empezamos con la implementación guiada de tu Plan Básico.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí te espero.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí! Aquí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te envié los datos de Nequi justo debajo de este mensaje. Con esos datos puedes hacer el pago y luego me envías la foto del comprobante para que activemos tu Plan Básico.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Perfecto! Aquí te espero para que me envíes el comprobante y podamos activar tu Plan Básico.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, ya pagó el Plan Básico y quiere verificar su pago.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** ¡Hola, Laura! Qué bueno que te interese el Plan Básico. Con este plan, tu tienda de ropa tendrá un asistente que responde al instante y no perderás clientes por demoras. Para empezar, necesito tu nombre completo y número de teléfono.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Excelente, Laura! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, por favor, envíame el comprobante para activar tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Perfecto, Laura. Arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos para activar tu Plan Básico.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Para activarlo, solo necesito tu nombre y número de teléfono. ¿Me los compartes?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¡Perfecto! Con tu número ya podemos avanzar. Puedes pagar el Plan Básico a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o con un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, me avisas para que el equipo pueda verificarlo y arranquemos con la configuración.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Con el Plan Básico vas a poder automatizar tus respuestas y asegurar el seguimiento de tus clientes para no perder más ventas. Para empezar, necesito tu nombre y número de teléfono. Luego te explico cómo activamos el servicio y los medios de pago.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, por favor envíame tu nombre y número de teléfono para activar tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico te ayudará a automatizar tus respuestas y a mantener el seguimiento con tus clientes. Para empezar, necesito tu nombre y número de teléfono. Luego te doy las opciones de pago.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Para consignar, ¿prefieres Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Para activar el Plan Básico, que incluye la configuración inicial y el asistente conversacional inteligente, solo necesito tu nombre, teléfono y los detalles para la implementación. El primer mes son COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. ¿Con qué medio de pago te gustaría cancelar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. ¿Cuál prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a transformar tus chats en ventas. Con este plan, vas a tener la configuración inicial y el asistente conversacional inteligente para tu WhatsApp. El primer mes tiene un costo de COP 210.000 (implementación + primer mes) y luego son COP 110.000 mensuales. Te confirmo que no hay permanencia obligatoria, puedes cancelar cuando quieras. Para activar el servicio, necesito tu nombre y número de teléfono.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi sin problema.   
  
¿Te gustaría que te envíe los datos para que puedas hacer el pago del Plan Básico?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico te ayudará a que tu WhatsApp funcione como un vendedor automático. Para empezar, ¿me confirmas tu nombre y número de teléfono?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro que sí, con gusto te paso con alguien del equipo por este mismo chat para que te ayude con lo que necesites.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Con este plan, pagas COP 100.000 de implementación y luego COP 110.000 al mes. Incluye la configuración inicial, la guía de integración con WhatsApp y tu asistente conversacional inteligente. ¿Te gustaría que te envíe los datos para que podamos arrancar de inmediato?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia, lamento mucho lo que pasó. Voy a pasar tu caso directamente al equipo para que revisen lo de los cobros y se pongan en contacto contigo lo antes posible.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Dijo que le cobraron dos veces y que nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente decisión! Con el Plan Básico vas a poder responder al instante y mantener el seguimiento de tus prospectos. Para empezar, necesito tu nombre y número de teléfono. Luego te doy las opciones para pagar.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. ¿Con qué nombre y número de teléfono registramos tu Plan Básico?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Excelente! Con el Plan Básico vas a convertir tu WhatsApp en un vendedor automático 24/7. Para empezar, necesito tu nombre y número de teléfono. Luego te explico los métodos de pago.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, claro que puedes transferir. Tenemos Nequi, Daviplata y transferencia a Bancolombia. ¿Cuál prefieres para enviarte los datos?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, claro que puedes pagar con Nequi. ¿Te envío los datos de Nequi para que puedas hacer la transferencia?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu nombre. Para seguir con la activación del Plan Básico, ¿cuál de los medios de pago prefieres? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, me confirmas para que el equipo active tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu número de teléfono. Ahora, cuando hagas el pago por Nequi, me envías el comprobante por aquí para que el equipo active tu Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, por favor, envíame una captura del comprobante por este chat. Con eso, el equipo verifica y activa tu Plan Básico para que empieces a convertir tus conversaciones en ventas.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, Juan Camilo, aquí te espero. Cuando tengas listo el comprobante, me lo envías para seguir con la activación de tu Plan Básico.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí, Juan Camilo! No hay problema. Ahí abajo te dejo de nuevo los datos para pagar por Nequi. Cuando hagas el pago, me envías el comprobante por aquí para que el equipo active tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Disculpa, ¿qué parte no te quedó clara? Te explico de nuevo: para pagar por Nequi, usas los datos que te acabo de enviar (aparecen justo debajo de mi mensaje). Cuando hagas el pago, me envías el comprobante por este chat para que podamos activar tu Plan Básico.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Excelente, Juan Camilo! Aquí estoy pendiente. Cuando hagas el pago, me envías el comprobante por este chat para que el equipo active tu Plan Básico.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, ya pagó el Plan Básico y quiere que se lo activen.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** ¡Hola, Laura! El Plan Básico es una excelente opción. Con él, tu WhatsApp se convierte en un vendedor automático que responde al instante y da seguimiento a tus clientes para que no pierdas ninguna venta. Para arrancar, necesito tu nombre, teléfono y correo.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Con el Plan Básico, la implementación y el primer mes te costarían COP 210.000. Después, solo COP 110.000 mensuales. ¿Me confirmas tu nombre y teléfono para terminar de activar tu servicio?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Ahora, haz el pago con los datos de Nequi que te envié arriba. Cuando lo hagas, me envías por aquí la captura del comprobante y con eso terminamos de activar tu Plan Básico.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente elección! Con el Plan Básico, tu WhatsApp se convertirá en un vendedor automático. Para empezar, ¿me puedes dar tu nombre y número de teléfono?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, con tu nombre y número podemos avanzar. Para el pago, ¿qué medio prefieres usar? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, ¿me podrías dar tu nombre completo para la activación?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Con el Plan Básico vas a poder responder al instante y hacer seguimiento automático a tus clientes. Para empezar, ¿me confirmas tu nombre y número de teléfono?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿Me confirmas tu nombre y número de teléfono para activar tu Plan Básico?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. Para activarlo, solo necesito tu nombre y número de teléfono. ¿Me los compartes?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría consignar? Tenemos Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B y link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Para empezar con el Plan Básico y activar tu asistente, necesito que me confirmes tu nombre y número de teléfono. Después te guío con el pago.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. ¿Cuál prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico te ayudará a que tu WhatsApp sea un vendedor automático. Para empezar, ¿me podrías dar tu nombre y número de teléfono?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para el pago?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a transformar tus conversaciones en ventas. Con este plan, pagas COP 100.000 de implementación y luego COP 110.000 al mes. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente.   
  
Para arrancar, ¿con qué medio de pago te gustaría hacer el primer pago de COP 210.000 (implementación + primer mes)?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro que sí, con gusto te paso con alguien de nuestro equipo para que te ayude con lo que necesites. Te contactarán por este mismo chat en breve.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Preguntó por una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Con el Plan Básico vas a poder automatizar tus respuestas y asegurar un seguimiento constante para no perder más ventas. Para empezar, necesito tu nombre y número de teléfono. Luego, te envío los datos para el pago del primer mes.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia por el cobro duplicado y la falta de respuesta. Voy a pasar tu caso directamente al equipo para que lo revisen y se pongan en contacto contigo lo antes posible.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Dijo que le cobraron dos veces y que nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a automatizar tus ventas. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. El primer mes cuesta COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales. ¿Te gustaría que te envíe los datos para el pago?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para activar tu Plan Básico, necesito tu nombre y número de teléfono, por favor.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Excelente! El Plan Básico es una gran opción para que tu WhatsApp se convierta en un vendedor automático. Para activarlo, necesito tu nombre y número de teléfono. Luego te envío los datos para el pago del primer mes, que incluye la configuración y la mensualidad.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, claro que puedes transferir. Tenemos Nequi, Daviplata y transferencia a Bancolombia. ¿Cuál prefieres para enviarte los datos?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, claro que puedes pagar con Nequi. ¿Te envío los datos de Nequi para que puedas hacer el pago y arranquemos?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Perfecto, Juan Camilo! Ya con tus datos, te envío la información de Nequi para que puedas hacer el pago del Plan Básico y empecemos a configurar tu asistente para tu tienda de ropa. Te llegará en un momento.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, me confirmas para que activemos el servicio y empecemos con la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Excelente, Juan Camilo! Ya tengo tu número. Ahora, para avanzar, haz el pago por Nequi con los datos que te envié y me envías el comprobante. Con eso, activamos tu Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, me envías el comprobante aquí por el chat. Con eso, nuestro equipo verifica tu pago y activamos tu Plan Básico para que empecemos la configuración de tu asistente.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí te espero. Cuando estés listo, me avisas.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí! Aquí te los dejo de nuevo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Disculpa, parece que hubo un error. Te vuelvo a enviar los datos para pagar por Nequi.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Perfecto! Cuando hayas hecho el pago, envíame el comprobante por aquí para que nuestro equipo lo verifique y activemos tu Plan Básico.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, ya consignó el Plan Básico y quiere que le verifiquen el pago.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** ¡Hola, Laura! Excelente que te interese el Plan Básico. Con este plan, tu tienda de ropa tendrá un asistente que responderá al instante y ayudará a que no se te escape ninguna venta. Para arrancar, necesito tu nombre completo y número de teléfono. Luego, te comparto las opciones de pago.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Claro que sí, Laura! Te dejo los datos para pagar por Nequi justo aquí abajo. Una vez que hagas el pago, por favor envíame tu nombre y número de teléfono para activar el servicio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Ahora que ya tienes los datos, haces el pago por Nequi y me envías aquí la captura del comprobante. Con eso, activamos tu Plan Básico y empezamos la configuración.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente elección! Con el Plan Básico, tu WhatsApp se convertirá en un vendedor automático. Para empezar, necesito tu nombre y número de teléfono. Después de eso, te guiaré con el pago.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, con tu número 3157778899 ya podemos avanzar. ¿Con qué medio de pago te gustaría continuar? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, me confirmas para que activemos tu servicio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Con el Plan Básico, tu WhatsApp se convierte en un vendedor automático. Para empezar, ¿con qué medio de pago te gustaría hacer la implementación y el primer mes?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, ¿me podrías confirmar tu nombre y número de teléfono para activar tu Plan Básico?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente elección! Con el Plan Básico, tu WhatsApp se convierte en un vendedor automático. Para activarlo, ¿me podrías dar tu nombre, teléfono y un correo electrónico?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago prefieres consignar? Tenemos Nequi, Daviplata, transferencia a Bancolombia o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es una gran opción para empezar a transformar tus conversaciones en ventas. Con este plan, pagas COP 100.000 por la implementación inicial y luego COP 110.000 al mes. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. ¿Te gustaría que te envíe los datos para el pago y así activar tu servicio?

**[2] Cliente:** cómo te pago

**[2] Asesor:** ¿Con qué medio de pago te gustaría hacerlo? Puedes usar Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico te ayudará a que tu WhatsApp sea un vendedor automático. Para empezar, ¿me podrías dar tu nombre y número de teléfono?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi sin problema. ¿Te gustaría que te envíe los datos para que puedas hacer el pago del Plan Básico?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Con el Plan Básico vas a poder automatizar tus respuestas y darle seguimiento a tus clientes para que no se te escape ninguna venta. Para empezar, ¿con qué medio de pago te gustaría hacer la implementación y el primer mes?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro que sí, con gusto te paso con alguien de nuestro equipo por este mismo chat para que te ayude con el Plan Básico. Ya te contactan.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! Para empezar con tu Plan Básico y activar tu asistente comercial, necesito tu nombre y número de teléfono. Con esos datos, te ayudo a dar el siguiente paso.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Dijo que le cobraron dos veces y que nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente! El Plan Básico es perfecto para empezar a automatizar tus ventas. Incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. El primer mes son COP 210.000 (implementación + primer mes) y luego COP 110.000 mensuales.   
  
Para avanzar, ¿con qué medio de pago te gustaría pagar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para activar tu servicio, necesito tu nombre y un número de teléfono.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos.   
  
¿Te gustaría añadir alguna bebida para acompañar tu pedido?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, claro que puedes transferir. Aceptamos Nequi, Daviplata y transferencia a Bancolombia (ahorros).   
  
¿Te gustaría que te envíe los datos de alguno de estos medios para que puedas pagar?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Quieres que te envíe los datos para que hagas la transferencia?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** ¡Perfecto, Juan Camilo! Ya tenemos tu nombre.   
  
Para confirmar tu pedido de la Hamburguesa Sencilla, ¿me podrías dar tu número de teléfono y dirección de entrega?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para que tu Hamburguesa Sencilla llegue rapidísimo, ¿me confirmas tu número de teléfono y dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu número: 3157778899.  
  
Solo falta la dirección de entrega para que tu Hamburguesa Sencilla esté en camino. ¿Me la podrías dar?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Después de hacer el pago por Nequi, por favor envíame una captura del comprobante por aquí. Así podemos confirmar tu pedido y enviarlo a la cocina para que tu hamburguesa llegue rapidito.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** ¡Claro que sí, Juan Camilo! Tómate tu tiempo. Aquí te espero.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí, Juan Camilo! No te preocupes, aquí te dejo de nuevo los datos para pagar por Nequi.  
  
Recuerda enviarme el comprobante cuando hayas hecho el pago.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Disculpa, creo que mi mensaje anterior no se envió bien. Te explico: te envié los datos de Nequi para que puedas hacer el pago de tu hamburguesa. Una vez lo hagas, me mandas una foto del comprobante por aquí, ¿listo?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Excelente, Juan Camilo! Quedo atento a la confirmación de tu pago. Cuando lo hagas, por favor envíame el comprobante por aquí para que podamos alistar tu Hamburguesa Sencilla.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en la Hamburguesa Sencilla y quiere pagar por Nequi. Pidió que le enviaran de nuevo los datos de Nequi y luego dijo que ya consignó.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Hola, Laura! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres una?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para ir preparando tu pedido, ¿me confirmas tu nombre completo, dirección y teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Ahora solo falta que hagas el pago a los datos que te envié y me compartas el comprobante por aquí. Así podemos confirmar tu pedido y prepararlo para que te llegue caliente.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¡Perfecto! Para pagar, puedes usar Nequi, Daviplata o hacer una transferencia a Bancolombia (ahorros). ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para completar tu pedido, ¿a qué dirección te lo llevamos?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla. ¿Quieres agregarle una bebida para acompañar tu pedido?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para confirmar tu pedido, ¿me podrías dar tu nombre, teléfono y dirección?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro que sí! Una Hamburguesa Sencilla. ¿Quieres agregarle alguna bebida para acompañar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría consignar? Tenemos Nequi, Daviplata y transferencia a Bancolombia.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro que sí! Una Hamburguesa Sencilla. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** ¿Cómo prefieres pagar? Puedes hacerlo con Nequi, Daviplata, transferencia a Bancolombia o Bre-B.

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Te gustaría añadir una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Recibimos pagos con Nequi. ¿Te gustaría que te envíe los datos de pago?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla. ¿Quieres agregarle algo para acompañar, como una gaseosa o un jugo natural?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Entiendo. Te paso con alguien de nuestro equipo para que te ayude con tu pedido.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla, ¿algo más para acompañar? Tenemos gaseosa por COP 5.000 o jugo natural por COP 7.000.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que te hayan cobrado dos veces. Voy a pasar tu caso al equipo para que lo revisen de inmediato y te den una solución. Ellos se pondrán en contacto contigo por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. El cliente dice que le cobraron dos veces y está molesto.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para confirmar tu pedido, ¿me puedes dar tu nombre, dirección y número de teléfono?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle algo para acompañar, como una gaseosa o un jugo natural?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, claro que puedes transferir. Aceptamos Nequi, Daviplata y transferencia a Bancolombia (cuenta de ahorros).  
  
¿Te gustaría que te envíe los datos para el pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** ¡Sí, claro! También puedes pagar con Nequi. ¿Prefieres que te envíe los datos de Nequi o de alguna otra opción?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Ya tenemos tu Hamburguesa Sencilla. ¿Confirmamos el pedido y te envío los datos para pagar con Nequi?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Para que tu Hamburguesa Sencilla llegue rapidísimo, ¿me confirmas tu dirección y un número de teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Ya tengo tu número. ¿A qué dirección te llevamos tu Hamburguesa Sencilla?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Después de hacer el pago por Nequi, envíame por aquí la captura del comprobante. Con eso confirmamos tu pedido y lo enviamos a la cocina.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, Juan Camilo, aquí te espero. Avísame cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí, Juan Camilo! No te preocupes, aquí te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Claro, te explico: arriba, en este chat, te dejé los datos para pagar con Nequi. Haces el pago usando esos datos y luego me envías aquí una captura del comprobante. Así podemos confirmar tu pedido y prepararlo.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Perfecto, Juan Camilo! Cuando hagas el pago, envíame el comprobante por aquí para confirmar tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo se interesó en la Hamburguesa Sencilla y quería pagar por Nequi. Pidió los datos de Nequi de nuevo y luego dijo que ya consignó.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Hola, Laura! La Hamburguesa Sencilla es una excelente elección. Lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregar alguna bebida para acompañar?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo, Laura! Ahí abajo te dejo los datos para pagar por Nequi. Para confirmar tu pedido, ¿me podrías dar tu nombre completo, dirección y un número de teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** ¡Perfecto, Laura! Ya te envié los datos de Nequi. Ahora solo tienes que hacer el pago y enviarme la captura del comprobante por aquí. Con eso confirmamos tu pedido y lo enviamos a la cocina.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro que sí! Una Hamburguesa Sencilla. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar tu pedido?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¡Perfecto! Para pagar, puedes usar Nequi, Daviplata, hacer una transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿A qué dirección te la llevamos?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla, ¿algo más para acompañar? Tenemos Gaseosa por COP 5.000 o Jugo Natural por COP 7.000.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿A qué dirección te la llevamos y cuál es tu número de teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro que sí! Una Hamburguesa Sencilla. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría consignar? Tenemos Nequi, Daviplata y transferencia a Bancolombia.

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Te gustaría añadir alguna bebida para acompañar tu pedido?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata o transferencia a Bancolombia. ¿Cuál prefieres para enviarte los datos?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro que sí! Una Hamburguesa Sencilla. ¿Quieres agregarle una bebida para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para el pago?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla, ¿algo más para acompañar tu pedido?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** ¡Entendido! Te paso con alguien de nuestro equipo para que te ayude con lo que necesites.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla y pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000.  
  
¿Te gustaría añadirle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia por el cobro duplicado. Voy a pasar tu caso al equipo para que lo revisen y se pongan en contacto contigo lo antes posible.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Dice que le cobraron dos veces y está molesto porque nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro que sí! Una Hamburguesa Sencilla. ¿Quieres agregarle alguna bebida para acompañar?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para confirmar tu pedido, ¿me podrías dar tu nombre, teléfono y dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregar una bebida para acompañar tu pedido?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes transferir. Aceptamos Nequi, Daviplata y transferencia a Bancolombia (ahorros). ¿Cuál prefieres usar?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, claro que puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para que puedas hacer la transferencia?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** ¡Perfecto, Juan Camilo! Entonces, para confirmar tu pedido: una Hamburguesa Sencilla. ¿Es correcto?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Para que tu hamburguesa llegue rapidísimo, ¿me confirmas tu dirección y número de teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu número: 3157778899. ¿A qué dirección te llevamos tu Hamburguesa Sencilla?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** ¡Claro! Una vez que hagas el pago por Nequi, solo tienes que enviarme una captura del comprobante por este mismo chat. Con eso, confirmamos tu pedido y lo mandamos a la cocina.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** ¡Claro! Tómate tu tiempo. Aquí te espero para cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí! No te preocupes, aquí te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Perfecto! Aquí estoy pendiente. Cuando termines, me envías el comprobante por este chat.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo está interesado en la Hamburguesa Sencilla y quiere pagar por Nequi. El cliente dice que ya consignó.

### restaurant · se presenta al empezar

**[1] Cliente:** Hola, soy Laura. Me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Hola, Laura! La Hamburguesa Sencilla es una excelente elección. Lleva carne artesanal, queso y vegetales frescos. ¿Cuántas te gustaría pedir?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para ir preparando tu pedido de la Hamburguesa Sencilla, ¿me confirmas tu nombre completo, dirección y teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** ¡Claro! Ya te envié los datos de Nequi. Ahora solo tienes que hacer el pago y enviarnos una captura del comprobante por aquí. Así confirmamos tu pedido y lo mandamos a la cocina.

### restaurant · da su teléfono antes de pagar

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Quieres agregarle una bebida para acompañar tu pedido?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¡Perfecto! Para pagar, puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. ¿A qué dirección te llevamos tu Hamburguesa Sencilla?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle alguna bebida para acompañar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para ir preparando tu pedido, ¿me confirmas tu nombre, teléfono y dirección de entrega?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos. ¿Te gustaría añadir una bebida para acompañar tu pedido?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría consignar? Tenemos Nequi, Daviplata y transferencia a Bancolombia (ahorros).

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Te gustaría añadirle una bebida para acompañar?

**[2] Cliente:** cómo te pago

**[2] Asesor:** ¿Con qué medio de pago te gustaría cancelar? Aceptamos Nequi, Daviplata, transferencia a Bancolombia (ahorros) y Bre-B.

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! Una Hamburguesa Sencilla, ¿algo más para acompañar? Tenemos gaseosa por COP 5.000 o jugo natural por COP 7.000.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para que puedas hacer el pago?

### restaurant · pide hablar con una persona

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Entendido, te paso con alguien de nuestro equipo para que te ayude con tu pedido.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Pidió hablar con una persona del equipo.

### restaurant · reclama

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Excelente elección! La Hamburguesa Sencilla lleva carne artesanal, queso y vegetales frescos por COP 18.000. ¿Quieres agregarle una gaseosa o un jugo natural para acompañar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que te hayan cobrado dos veces y que no hayas recibido respuesta. Voy a pasar tu caso con el equipo para que lo revisen y se pongan en contacto contigo lo antes posible.

*[2] Nota para el equipo:* El cliente quiere una Hamburguesa Sencilla. Dice que le cobraron dos veces y está molesto porque nadie le responde.

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Claro! Una Hamburguesa Sencilla, ¿algo más para acompañar tu pedido?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para confirmar tu pedido, ¿me podrías dar tu nombre, teléfono y dirección?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Excelente! Con Agenda Plus te ayudaremos a gestionar y confirmar tus citas para que no pierdas pacientes por demoras.  
  
Para empezar, ¿me podrías dar tu nombre y número de teléfono? Así coordinamos el día y la hora para la implementación.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes transferir a nuestra cuenta de Bancolombia (ahorros). ¿Te gustaría que te envíe los datos para la transferencia?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** ¡Claro que sí! También puedes pagar con Nequi.   
  
¿Prefieres Nequi o transferencia a Bancolombia para enviarte los datos de pago?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Hola Juan Camilo! Te cuento que Agenda Clinica Pro está diseñado para clínicas y consultorios. Nuestro servicio se enfoca en agendar citas médicas y de salud, no para tiendas de ropa.  
  
¿Te gustaría que te ayude a buscar una solución más adecuada para tu negocio?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Para poder agendar la implementación de Agenda Plus, ¿me podrías confirmar tu número de teléfono y el nombre de tu clínica o consultorio?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu número de teléfono.   
  
Para continuar con la implementación de Agenda Plus, ¿me podrías enviar el comprobante de pago por Nequi? Con eso ya podemos coordinar el día y la hora para empezar.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, solo envíame la captura del comprobante por aquí. Con eso, nuestro equipo de Agenda Clínica Pro te contactará para coordinar el día y la hora de la implementación. ¿Te parece bien?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** ¡Claro, tómate tu tiempo! Aquí estoy para cuando me necesites.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí! No te preocupes, aquí te dejo de nuevo los datos para pagar por Nequi.  
  
Cuando tengas el comprobante, me lo envías por aquí para que coordinemos la implementación de Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** ¡Disculpa si no fui claro! Quise decir que ya te envié los datos para pagar por Nequi en el mensaje anterior. Solo tienes que usarlos para hacer el pago y luego enviarme la captura del comprobante por este chat. ¿Hay algo más en lo que te pueda ayudar?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Perfecto! Aquí estoy pendiente para cuando me envíes el comprobante. Una vez lo tenga, nuestro equipo se pondrá en contacto contigo para coordinar la implementación de Agenda Plus.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, ya pagó por Nequi el plan Agenda Plus y quiere que le confirmen el pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** ¡Hola, Laura! Agenda Plus es un servicio para clínicas y consultorios que te ayuda a agendar citas rápido y sin perder pacientes. Te permite gestionar y confirmar citas, y hacer seguimiento a tus pacientes. ¿Te gustaría saber más sobre cómo funciona o resolver alguna duda?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para agendar la implementación de Agenda Plus, ¿me podrías dar tu nombre y un número de teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus te ayudará a gestionar y confirmar tus citas sin perder pacientes por demoras.  
  
Para agendar, necesito que me des tu nombre, teléfono, y si tienes algún día u hora preferida para coordinar la implementación. Nuestro equipo confirmará la agenda.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, con tu número 3157778899 podemos avanzar. ¿Qué medio de pago prefieres usar? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, por favor, envíanos los detalles para que nuestro equipo pueda confirmar tu agenda y coordinar el día y la hora de la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. Con este servicio gestionamos y confirmamos tus citas para que no pierdas pacientes por demoras.   
  
¿Te gustaría que agendemos una cita para empezar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para seguir con tu Agenda Plus, ¿me podrías dar tu nombre y teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus es ideal para gestionar y confirmar tus citas sin perder pacientes. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. ¿Te gustaría agendar una cita para empezar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría consignar? Tenemos Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Con Agenda Plus vas a poder gestionar y confirmar tus citas de forma más rápida. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes.  
  
Para empezar, ¿te gustaría que coordinemos el día y la hora para la implementación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (cuenta de ahorros), Bre-B o con un link de pago. ¿Cuál prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus es ideal para gestionar y confirmar tus citas sin perder pacientes por demoras. Para empezar, ¿podrías darme tu nombre y número de teléfono?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro, puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para la implementación de Agenda Plus?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus es la solución perfecta para agendar tus citas rápidamente y sin perder pacientes. Para empezar, ¿podrías darme tu nombre y número de teléfono?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro que sí. Con gusto te pongo en contacto con alguien de nuestro equipo para que te ayude. Por favor, espera un momento.

*[2] Nota para el equipo:* El cliente quiere el producto Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. Con este servicio, gestionamos y confirmamos las citas para tu clínica.  
  
Para agendar, necesito tu nombre, teléfono, y si tienes algún día u hora preferida.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia por el cobro duplicado y la falta de respuesta. Voy a pasar tu caso directamente al equipo para que lo revisen y te contacten lo antes posible por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Dice que le cobraron dos veces y que nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus te ayudará a gestionar y confirmar tus citas de forma más eficiente. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes.  
  
Para empezar, ¿te gustaría que coordinemos el día y la hora de tu cita de implementación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia.  
  
Para que el equipo pueda coordinar la implementación de Agenda Plus, ¿me podrías dar tu nombre y un número de teléfono?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Excelente! Agenda Plus te ayudará a gestionar y confirmar tus citas sin perder pacientes. Para empezar, necesito que me confirmes tu nombre, teléfono, y si tienes algún día u hora preferida para coordinar la implementación. Nuestro equipo se encargará de confirmarte la agenda.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar Agenda Plus por transferencia a Bancolombia (cuenta de ahorros). ¿Te gustaría que te envíe los datos para que puedas hacer la transferencia?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Prefieres que te envíe los datos de Nequi o los de Bancolombia?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, Juan Camilo. Aunque Agenda Clinica Pro está diseñado para clínicas y consultorios, puedo pasarte con nuestro equipo para que revisen tu caso y vean si Agenda Plus se adapta a las necesidades de tu tienda de ropa. ¿Te parece bien?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, por favor, envíanos tu nombre completo y un número de teléfono para coordinar la implementación de Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tenemos tu número de teléfono. Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Una vez que hagas el pago, por favor, envíanos la captura del comprobante aquí para que el equipo pueda verificarlo y coordinar la implementación de Agenda Plus.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, por favor, envíanos la captura del comprobante aquí en el chat. Así nuestro equipo podrá verificarlo y nos pondremos en contacto contigo para coordinar la implementación de Agenda Plus.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí te espero. ¡Avísame cuando estés listo!

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí! Aquí te dejo de nuevo los datos para pagar por Nequi. Cuando hagas el pago, por favor, envíanos la captura del comprobante aquí en el chat para que el equipo pueda verificarlo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Disculpa la confusión. Para pagar por Nequi, necesitas usar la aplicación de Nequi en tu celular. Los datos que te envié antes son el número de Nequi al que debes enviar el dinero.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Perfecto! Aquí estoy pendiente. Cuando termines, me envías el comprobante por favor.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, ya pagó por Agenda Plus y consignó el dinero. El cliente quiere que se verifique su pago.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** ¡Hola, Laura! Con Agenda Plus ayudamos a clínicas y consultorios a agendar citas rápido y sin perder pacientes. Veo que tienes una tienda de ropa, ¿te interesaría algo relacionado con la gestión de citas o tienes alguna necesidad específica en mente?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para agendar la implementación de Agenda Plus, ¿me podrías dar tu nombre y teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** ¡Claro! Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Una vez que hagas el pago, me envías la captura del comprobante por aquí para que nuestro equipo lo verifique y podamos coordinar la implementación de Agenda Plus.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus te ayuda a gestionar y confirmar tus citas para que no pierdas pacientes por demoras.  
  
Para empezar, ¿podrías darme tu nombre y teléfono? Así coordinamos el día y la hora para tu implementación.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¡Perfecto! Para el pago de Agenda Plus, puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (cuenta de ahorros), Bre-B o un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez hecho el pago, ¿qué día y hora te gustaría agendar la implementación?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Con Agenda Plus podremos gestionar y confirmar las citas de tu clínica para que no pierdas pacientes por demoras. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. ¿Te gustaría agendar una cita para empezar con la implementación?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para agendar la cita de implementación, ¿me podrías dar tu nombre y un número de teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente elección! Con Agenda Plus, tu clínica podrá gestionar y confirmar citas de manera eficiente para no perder pacientes. Tiene un costo de implementación de COP 140.000 y una mensualidad de COP 170.000.   
  
¿Te gustaría que agendemos una cita para la implementación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Para pagarlo, puedes usar Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál prefieres?

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus te ayudará a gestionar y confirmar tus citas sin perder pacientes. Para empezar, ¿me podrías dar tu nombre y teléfono?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál prefieres?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus te ayuda a gestionar y confirmar tus citas para que no pierdas pacientes por demoras. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes.  
  
Para agendar tu cita de implementación, ¿me podrías dar tu nombre y número de teléfono?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi para la implementación de Agenda Plus.

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus tiene un costo de COP 140.000 para la implementación y COP 170.000 al mes. Con este servicio gestionamos y confirmamos las citas de tu clínica.  
  
Para agendar, necesito tu nombre, teléfono y el día y la hora que te gustaría. Luego, el equipo te confirmará la agenda.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro que sí, con gusto te paso con alguien del equipo para que te ayude. Ellos te contactarán por este mismo chat para resolver tus dudas y coordinar lo que necesites.

*[2] Nota para el equipo:* El cliente quiere el producto Agenda Plus. Pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus es ideal para gestionar y confirmar tus citas sin perder pacientes. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. ¿Te gustaría que coordinemos el día y la hora para empezar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho escuchar lo que pasó con el cobro. Voy a pasar tu caso con el equipo para que revisen lo sucedido y te den una pronta solución.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Dijo que le cobraron dos veces y que nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Con Agenda Plus podremos ayudarte a gestionar y confirmar tus citas sin perder pacientes por demoras. Para empezar, ¿podrías darme tu nombre, teléfono y algunos detalles sobre tu clínica?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. ¿Podrías confirmarme tu nombre y número de teléfono para que el equipo pueda coordinar la implementación y el agendamiento?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** ¡Excelente! Agenda Plus es ideal para ayudarte a gestionar y confirmar tus citas. Para empezar, necesito que me compartas tu nombre y número de teléfono. Así, nuestro equipo puede coordinar el día y la hora para la implementación.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, claro que puedes transferir. Aceptamos transferencias a Bancolombia (ahorros), Nequi y Daviplata. ¿Cuál de estas opciones prefieres?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, claro que puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para la transferencia?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Entiendo que tu negocio es una tienda de ropa. Te comento que Agenda Clínica Pro está diseñado específicamente para clínicas y consultorios de salud, ayudándolos a gestionar sus citas de manera eficiente.

*[5] Nota para el equipo:* Juan Camilo, de una tienda de ropa, está interesado en Agenda Plus y preguntó si podía pagar con Nequi. El cliente quiere empezar.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Una vez que hagas el pago, por favor, envíanos el comprobante para que podamos coordinar la implementación de Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** ¡Perfecto, Juan Camilo! Ya tengo tu número de teléfono: 3157778899. Por favor, realiza el pago por Nequi con los datos que te envié y envíame el comprobante por aquí. Con eso ya coordinamos la implementación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, solo necesitas enviarme el comprobante por este chat. Con eso, nuestro equipo se encarga de coordinar contigo el día y la hora para empezar con la implementación de Agenda Plus.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí estoy. Avísame cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí! No te preocupes, aquí te dejo de nuevo los datos para pagar por Nequi. Cuando hagas el pago, me envías el comprobante por aquí para coordinar la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago a ese Nequi y me envías aquí la captura del comprobante. Con eso, ya coordinamos el día y la hora para empezar con Agenda Plus.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** ¡Excelente! Estaré atento a que me envíes el comprobante por aquí para que podamos seguir con la coordinación de tu Agenda Plus.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, de una tienda de ropa, ya consignó el pago de Agenda Plus y quiere que se verifique.

### clinic · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Agenda Plus

**[1] Asesor:** ¡Hola, Laura! Agenda Plus es un motor comercial para clínicas y consultorios, que te ayuda a agendar citas rápidamente y sin perder pacientes. Veo que tienes una tienda de ropa, ¿te interesaría algo para gestionar tus ventas o clientes?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para que el equipo te ayude a coordinar el día y la hora de implementación, ¿me podrías regalar tu nombre y número de teléfono?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Ahora que tienes los datos de Nequi, el siguiente paso es que hagas el pago y nos envíes por aquí la captura del comprobante. Así el equipo puede verificarlo y coordinar contigo la implementación de Agenda Plus.

### clinic · da su teléfono antes de pagar

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Claro! Agenda Plus tiene un costo de implementación de COP 140.000 y una mensualidad de COP 170.000. Con este servicio, te ayudamos con la gestión y confirmación de citas para que no pierdas pacientes por demoras.  
  
¿Te gustaría que agendemos una cita para empezar?

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** ¡Perfecto! Para el pago de Agenda Plus, puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia (cuenta de ahorros), Bre-B o un link de pago. ¿Cuál prefieres?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para agendar tu cita de implementación, ¿cuál es tu nombre y en qué día y hora te gustaría que coordinemos?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus es la solución para gestionar y confirmar tus citas sin perder pacientes. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. ¿Te gustaría agendar una cita para coordinar el día y la hora de inicio?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para seguir con la implementación de Agenda Plus, ¿me podrías dar tu nombre y número de teléfono, por favor?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus te ayudará a gestionar y confirmar tus citas de forma más eficiente. Tiene un costo de implementación de COP 140.000 y una mensualidad de COP 170.000. ¿Te gustaría que coordinemos el día y la hora para empezar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con qué medio de pago te gustaría consignar? Tenemos Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B y link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Gracias por escribirnos. En este momento no puedo responderte; por favor escríbenos de nuevo en unos minutos.

**[2] Cliente:** cómo te pago

**[2] Asesor:** ¿Qué medio de pago prefieres? Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. También te ofrecemos financiación con Addi o Sistecredito.

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Con Agenda Plus podemos ayudarte a gestionar y confirmar tus citas para que no pierdas pacientes. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 mensuales.  
  
Para empezar, ¿te gustaría que coordinemos el día y la hora para la implementación?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que sí. Puedes pagar con Nequi. ¿Te gustaría que te envíe los datos para que puedas hacer el pago de la implementación?

### clinic · pide hablar con una persona

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Con Agenda Plus podemos ayudarte a agendar más citas y tener tu disponibilidad en orden. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con alguien de nuestro equipo para que te ayude con el proceso. Por este mismo chat te atenderán.

*[2] Nota para el equipo:* El cliente quiere el producto Agenda Plus y pidió hablar con una persona del equipo.

### clinic · reclama

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Claro! Con Agenda Plus, tu clínica tendrá gestión y confirmación de citas para que no pierdas pacientes por demoras. Tiene un costo de implementación de COP 140.000 y luego COP 170.000 al mes. ¿Te gustaría agendar una cita para empezar?

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Lamento mucho que estés pasando por esta situación. Voy a pasar tu caso al equipo para que revisen lo ocurrido con el cobro y se pongan en contacto contigo lo antes posible para resolverlo.

*[2] Nota para el equipo:* El cliente quiere Agenda Plus. Dijo que le cobraron dos veces y que nadie le responde.

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Excelente! Agenda Plus tiene un costo de COP 140.000 para la implementación y COP 170.000 al mes. Con este servicio, gestionamos y confirmamos las citas de tu clínica.  
  
Para agendar, necesito algunos datos. ¿Me podrías dar tu nombre y tu número de teléfono?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para poder coordinar el día y la hora de tu implementación, ¿me podrías confirmar tu nombre y número de teléfono?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
