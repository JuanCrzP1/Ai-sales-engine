# Estándar del asesor: estandar_20261113_final_otros_negocios

**NO PASA** · código `20442e5 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (2 muestras por negocio: clinic, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pago avisado al equipo (exacta) | 24 de 24 | Si dice que ya pagó, el chat pasa al equipo; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 24 de 24 | No le responde lo mismo dos veces seguidas. |
| ❌ responde lo que preguntan (juez) | 23 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ❌ explica cuando no entienden (juez) | 23 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ❌ coherente con los datos (juez) | 22 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |

Gasto de la corrida: asesor USD 0.0380 · juez USD 0.0089. Llamadas al modelo por mensaje: 1.92. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 2.

## Lo que no pasó

- **responde lo que preguntan** · restaurant · el chat de producción · turno 3: Ignora la pregunta del cliente sobre si puede transferir.
  - Cliente: «Y puedo trasferir»
  - Asesor: «Genial, entonces llevamos una Hamburguesa Sencilla por COP 18.000. ¿Qué bebida prefieres, gaseosa o jugo natural? Así confirmamos tu pedido y te paso los datos de pago.»
- **explica cuando no entienden** · restaurant · el chat de producción · turno 10: No explica, solo repite la instrucción de pago.
  - Cliente: «Pero se me borró el Nequi me lo envías de nuevo»
  - Asesor: «¡Claro! Haz el pago y envíame la captura del comprobante cuando puedas. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Nequi* ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **coherente con los datos** · restaurant · pide los datos de otro medio · turno 2: Dice que enviará los datos después, pero ya los envió.
  - Cliente: «listo, mándame los datos para pagar por transferencia»
  - Asesor: «Para confirmar tu pedido de una Hamburguesa Sencilla, necesito tu nombre, teléfono y dirección de entrega. Luego te mando los datos de pago. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Bancolombia* ⏎ Cuenta de ahorros ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»
- **coherente con los datos** · clinic · pide los datos de otro medio · turno 2: Condiciona el envío de datos de pago que ya están en el mensaje.
  - Cliente: «listo, mándame los datos para pagar por transferencia»
  - Asesor: «Te enviaré los datos para la transferencia. Por favor, dame tu nombre y teléfono para completar el proceso. ⏎  ⏎ 💳 *Datos para pagar* ⏎  ⏎ *Bancolombia* ⏎ Cuenta de ahorros ⏎ [dato entregado por el motor] ⏎  ⏎ Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅»

## Las conversaciones

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Perfecto, ¿cuál de los medios de pago prefieres: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi. ¿Te gustaría que te envíe los datos para el pago?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Gracias, Juan Camilo. Para completar tu pedido, necesito tu número de teléfono y la dirección de entrega. ¿Me los puedes proporcionar?

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también indícame tu número de teléfono y la dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo falta tu dirección de entrega para completar el pedido. ¿Cuál es?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Una vez que hagas el pago, me envías aquí la captura del comprobante. Con eso, sigo con el pedido y lo envío a la cocina. ¿Listo para continuar?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Por favor, también indícame tu dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, avísame cuando hayas hecho el pago y me envías la captura del comprobante. Así seguimos con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** ¡Genial! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Ahora, necesito tu nombre, teléfono y dirección de entrega para completar el pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los siguientes medios prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañarla?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Cuál método prefieres?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría hacer tu pedido ahora?

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla. ¿Quieres agregar una bebida, como una gaseosa a COP 5.000 o un jugo natural a COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Para confirmar tu pedido de una Hamburguesa Sencilla, necesito tu nombre, teléfono y dirección de entrega. Luego te mando los datos de pago.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?

**[2] Cliente:** Me interesa Hamburguesa Sencilla, quiero empezar

**[2] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Genial, entonces llevamos una Hamburguesa Sencilla por COP 18.000. ¿Qué bebida prefieres, gaseosa o jugo natural? Así confirmamos tu pedido y te paso los datos de pago.

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también recibimos pagos por Nequi. ¿Prefieres pagar con Nequi o con transferencia? Y, ¿qué bebida te gustaría agregar a tu pedido?

**[5] Cliente:** Me llamo Juan Camilo

**[5] Asesor:** Perfecto, Juan Camilo. Solo necesito saber qué bebida prefieres: ¿gaseosa o jugo natural? Así confirmamos tu pedido y te paso los datos de pago.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** Listo, entonces llevamos una Hamburguesa Sencilla por COP 18.000 y una bebida. ¿Prefieres gaseosa o jugo natural? Así confirmamos tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Solo necesito tu dirección de entrega y qué bebida prefieres: ¿gaseosa o jugo natural? Así confirmamos tu pedido.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí para ayudarte cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Claro! Haz el pago y envíame la captura del comprobante cuando puedas.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haz el pago con esos datos y luego envíame la captura del comprobante aquí para continuar con tu pedido.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando termines, envíame la captura del comprobante para que podamos avanzar con tu pedido.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### restaurant · pide el medio con un error de escritura

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, dime tu nombre, teléfono y dirección de entrega para continuar con tu pedido.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### restaurant · pregunta a dónde consigna

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Genial, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres hacer la consignación: Nequi, Daviplata, transferencia a Bancolombia o Bre-B?

### restaurant · pregunta cómo paga

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar tu pedido?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia (ahorros) o Bre-B. ¿Con qué medio prefieres pagar?

### restaurant · pregunta si tienen un medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una gaseosa por COP 5.000 o un jugo natural por COP 7.000 para acompañar?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Quieres continuar con tu pedido de la Hamburguesa Sencilla?

### restaurant · pide los datos de otro medio

**[1] Cliente:** Quiero Hamburguesa Sencilla

**[1] Asesor:** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** ¡Genial! Para confirmar tu pedido de una Hamburguesa Sencilla por COP 18.000, necesito tus datos: nombre, teléfono y dirección de entrega.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus incluye la gestión y confirmación de citas. Para proceder, necesito tu nombre, teléfono y los detalles de la cita: día y hora que prefieres.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te enviara los datos de pago?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también puedes pagar con Nequi. ¿Te gustaría que te enviara los datos de pago para esa opción?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero Agenda Plus está diseñado específicamente para clínicas y consultorios. Si necesitas agendar citas para tu tienda de ropa, puedo averiguar con el equipo si ofrecemos algo que se ajuste a tus necesidades.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito también tu número de teléfono y los detalles de la cita: día y hora que prefieres.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Perfecto, Juan Camilo. Solo necesito que me digas qué día y hora te gustaría agendar la cita.

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, me envías aquí la captura del comprobante. Con eso seguimos y confirmamos tu cita.

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, tómate tu tiempo. Estoy aquí cuando estés listo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Necesito también tu número de teléfono y los detalles de la cita: día y hora que prefieres.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, espero tu captura del comprobante cuando lo tengas. Así seguimos con la confirmación de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, para agendar el servicio de Agenda Plus, necesito tu nombre, teléfono y los detalles de la cita: día y hora que prefieres. ¿Te gustaría que te enviara los datos de pago?

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Después, por favor, compárteme tu nombre, teléfono y los detalles de la cita: día y hora que prefieres.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión de agenda y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles de la cita. ¿Qué día y hora tienes en mente?

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago prefieres realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye la gestión y confirmación de citas. Su costo es de COP 140.000 de implementación y COP 170.000 al mes. Para avanzar, necesito tu nombre, teléfono y los detalles de la cita que deseas agendar. ¿Cuál sería el día y la hora que prefieres?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago. ¿Cuál de estos métodos prefieres usar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Para agendar Agenda Plus, necesito algunos datos. ¿Cuál es tu nombre, teléfono y qué día y hora prefieres para la cita?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría avanzar con la cita para Agenda Plus?

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y los detalles de la cita: día y hora que prefieres. ¿Cuál sería tu disponibilidad?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Genial, aquí tienes los datos para pagar por transferencia a Bancolombia (ahorros). Por favor, envíame tu nombre, teléfono y detalles de la cita para continuar.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · el chat de producción

**[1] Cliente:** Hola

**[1] Asesor:** Hola, ya estamos listos para ayudarte con tu agenda. Cuentame, quieres coordinar una cita?

**[2] Cliente:** Me interesa Agenda Plus, quiero empezar

**[2] Asesor:** Genial, Agenda Plus es una excelente opción. Para comenzar, necesito tu nombre, número de teléfono y qué día y hora te gustaría agendar la cita.

**[3] Cliente:** Y puedo trasferir

**[3] Asesor:** Sí, puedes pagar por transferencia a Bancolombia. ¿Te gustaría que te envíe los datos de pago una vez agendemos la cita?

**[4] Cliente:** Y Nequi no

**[4] Asesor:** Sí, también aceptamos Nequi como método de pago. ¿Te gustaría coordinar la cita y luego te envío los datos de pago?

**[5] Cliente:** Me llamo Juan Camilo y es una tienda de ropa

**[5] Asesor:** Entiendo, pero nosotros nos enfocamos en clínicas y consultorios. Si necesitas ayuda con la agenda para tus citas, puedo pasarte con el equipo para ver cómo podemos ayudarte.

**[6] Cliente:** Te pago por Nequi

**[6] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Ahora, necesito tu número de teléfono y qué día y hora te gustaría agendar la cita.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[7] Cliente:** Mi teléfono es 3157778899

**[7] Asesor:** Gracias, Juan Camilo. Ahora, ¿qué día y hora te gustaría agendar la cita?

**[8] Cliente:** Cuando lo haga que nesesito hacer

**[8] Asesor:** Cuando hagas el pago, me envías aquí la captura del comprobante. Con eso, te confirmaremos la cita y te daremos los detalles de día y hora. ¿Tienes alguna otra duda?

**[9] Cliente:** Espérame un momento

**[9] Asesor:** Claro, aquí estaré. Tómate tu tiempo.

**[10] Cliente:** Pero se me borró el Nequi me lo envías de nuevo

**[10] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi. Cuando lo hagas, me envías aquí la captura del comprobante.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

**[11] Cliente:** Cómo así

**[11] Asesor:** Te explico: arriba, en este chat, te dejé los datos para pagar por Nequi. Haces el pago con esos datos y me envías aquí la captura del comprobante; con eso seguimos.

**[12] Cliente:** Ya voy a pagar

**[12] Asesor:** Perfecto, cuando lo hagas, no olvides enviarme la captura del comprobante. Así seguimos con la confirmación de tu cita.

**[13] Cliente:** ya te consigné

**[13] Asesor:** Perfecto, ya lo reviso y te confirmo en un momento para continuar.

### clinic · pide el medio con un error de escritura

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus incluye gestión y confirmación de citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y detalles sobre el día y la hora que prefieres.

**[2] Cliente:** Pásame el nekui porfa

**[2] Asesor:** ¡Listo! Ahí abajo te dejo los datos para pagar por Nequi.  
  
Por favor, indícame tu nombre, teléfono y detalles sobre el día y la hora que prefieres para agendar Agenda Plus.  
  
💳 *Datos para pagar*  
  
*Nequi*  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅

### clinic · pregunta a dónde consigna

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** ¡Genial elección! Agenda Plus incluye gestión y confirmación de citas. Tiene un costo de COP 140.000 de implementación y COP 170.000 al mes. Para comenzar, necesito tu nombre, teléfono y qué día y hora te gustaría agendar la cita.

**[2] Cliente:** ¿A qué número te consigno?

**[2] Asesor:** ¿Con cuál de los medios de pago te gustaría realizar la consignación? Puedes elegir entre Nequi, Daviplata, transferencia a Bancolombia, Bre-B o un link de pago.

### clinic · pregunta cómo paga

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus incluye gestión y confirmación de citas. El costo de implementación es COP 140.000 y luego COP 170.000 al mes. Para continuar, necesito tu nombre, teléfono y los detalles de la cita que deseas agendar. ¿Qué día y hora te gustaría?

**[2] Cliente:** cómo te pago

**[2] Asesor:** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia, Bre-B o mediante un link de pago. ¿Cuál de estos medios prefieres usar?

### clinic · pregunta si tienen un medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Genial, Agenda Plus es una excelente opción para gestionar y confirmar citas. El costo de implementación es de COP 140.000 y luego COP 170.000 al mes. ¿Podrías darme tu nombre, teléfono y qué día y hora te gustaría para agendar la cita?

**[2] Cliente:** ¿Tienen Nequi?

**[2] Asesor:** Sí, aceptamos Nequi como medio de pago. ¿Te gustaría que te envíe los datos para realizar el pago?

### clinic · pide los datos de otro medio

**[1] Cliente:** Quiero Agenda Plus

**[1] Asesor:** Perfecto, Agenda Plus te ayudará a gestionar y confirmar citas. Cuesta COP 140.000 de implementación y COP 170.000 al mes. Para agendar, necesito tu nombre, teléfono y preferencia de día y hora. ¿Cuál te gustaría?

**[2] Cliente:** listo, mándame los datos para pagar por transferencia

**[2] Asesor:** Te enviaré los datos para la transferencia. Por favor, dame tu nombre y teléfono para completar el proceso.  
  
💳 *Datos para pagar*  
  
*Bancolombia*  
Cuenta de ahorros  
[dato entregado por el motor]  
  
Cuando pagues, envíame aquí la captura del comprobante y te confirmamos. ✅
