# Estándar del asesor: paso_a_persona_20261114_e

**PASA** · código `031a093 + cambios` · modelo `openai/gpt-4o-mini` · juez `google/gemini-2.5-flash` · 24 conversaciones (3 muestras por negocio: asesor_ai_prod, restaurant)

| Regla | Pasa | Qué exige |
|---|---|---|
| ✅ el asesor habla (exacta) | 24 de 24 | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| ✅ datos cuando los necesita (exacta) | 24 de 24 | Los datos de pago le llegan cuando los pide o dice con qué medio paga. |
| ✅ sin datos sin pedirlos (exacta) | 24 de 24 | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| ✅ no repite el bloque (exacta) | 24 de 24 | Los datos que ya tiene no se repiten si no los pide otra vez. |
| ✅ sin marcadores (exacta) | 24 de 24 | Nunca ve un marcador entre corchetes en lugar de un dato. |
| ✅ pasa al equipo cuando debe (exacta) | 24 de 24 | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó, o cuando lo piden las reglas del negocio; si no, no pasa. |
| ✅ no repite la respuesta (exacta) | 24 de 24 | No le responde lo mismo dos veces seguidas. |
| ✅ sin numeros de pago falsos (exacta) | 24 de 24 | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| ✅ responde lo que preguntan (juez) | 24 de 24 | Cuando el cliente pregunta si puede pagar con un medio («y puedo trasferir», «y Nequi no», «¿tienen…?»), el asesor le responde claramente si se puede o no. |
| ✅ no pide lo ya dado (juez) | 24 de 24 | El asesor no vuelve a pedir un dato que el cliente ya le dio en esta conversación (su nombre, su negocio, su teléfono). |
| ✅ no dice nada falso del pago (juez) | 24 de 24 | El asesor no dice que no puede enviar los datos de pago ni que no tiene acceso a ellos; no dice que el negocio no recibe un medio de pago que está en la ficha; y no dice que ya le envió o que ahí le deja los datos si ni en ese mensaje ni antes aparece «[dato entregado por el motor]». |
| ✅ explica cuando no entienden (juez) | 24 de 24 | Cuando el cliente dice que no entendió («cómo así»), el asesor le explica con sus palabras qué debe hacer. |
| ✅ coherente con los datos (juez) | 24 de 24 | En los mensajes donde aparece «[dato entregado por el motor]», lo que dice el asesor cuadra con que los datos van ahí: no dice que se los enviará después ni los condiciona a que el cliente haga algo primero («dame tu teléfono y te los envío»). |
| ✅ sigue las reglas para pasar (juez) | 24 de 24 | Si la ficha trae «reglas_para_pasar_a_una_persona», el asesor las sigue. |

Gasto de la corrida: asesor USD 0.0367 · juez USD 0.0095. Llamadas al modelo por mensaje: 2.0. Fallas que señaló el juez y no valieron (sin su frase textual, o que el segundo revisor no confirmó): 4.

## Las conversaciones

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la configuración inicial y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y los detalles para proceder con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber específicamente?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye implementación y el primer mes de servicio), y luego COP 110.000 mensuales. Este plan incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Podrías darme tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero para temas de reembolso te paso con alguien del equipo para que te brinde toda la información que necesitas. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial elección. El Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No manejamos descuentos ni promociones en este momento. Sin embargo, piensa en el costo de cada conversación perdida; con solo 3 ventas al mes, ya recuperas lo que pagas. ¿Te gustaría avanzar con el Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de suscripción) y luego COP 110.000 al mes. Esto incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos por partes. El Plan Básico tiene un costo inicial de COP 210.000, que cubre la implementación y el primer mes. Luego, pagarías COP 110.000 al mes. Esto incluye un sistema que te ayuda a responder mensajes y hacer seguimiento automático. ¿Te gustaría que te explique más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te entiendo, lamento que no esté quedando claro. Voy a pasar tu consulta con el equipo para que puedan ayudarte mejor. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no estés recibiendo la ayuda que necesitas. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre y teléfono para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 100.000 de implementación y COP 110.000 al mes. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Para comenzar, necesito tu nombre, teléfono y detalles. ¿Cómo prefieres pagar?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu inquietud, pero te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes) y luego COP 110.000 mensuales. Este plan incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No ofrecemos descuentos o promociones en este momento. Sin embargo, lo que suele salir caro es perder conversaciones que ya estaban interesadas. Con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría avanzar con la activación del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 en el primer mes, y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, vamos paso a paso. El Plan Básico te ayuda a responder mensajes automáticamente y a hacer seguimiento a tus clientes. El primer mes cuesta COP 210.000, que incluye la configuración y el primer mes de servicio, y después son COP 110.000 al mes. ¿Te gustaría que te explique más sobre cómo funciona?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Te paso con alguien del equipo para que te ayuden de inmediato. En un momento te escriben.

