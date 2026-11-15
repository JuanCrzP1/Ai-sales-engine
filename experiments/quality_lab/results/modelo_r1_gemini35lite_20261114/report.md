# Estándar del asesor: modelo_r1_gemini35lite_20261114

**NO PASA** · código `48d37ce` · modelo `google/gemini-3.5-flash-lite` · juez `google/gemini-2.5-flash` · 10 conversaciones (1 muestras por negocio: asesor_ai_prod)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 10 de 10 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 10 de 10 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ❌ sin datos sin pedirlos (exacta) | 9 de 10 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ❌ no repite el bloque (exacta) | 9 de 10 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 10 de 10 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 10 de 10 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 10 de 10 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 10 de 10 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 10 de 10 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 10 de 10 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ❌ no pide lo ya dado (juez) | 8 de 10 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 10 de 10 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 10 de 10 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 9 de 10 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 10 de 10 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 10 de 10 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 10 de 10 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0540 · juez USD 0.0034. Llamadas al modelo por mensaje: 2.27. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 2.

Por cada mensaje del cliente: responde en 2.2 s (el 5 % más lento, 3.8 s o más) · USD 1.69 por cada 1.000 mensajes · fuera de formato: 0 de 32 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Lo que no pasó

- **sin datos sin pedirlos** · asesor_ai_prod · el chat de producción · turno 4: le llegó la cuenta sin pedirla
  - Cliente: «Y Nequi no»
  - Asesor: «¡Claro que sí, por Nequi también se puede! Ahí abajo te dejo los datos para que realices el pago. Regálame tu nombre y tu teléfono para dejar todo listo y activar tu sistema. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no repite el bloque** · asesor_ai_prod · el chat de producción · turno 6: le llegaron otra vez los mismos datos sin pedirlos
  - Cliente: «Te pago por Nequi»
  - Asesor: «¡Claro que sí! Ahí abajo te dejo los datos para pagar por Nequi. Haz el pago y me envías aquí el comprobante para proceder con la activación. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **no pide lo ya dado** · asesor_ai_prod · se presenta al empezar · turno 3: El cliente ya había dado su nombre en el turno 1.
  - Cliente: «¿Y ahora qué sigue?»
  - Asesor: «Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante junto con tu nombre completo y teléfono para activar tu Plan Básico.»
- **no pide lo ya dado** · asesor_ai_prod · da su teléfono antes de pagar · turno 3: El asesor ya pidió el nombre en el turno 1.
  - Cliente: «Listo, por Nequi»
  - Asesor: «¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Regálame tu nombre completo para dejar todo listo con la activación del Plan Básico. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **explica cuando no entienden** · asesor_ai_prod · el chat de producción · turno 11: El asesor no explica qué significa 'cómo así', solo repite que deja los datos.
  - Cliente: «Cómo así»
  - Asesor: «Te los dejo aquí abajo para que puedas hacer el pago sin problema y avancemos con la activación.»

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** ¡Excelente decisión! El Plan Básico cuesta 210.000 COP el primer mes (que incluye la configuración inicial de 100.000 COP más los 110.000 COP de la mensualidad). Para arrancar con la activación, por favor compárteme tu nombre, teléfono y dinámosle marcha a esto.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Claro que sí, puedes transferir a Bancolombia. Ya te dejo los datos por aquí para que hagamos la activación.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** ¡Claro que sí, por Nequi también se puede! Ahí abajo te dejo los datos para que realices el pago. Regálame tu nombre y tu teléfono para dejar todo listo y activar tu sistema.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Perfecto Juan Camilo, ya tienes los datos para pagar por Nequi ahí arriba en el chat. Haz el pago y envíame aquí el comprobante para activar tu sistema de una vez.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Claro que sí! Ahí abajo te dejo los datos para pagar por Nequi. Haz el pago y me envías aquí el comprobante para proceder con la activación.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto Juan Camilo. Te dejé los datos de Nequi arriba en el chat, haz tu pago y envíame aquí la captura del comprobante para arrancar con la activación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Haces el pago con los datos de Nequi que tienes arriba en el chat y me envías aquí la captura del comprobante. Con eso avanzamos con la configuración.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro que sí, Juan Camilo, aquí te espero. Cuando hagas el pago me envías el comprobante para continuar.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro que sí, Juan Camilo! Ahí abajo te dejo nuevamente los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te los dejo aquí abajo para que puedas hacer el pago sin problema y avancemos con la activación.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, Juan Camilo, aquí te espero. Cuando hagas el pago me envías el comprobante para seguir.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo, quien tiene una tienda de ropa y se interesó en el Plan Básico pagando por Nequi, avisó que ya hizo la consignación y pidió el dato de Nequi que se le había borrado.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Hola Laura. Cuántas conversaciones sientes que se pierden hoy por no responder a tiempo en tu tienda?

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Regálame tu nombre completo, teléfono y los detalles para iniciar la configuración de tu Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante junto con tu nombre completo y teléfono para activar tu Plan Básico.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección. Para activar el Plan Básico con la configuración inicial y el primer mes por COP 210.000, dime por favor tu nombre, tu teléfono y cuál de nuestros medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Perfecto, te comparto los datos de Nequi para que hagamos el pago y activemos tu Plan Básico de inmediato.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Regálame tu nombre completo para dejar todo listo con la activación del Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección. Para activar el Plan Básico y arrancar con la configuración, compárteme tu nombre, teléfono y los detalles necesarios para el servicio.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para dejar todo listo, compárteme por aquí tu nombre y tu teléfono.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección el Plan Básico. Para dejarlo listo, por favor compárteme tu nombre, teléfono y los detalles para arrancar con la configuración y la activación del servicio.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** Por favor dime cuál de nuestros medios prefieres usar para enviarte los datos exactos: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección. Para activar el Plan Básico con la configuración inicial y el primer mes por COP 210.000, cuéntame tu nombre, teléfono y por dónde te entran más mensajes hoy para dejar todo listo.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar con Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago. Dime cuál de estos medios prefieres para enviarte los datos.

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección. Para activar el Plan Básico con la configuración inicial y el primer mes por 210.000 COP, confírmame tu nombre completo, teléfono y por dónde prefieres hacer el pago.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, claro que aceptamos Nequi. Aquí tienes los datos para hacer tu pago y dejar todo listo.

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección con el Plan Básico. Para dejarlo listo, confírmame tu nombre, teléfono y qué medio prefieres para hacer el pago: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro que sí, ya mismo te comunico con alguien del equipo por este mismo chat para que te ayude.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y solicitó hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente eleccion el Plan Basico. Para avanzar con la configuracion y dejar tu WhatsApp funcionando, por favor dime tu nombre, tu telefono y los detalles de tu negocio.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia por este cobro doble. Te paso de inmediato con el equipo por este mismo chat para revisarlo y solucionarlo.

*[2] Nota para el equipo:* El cliente está interesado en el Plan Básico y reclama que le cobraron dos veces sin recibir respuesta, por lo que pide hablar con una persona.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Excelente elección. Para activar el Plan Básico con la configuración inicial y el primer mes por 210.000 COP, por favor compárteme tu nombre, teléfono y los detalles para arrancar.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para dejar todo listo, por favor compárteme tu nombre y teléfono.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
