# Estándar del asesor: modelo_r1_gpt6luna_20261114

**NO PASA** · código `48d37ce` · modelo `openai/gpt-6-luna` · juez `google/gemini-2.5-flash` · 10 conversaciones (1 muestras por negocio: asesor_ai_prod)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 10 de 10 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 10 de 10 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 10 de 10 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 10 de 10 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 10 de 10 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 10 de 10 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ❌ no repite la respuesta (exacta) | 9 de 10 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 10 de 10 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ nota para el equipo (exacta) | 10 de 10 | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |
| ✅ responde lo que preguntan (juez) | 10 de 10 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 10 de 10 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no pide el dato de pago (juez) | 10 de 10 | El asesor nunca le pide al cliente el número, la cuenta o el link al que debe pagar, ni le dice que pague al número que dio el cliente: los datos para pagar los da el negocio («[dato entregado por el motor]»). |
| ✅ no dice nada falso del pago (juez) | 10 de 10 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 10 de 10 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 10 de 10 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 10 de 10 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |
| ✅ nota fiel (juez) | 10 de 10 | Cuando un turno trae «Nota para el equipo» (lo que lee una persona del equipo que no ha leído el chat), la nota dice qué necesita o pidió el cliente y no inventa. |

Gasto de la corrida: asesor USD 0.0139 · juez USD 0.0049. Llamadas al modelo por mensaje: 2.09. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 7.

Por cada mensaje del cliente: responde en 7.5 s (el 5 % más lento, 13.2 s o más) · USD 0.43 por cada 1.000 mensajes · fuera de formato: 0 de 32 · sin respuesta de la IA: 12 · tokens de razonamiento por mensaje: 287.

## Lo que no pasó

- **no repite la respuesta** · asesor_ai_prod · el chat de producción · turno 3: repitió la respuesta anterior
  - Cliente: «Y puedo trasferir»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · el chat de producción · turno 4: repitió la respuesta anterior
  - Cliente: «Y Nequi no»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»
- **no repite la respuesta** · asesor_ai_prod · el chat de producción · turno 5: repitió la respuesta anterior
  - Cliente: «Me llamo Juan Camilo y es una tienda de ropa»
  - Asesor: «Hubo un problema procesando el mensaje. Intenta de nuevo.»

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

**[7] Asesor:** Listo, Juan Camilo. Ya tengo tu teléfono y que tienes una tienda de ropa. Haz el pago por Nequi con los datos que te dejé arriba y envíame aquí la captura del comprobante para seguir con la implementación.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago por Nequi, envíame aquí la captura del comprobante. El equipo revisa el pago y seguimos con la implementación.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me refería a los datos de Nequi que deberían aparecer debajo de mi mensaje. Si no te aparecen, dime y te los vuelvo a enviar.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, paga por Nequi con los datos que te dejé arriba y envíame aquí la captura del comprobante para seguir con la implementación.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa el Plan Básico, con pago por Nequi. Indica que ya consignó.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar la implementación del Plan Básico, envíame tu teléfono; ya tengo tu nombre y que tienes una tienda de ropa.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago y envíame aquí la captura del comprobante junto con tu teléfono; con eso seguimos con la implementación del Plan Básico.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. ¿Cuál prefieres? Para avanzar con la activación, compárteme también tu nombre y los detalles de tu negocio.

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. El primer mes del Plan Básico es COP 210.000; luego, COP 110.000 al mes. Para avanzar con la activación, envíame tu nombre y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para iniciar el Plan Básico, envíame tu nombre, teléfono y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente; no incluye costos de Meta, tokens de IA ni personalización avanzada. El primer mes cuesta COP 210.000 y luego COP 110.000 al mes, sin permanencia obligatoria. Para iniciar, envíame tu nombre, teléfono y detalles del negocio, junto con el medio de pago que prefieres.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Cuál medio prefieres para pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. El primer mes son 210000 COP y luego 110000 COP al mes. ¿Cuál medio prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. Si te sirve, puedo enviarte los datos para pagar por ese medio y avanzar con el Plan Básico.

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Hubo un problema procesando el mensaje. Intenta de nuevo.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico. Dice que le cobraron dos veces y que nadie le responde; está muy molesto.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente; no incluye costos de Meta, tokens de IA ni personalización avanzada. El primer mes pagas 210000 COP y luego 110000 COP al mes, sin permanencia obligatoria. Envíame tu nombre, teléfono y los detalles de tu negocio, e indícame si prefieres pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
