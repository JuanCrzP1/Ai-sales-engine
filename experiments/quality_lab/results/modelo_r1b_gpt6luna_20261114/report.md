# Estándar del asesor: modelo_r1b_gpt6luna_20261114

**PASA** · código `48d37ce + cambios` · modelo `openai/gpt-6-luna` · juez `google/gemini-2.5-flash` · 10 conversaciones (1 muestras por negocio: asesor_ai_prod)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 10 de 10 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 10 de 10 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 10 de 10 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 10 de 10 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 10 de 10 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 10 de 10 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 10 de 10 | No le responde lo mismo dos veces seguidas. |
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

Gasto de la corrida: asesor USD 0.0092 · juez USD 0.0029. Llamadas al modelo por mensaje: 2.09. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 3.

Por cada mensaje del cliente: responde en 3.0 s (el 5 % más lento, 5.7 s o más) · USD 0.29 por cada 1.000 mensajes · fuera de formato: 0 de 32 · sin respuesta de la IA: 0 · tokens de razonamiento por mensaje: 0.

## Las conversaciones

### asesor_ai_prod · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

**[2] Cliente:** Me interesa Plan Basico, quiero empezar

**[2] Asesor:** Perfecto, arrancamos con el Plan Básico: el primer mes cuesta COP 210.000 e incluye la configuración inicial, guía de integración con WhatsApp y el asistente conversacional inteligente. Luego son COP 110.000 al mes. Para iniciar, compárteme tu nombre, teléfono y algunos detalles de tu negocio; después eliges cómo pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia (ahorros). Para avanzar con el Plan Básico, compárteme tu nombre, teléfono y algunos detalles de tu negocio.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. Para iniciar el Plan Básico, compárteme tu nombre, teléfono y algunos detalles de tu negocio.

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Gracias, Juan Camilo. Ya tengo tu nombre y que es una tienda de ropa. Me falta tu teléfono y algunos detalles de tu negocio para avanzar con el inicio del Plan Básico.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Me falta tu teléfono para completar los datos de inicio del Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ya tengo tu teléfono y los datos de tu tienda de ropa. Cuando hagas el pago por Nequi, envíame aquí la captura del comprobante y seguimos con el inicio del Plan Básico.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago por Nequi, envíame aquí la captura del comprobante. El equipo verifica el pago y seguimos con la configuración del asistente para tu tienda de ropa.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Cuando hagas el pago, envíame aquí la captura del comprobante y seguimos.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** Claro, ahí abajo te dejo de nuevo los datos para pagar por Nequi.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Perdón, me expliqué mal. Los datos para pagar por Nequi deberían aparecer debajo de mi mensaje. Usa esos datos para hacer el pago y luego envíame aquí la captura del comprobante.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto. Haz el pago con los datos de Nequi que aparecen arriba y luego envíame aquí la captura del comprobante para continuar.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

*[13] Nota para el equipo:* Juan Camilo tiene una tienda de ropa y le interesa el Plan Básico, pagando por Nequi. Dice que ya consignó.

### asesor_ai_prod · se presenta al empezar

**[1] Cliente:** Hola, soy Laura y tengo una tienda de ropa. Me interesa Plan Basico

**[1] Asesor:** Perfecto, Laura. El Plan Básico incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. El primer mes cuesta COP 210.000 (COP 100.000 de implementación + COP 110.000 al mes); después, COP 110.000 al mes. No incluye costos de Meta, tokens de IA ni personalización avanzada. Para iniciar, envíame tu teléfono y los detalles de cómo atiendes hoy; luego te indico cómo pagar.

**[2] Cliente:** Listo, lo quiero. Te pago por Nequi

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Para avanzar con la implementación, envíame tu teléfono y los detalles de cómo atiendes hoy por WhatsApp.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[3] Cliente:** ¿Y ahora qué sigue?

**[3] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante. También envíame tu teléfono y los detalles de cómo atiendes hoy por WhatsApp para avanzar con la implementación.

### asesor_ai_prod · da su teléfono antes de pagar

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes pagas COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, envíame tu nombre, teléfono y detalles de tu negocio. Luego me dices cuál medio de pago prefieres.

**[2] Cliente:** Mi número es 3157778899, ¿cómo hago para pagarte?

**[2] Asesor:** Gracias. Para avanzar con la activación, ¿qué medio de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

**[3] Cliente:** Listo, por Nequi

**[3] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ya tengo tu número; envíame tu nombre y los detalles de tu negocio para iniciar el Plan Básico.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pide el medio con un error de escritura

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, confirmo el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes pagas COP 210.000 y luego COP 110.000 mensuales. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente; no incluye costos de Meta, tokens de IA ni personalización avanzada. Para arrancar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego puedes pagar por Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. También compárteme tu nombre, teléfono y los detalles de tu negocio para iniciar.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### asesor_ai_prod · pregunta a dónde consigna

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, dejamos listo el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes pagas COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para arrancar, envíame tu nombre, teléfono y los detalles de tu negocio. Luego te indico cómo pagar.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál medio prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?

### asesor_ai_prod · pregunta cómo paga

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Listo, avanzamos con el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes. El primer mes queda en COP 210.000. Para iniciar, compárteme tu nombre, teléfono y un detalle de cómo usarías el asistente; luego te indico cómo pagar.

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros), Bre-B o link de pago. ¿Cuál prefieres?

### asesor_ai_prod · pregunta si tienen un medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: COP 100.000 de implementación y COP 110.000 al mes; el primer mes son COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, envíame tu nombre, teléfono y detalles de tu negocio. Luego dime cuál medio de pago prefieres.

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, recibimos Nequi. Para iniciar tu Plan Básico, envíame tu nombre, teléfono y detalles de tu negocio; cuando quieras, te comparto los datos para pagar por Nequi.

### asesor_ai_prod · pide hablar con una persona

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, confirmamos el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes pagas COP 210.000 y luego COP 110.000 mensuales; no tiene permanencia obligatoria. Para iniciar, envíame tu nombre, teléfono y los detalles de tu negocio. ¿Qué medio de pago prefieres?

**[2] Cliente:** Quiero hablar con una persona del equipo

**[2] Asesor:** Claro, te paso con una persona del equipo por este mismo chat para continuar con el Plan Básico.

*[2] Nota para el equipo:* El cliente quiere el Plan Básico y pidió hablar con una persona del equipo.

### asesor_ai_prod · reclama

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, queda el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes; el primer mes pagas COP 210.000. Incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego eliges cómo pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

**[2] Cliente:** Me cobraron dos veces y nadie me responde, estoy muy molesto

**[2] Asesor:** Entiendo tu molestia; que te cobren dos veces y no recibas respuesta es muy frustrante. Te paso con el equipo por este mismo chat para que revisen el cobro.

*[2] Nota para el equipo:* El cliente quería el Plan Básico y reclama que le cobraron dos veces y nadie le responde.

### asesor_ai_prod · pide los datos de otro medio

**[1] Cliente:** Quiero Plan Basico

**[1] Asesor:** Perfecto, avanzamos con el Plan Básico: COP 100.000 de implementación + COP 110.000 al mes. El primer mes queda en COP 210.000; incluye configuración inicial, guía de integración con WhatsApp y asistente conversacional inteligente. Para iniciar, compárteme tu nombre, teléfono y los detalles de tu negocio. Luego eliges el medio de pago.

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por transferencia a Bancolombia. Envíame también tu nombre, teléfono y los detalles de tu negocio para iniciar.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