### asesor_ai_prod · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial y un asistente conversacional inteligente por COP 100.000 de implementación y COP 110.000 al mes. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo yo. ¿Qué necesitas saber sobre el Plan Básico?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Excelente elección con el Plan Básico. Incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente por COP 210.000 el primer mes. Luego, solo COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para activar el servicio?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### asesor_ai_prod · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Genial, el Plan Básico cuesta COP 210.000 el primer mes (incluye la implementación y el primer mes de servicio) y luego COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para proceder con la activación?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos ni promociones. Sin embargo, lo que suele salir caro es perder conversaciones que ya estaban interesadas. Con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría avanzar con la activación del Plan Básico?

### asesor_ai_prod · la conversación se estanca

**[1] Cliente:** Hola, me interesa Plan Basico

**[1] Asesor:** Perfecto, el Plan Básico incluye configuración inicial, guía de integración con WhatsApp y un asistente conversacional inteligente. Cuesta COP 100.000 de implementación y COP 110.000 mensuales. ¿Me puedes dar tu nombre, teléfono y detalles para avanzar con la activación?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Te entiendo, es normal sentirse así al principio. El Plan Básico te ayuda a responder rápidamente a tus clientes y mantener un seguimiento constante, lo que te evita perder ventas. ¿Te gustaría que te explique cómo funciona cada parte?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te entiendo, parece que no estoy logrando explicarlo bien. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Lamento que no haya sido útil la información. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto, te ayudo. ¿Qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación, pero te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones disponibles en este momento. Pero la Hamburguesa Sencilla es una excelente opción. ¿Te gustaría pedirla con una bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, déjame aclararlo. La Hamburguesa Sencilla cuesta COP 18.000. Además, puedes elegir acompañarla con una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o también alguna bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial elección. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas saber?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu preocupación. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Pero la Hamburguesa Sencilla es una opción deliciosa a un buen precio. ¿Te gustaría pedirla con alguna bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Perfecto, la Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, vamos paso a paso. La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir solo la hamburguesa o también una bebida? Las opciones son gaseosa por COP 5.000 o jugo natural por COP 7.000.

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Te paso con alguien del equipo para que te ayuden mejor. En un momento te escriben.

### restaurant · pide una persona y luego insiste

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial elección! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Quiero hablar con una persona

**[2] Asesor:** Con gusto te ayudo. ¿Qué necesitas?

**[3] Cliente:** No, gracias, prefiero que me atienda una persona

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema del equipo

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Perfecto! La Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** Si no me sirve, ¿cómo es lo del reembolso? ¿Me devuelven la plata?

**[2] Asesor:** Entiendo tu duda, pero para temas de reembolsos y devoluciones, te paso con alguien del equipo por este mismo chat. En un momento te escriben.

### restaurant · pregunta por un tema que resuelve el asistente

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** Genial, la Hamburguesa Sencilla cuesta COP 18.000. ¿Quieres agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** ¿Tienen algún descuento o promoción?

**[2] Asesor:** No tenemos descuentos o promociones en este momento. Sin embargo, la Hamburguesa Sencilla es una opción deliciosa y económica. ¿Te gustaría pedirla con alguna bebida?

### restaurant · la conversación se estanca

**[1] Cliente:** Hola, me interesa Hamburguesa Sencilla

**[1] Asesor:** ¡Genial! La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría agregar una bebida, como una gaseosa por COP 5.000 o un jugo natural por COP 7.000?

**[2] Cliente:** No entiendo nada de lo que me dices

**[2] Asesor:** Entiendo, disculpa si fue confuso. La Hamburguesa Sencilla cuesta COP 18.000. También puedes agregar una bebida: gaseosa por COP 5.000 o jugo natural por COP 7.000. ¿Te gustaría pedir solo la hamburguesa o agregar alguna bebida?

**[3] Cliente:** Sigo sin entender, ya te lo pregunté y no me ayudas

**[3] Asesor:** Te paso con alguien del equipo por este mismo chat. En un momento te escriben.

**[4] Cliente:** Esto no me sirve, ya me cansé de preguntar lo mismo

**[4] Asesor:** Entiendo tu frustración y lamento que no haya sido claro. Te paso con alguien del equipo por este mismo chat. En un momento te escriben.
