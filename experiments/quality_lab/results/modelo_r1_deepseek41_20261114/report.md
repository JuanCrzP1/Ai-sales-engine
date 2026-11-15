# Estándar del asesor: modelo_r1_deepseek41_20261114

**NO PASA** · código `48d37ce` · modelo `deepseek/deepseek-v4.1-flash` · juez `google/gemini-2.5-flash` · 10 conversaciones (1 muestras por negocio: asesor_ai_prod)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 10 de 10 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ❌ datos cuando los necesita (exacta) | 8 de 10 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 10 de 10 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 10 de 10 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 10 de 10 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 10 de 10 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 7 de 10 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 10 de 10 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ❌ nota para el equipo (exacta) | 7 de 10 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 10 de 10 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 9 de 10 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 10 de 10 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ❌ no dice nada falso del pago (juez) | 9 de 10 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 10 de 10 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 10 de 10 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 10 de 10 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 10 de 10 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0213 · juez USD 0.0025. Llamadas al modelo por mensaje: 2.15. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 1.

Por cada mensaje del cliente: responde en 4.2 s (el 5 % más lento, 9.4 s o más) · USD 0.67 por cada 1.000 mensajes · fuera de formato: 0 de 32 · sin respuesta de la IA: 18 · tokens de razonamiento por mensaje: 405.

## Lo que no pasó

- **datos cuando los necesita** · asesor_ai_prod · se presenta al empezar · turno 2: dijo con qué medio paga y todavía no tiene los datos
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **datos cuando los necesita** · asesor_ai_prod · da su teléfono antes de pagar · turno 3: dijo con qué medio paga y todavía no tiene los datos
  - Cliente: «Listo, por Nequi»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · el chat de producción · turno 3: repitió la respuesta anterior
  - Cliente: «Y puedo trasferir»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · el chat de producción · turno 4: repitió la respuesta anterior
  - Cliente: «Y Nequi no»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · el chat de producción · turno 5: repitió la respuesta anterior
  - Cliente: «Me llamo Juan Camilo y es una tienda de ropa»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · se presenta al empezar · turno 2: repitió la respuesta anterior
  - Cliente: «Listo, lo quiero. Te pago por Nequi»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · da su teléfono antes de pagar · turno 2: repitió la respuesta anterior
  - Cliente: «Mi número es 3157778899, ¿cómo hago para pagarte?»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · da su teléfono antes de pagar · turno 3: repitió la respuesta anterior
  - Cliente: «Listo, por Nequi»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **nota para el equipo** · asesor_ai_prod · el chat de producción · turno 13: el chat pasó al equipo sin una nota de lo que necesita el cliente
  - Cliente: «ya te consigné»
  - Asesor: «Perfecto, ya lo reviso y te confirmo en un momento para continuar.»
- **nota para el equipo** · asesor_ai_prod · pide hablar con una persona · turno 2: el chat pasó al equipo sin una nota de lo que necesita el cliente
  - Cliente: «Quiero hablar con una persona del equipo»
  - Asesor: «Claro, te paso con alguien del equipo por este mismo chat. Ya les dejo tu solicitud del Plan Básico para que retomen la conversación contigo aquí. En un momento te escriben.»
- **nota para el equipo** · asesor_ai_prod · reclama · turno 2: el chat pasó al equipo sin una nota de lo que necesita el cliente
  - Cliente: «Me cobraron dos veces y nadie me responde, estoy muy molesto»
  - Asesor: «Entiendo tu molestia, un cobro doble es algo que hay que revisar ya. Te paso con el equipo por este mismo chat para que verifiquen el cobro y te den respuesta. No es una llamada, sigue aquí.»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 3: El asesor pide el nombre y el nombre de la tienda que el cliente ya dio.
  - Cliente: «¿Y ahora qué sigue?»
  - Asesor: «Perfecto Laura, vamos con el Plan Basico. Aquí abajo te dejo los datos de Nequi para que hagas el pago. Mientras tanto, envíame por este chat tu nombre completo, tu teléfono y el nombre de tu tienda; con eso dejamos lista la configuración inicial y arrancamos con la integración a WhatsApp.»
- **no dice nada falso del pago** · asesor_ai_prod · se presenta al empezar · turno 3: El asesor dice que deja los datos de pago, pero no aparecen.
  - Cliente: «¿Y ahora qué sigue?»
  - Asesor: «Perfecto Laura, vamos con el Plan Basico. Aquí abajo te dejo los datos de Nequi para que hagas el pago. Mientras tanto, envíame por este chat tu nombre completo, tu teléfono y el nombre de tu tienda; con eso dejamos lista la configuración inicial y arrancamos con la integración a WhatsApp.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Listo, Juan Camilo. Haces el pago por Nequi con los datos que te dejé aquí arriba en el chat y, cuando lo tengas, me envías por acá la captura del comprobante. Con eso el equipo verifica el pago y arrancamos de una con la configuración de tu tienda de ropa.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, Juan Camilo, aquí te espero. Cuando tengas el comprobante me lo envías y seguimos con la configuración.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo otra vez los datos para pagar por Nequi. Cuando hagas el pago me envías la captura del comprobante por acá y seguimos con la configuración.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico fácil, Juan Camilo: aquí abajo, debajo de este mensaje, te dejé los datos de Nequi. Abres tu app, haces la transferencia por el valor acordado y me envías por este mismo chat la captura del comprobante. Con eso el equipo verifica y arrancamos. ¿Te quedó claro o te lo explico de otra forma?

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, Juan Camilo. Quedo pendiente: cuando termines me envías la captura del comprobante por acá y el equipo verifica para arrancar con la configuración de tu tienda.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Perfecto Laura, vamos con el Plan Basico. Aquí abajo te dejo los datos de Nequi para que hagas el pago. Mientras tanto, envíame por este chat tu nombre completo, tu teléfono y el nombre de tu tienda; con eso dejamos lista la configuración inicial y arrancamos con la integración a WhatsApp.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** ¡Excelente elección! El Plan Básico te permite automatizar tus ventas desde WhatsApp. Para iniciar, por favor dime tu nombre, teléfono y algunos detalles. Así te guío con el proceso de pago. ¿Qué medio de pago prefieres, Nequi, Daviplata o transferencia?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, arrancamos con el Plan Basico: configuración inicial por COP 100.000 y COP 110.000 al mes. El primer mes queda en COP 210.000 y luego pagas solo la mensualidad, sin permanencia. Envíame por aquí tu nombre, teléfono y detalles del negocio, y te dejo listo el pago y la implementación guiada paso a paso.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. Dime con cuál te queda más fácil y te comparto los datos por aquí mismo para dejarte arrancando hoy.

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. El Plan Básico queda en COP 100.000 de implementación + COP 110.000 al mes, y el primer mes pagas COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y el asistente conversacional. ¿Te envío los datos de Nequi para dejarlo activo?

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con alguien del equipo por este mismo chat. Ya les dejo tu solicitud del Plan Básico para que retomen la conversación contigo aquí. En un momento te escriben.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia, un cobro doble es algo que hay que revisar ya. Te paso con el equipo por este mismo chat para que verifiquen el cobro y te den respuesta. No es una llamada, sigue aquí.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Perfecto, aquí abajo te van los datos de la transferencia a Bancolombia. El primer pago es de COP 210.000 (configuración + primer mes) y luego COP 110.000 mensuales, sin permanencia. Cuando la hagas, mándame por aquí tu nombre y teléfono para dejarte la implementación agendada.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
