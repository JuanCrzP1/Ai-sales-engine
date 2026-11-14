# Estándar del asesor: estandar_20261113_paso_a_persona_ia

**NO PASA** · código `9e88699 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 18 conversaciones (3 muestras por negocio: asesor_ai_prod)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 18 de 18 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 18 de 18 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 18 de 18 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 18 de 18 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 18 de 18 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pago avisado al equipo (exacta) | 18 de 18 | Si dice que ya pagó, el chat pasa al equipo; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 18 de 18 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 18 de 18 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ responde lo que preguntan (juez) | 18 de 18 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 17 de 18 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 18 de 18 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 18 de 18 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 18 de 18 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |

Gasto de la corrida: asesor USD 0.0427 · juez USD 0.0075. Llamadas al modelo por mensaje: 2.01. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 7.

## Lo que no pasó

- **no pide lo ya dado** · asesor_ai_prod · el chat de producción · turno 10: El cliente ya había dado su número de teléfono.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu número de teléfono para completar la activación del servicio. ⏎  ⏎ Datos Nequi: ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Genial, el Plan Básico cuesta COP 210.000 en el primer mes (incluye implementación y el primer mes de servicio). Luego sigue con COP 110.000 mensuales. ¿Con cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Para continuar, necesito tu nombre, teléfono y detalles para la implementación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría proceder con ese medio de pago? Para continuar, necesito tu nombre, teléfono y detalles para la implementación.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** ¡Listo, Juan Camilo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, confirma tu número de teléfono para completar el registro.  
  
Datos de Nequi:  
- Nombre: Asesor Comercial  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Perfecto, entonces puedes hacer el pago por Nequi. Por favor, envíame la captura del comprobante una vez lo realices, y seguimos con la implementación.

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Entonces, espero tu comprobante de pago por Nequi y con eso avanzamos con la implementación. Si tienes alguna duda, aquí estoy.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez hagas el pago y me envíes la captura del comprobante, procederemos a configurar el sistema para tu tienda de ropa. Te guiaré en cada paso para que todo quede listo.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Aquí estaré cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Haz el pago y me envías aquí la captura del comprobante. Así seguimos con la implementación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante. Con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la configuración. ¡Avísame cuando estés listo!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye la configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes. Después, pagas COP 110.000 mensualmente. Solo necesito tu nombre, teléfono y detalles para proceder.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Nombre: Asesor Comercial  
  
Por favor, compárteme tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y primer mes) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes es de COP 210.000 (COP 100.000 de implementación + COP 110.000 al mes) y luego solo COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o un link de pago. ¿Cuál medio prefieres utilizar?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para continuar, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para que puedas realizar el pago?

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (que incluye la implementación y el primer pago mensual), y luego COP 110.000 cada mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, realiza la transferencia y confirma cuando lo hayas hecho.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico cuesta COP 210.000 el primer mes (100.000 de implementación + 110.000 mensual). Luego, sigues con COP 110.000 cada mes. ¿Con cuál medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, para la transferencia a Bancolombia, necesitaré tus datos: nombre y teléfono para avanzar con la activación del servicio.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Quieres que te envíe los datos para pagar con Nequi?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Te enviaré los datos para pagar con Nequi y activar tu Plan Básico. ¿Cuál es tu número de teléfono?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu número de teléfono para completar la activación del servicio.  
  
Datos Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Asegúrate de hacer el pago por Nequi y luego envíame la captura del comprobante aquí. Así avanzamos con la activación de tu servicio.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, solo envíame aquí la captura del comprobante. Con eso, procederemos a activar tu servicio y te guiaré en la configuración inicial.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu número de teléfono para completar la activación del servicio.  
  
Datos Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando tengas el comprobante, solo envíamelo aquí y avanzamos con la activación del servicio.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes (COP 100.000 de implementación + COP 110.000 mensual). ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
¿Me puedes dar tu nombre y teléfono para continuar?  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente elección! El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000 (incluye implementación y primer mes) y luego solo COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Cuál de los medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye la configuración inicial, la guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta COP 210.000, que incluye la implementación y el primer pago mensual. Luego, se paga COP 110.000 al mes. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o mediante un link de pago. ¿Cuál de estos métodos prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes, que incluye la implementación y el primer mes de servicio. Luego, cada mes pagarás COP 110.000. Para proceder, necesito tu nombre, teléfono y detalles. ¿Te gustaría que te envíe los datos de pago?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para que puedas realizar el pago?

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico tiene un costo de COP 100.000 por la implementación y COP 110.000 al mes. Incluye la configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para la transferencia a Bancolombia. Por favor, realiza la transferencia y envíame el comprobante para activar tu servicio.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Genial! El Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 el primer mes, y luego COP 110.000 mensuales. Para avanzar, necesito tu nombre, teléfono y detalles para la configuración. ¿Me puedes compartir eso?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, puedes hacer la transferencia a Bancolombia. Para continuar, por favor, comparte tu nombre, teléfono y detalles para la configuración.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. Si prefieres pagar con ese medio, puedo enviarte los datos. ¿Te gustaría que te los enviara?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Necesito tu número de teléfono y cualquier detalle adicional que quieras incluir para la configuración. Así podemos activar tu Plan Básico y empezar a mejorar tu atención al cliente.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, comparte tu número de teléfono para completar la configuración:  
  
Espero tu número para avanzar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Con tu pago por Nequi y tu número [dato entregado por el motor], podemos proceder con la activación del Plan Básico. Cuando me envíes la captura del comprobante de pago, comenzaremos con la configuración. ¡Espero tu mensaje!

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez me envíes la captura del comprobante, iniciaré la configuración de tu sistema. Te guiaré paso a paso para que todo esté listo. ¡Espero tu comprobante para comenzar!

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Aquí te dejo de nuevo los datos para pagar por Nequi:  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅  
  
Cuando hagas el pago, envíame la captura del comprobante y seguimos con la activación.

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu comprobante para continuar con la activación de tu Plan Básico. ¡Estoy aquí para ayudarte!

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un sistema mensual por COP 210.000 el primer mes y luego COP 110.000 mensuales. Para avanzar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Nombre: Asesor Comercial  
  
Después, por favor, compárteme tu nombre y teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para proceder, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Cuál de los medios de pago prefieres usar? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 210.000 en el primer mes (COP 100.000 de implementación + COP 110.000 al mes). Luego, se paga mensualmente COP 110.000. ¿Cuál es tu nombre y número de teléfono para avanzar con la activación?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos métodos prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para avanzar, necesito tu nombre, teléfono y cómo prefieres pagar.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos de pago para continuar?

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). ¿Me confirmas tu nombre y teléfono para completar la activación?  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
