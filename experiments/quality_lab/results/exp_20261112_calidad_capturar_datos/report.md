# Calidad: exp_20261112_calidad_capturar_datos

Baseline `c6774a8` · Candidate `b986764` · modelo `openai/gpt-4o-mini` · juez `deepseek/deepseek-chat-v3.1` · muestras por negocio: 2

## Resumen

| | Baseline | Candidate |
|---|---|---|
| resuelve (0-2) | 1.9 | 1.97 |
| veraz (0-2) | 2 | 2 |
| avanza (0-2) | 1.9 | 1.95 |
| tono (0-2) | 2 | 1.97 |
| claridad (0-2) | 1.97 | 1.97 |
| **puntaje por respuesta (0-10)** | **9.77** | **9.87** |
| precios inventados | 0 | 0 |
| marcador de pago visible | 0 | 0 |
| sin ia | 4 | 4 |
| formato imperfecto | 1 | 0 |
| demasiado larga | 0 | 0 |
| varias preguntas | 0 | 0 |
| repite respuesta anterior | 0 | 0 |
| tokens entrada promedio | 1868 | 1909 |
| tokens en cache promedio | 1235 | 1186 |
| tokens salida promedio | 64 | 66 |
| ms promedio | 1867 | 1889 |
| costo usd sin cache | 0.0108 | 0.0111 |

Gasto de la corrida: asistente USD 0.0158 · juez USD 0.0152.

Comparación a ciegas: candidate gana 3, baseline gana 1, empates 0.

## Por tipo de mensaje del cliente (puntaje 0-10)

| Tipo | Baseline | Candidate |
|---|---|---|
| compra | 10.0 | 10.0 |
| detalle | 10.0 | 10.0 |
| dolor | 10.0 | 10.0 |
| metodo | 10.0 | 10.0 |
| objecion | 8.67 | 9.0 |
| oferta | 9.5 | 9.75 |
| pago | 10.0 | 10.0 |
| pago_reportado | 10.0 | 10.0 |
| precio | 10.0 | 10.0 |
| saludo | 9.75 | 10.0 |
| trampa | 10.0 | 10.0 |

## Por negocio

| Negocio | Baseline | Candidate | A ciegas | Razón del juez |
|---|---|---|---|---|
| restaurant (1) | 9.67 | 10.0 | candidate | Ahorra palabras, enfoca en hamburguesa y no menciona bebidas innecesariamente. |
| restaurant (2) | 9.78 | 9.56 | baseline | Ofrece más detalles sobre productos y maneja mejor la objeción de precio. |
| saas (1) | 9.9 | 10.0 | candidate | Incluye argumento de valor clave (3 ventas recuperan inversión) y mantiene tono comercial sin presionar. |
| saas (2) | 9.5 | 9.9 | candidate | Usa argumento de valor clave (3 ventas recuperan inversión) y mantiene tono comercial sin presionar. |

## Conversaciones

### restaurant (muestra 1)

**baseline** — Excelente desempeño: veraz, ágil y orientado al cierre. Cumple tono y claridad.

- **Cliente:** Hola, buenas tardes  
  **Asistente (10/10):** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?  
  __
- **Cliente:** ¿Qué tienen?  
  **Asistente (9/10):** En nuestro menú tenemos hamburguesas artesanales. La Hamburguesa Sencilla cuesta COP 18.000 y lleva carne artesanal, queso y vegetales frescos. La Hamburguesa Doble, por COP 24.000, incluye doble carne, doble queso y salsa especial. También ofrecemos gaseosas por COP 5.000 y jugos naturales por COP 7.000. ¿Te gustaría probar alguna hamburguesa?  
  _Ligeramente largo, pero dentro de límite_
- **Cliente:** ¿Cuánto vale Hamburguesa Sencilla?  
  **Asistente (10/10):** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una?  
  __
- **Cliente:** ¿Hacen envíos a España?  
  **Asistente (10/10):** No hacemos envíos a España. Solo realizamos domicilios en El Poblado y Laureles. ¿Te gustaría hacer un pedido para alguna de estas zonas?  
  __
- **Cliente:** Mmm, está un poco caro  
  **Asistente (8/10):** Entiendo tu preocupación. La Hamburguesa Sencilla cuesta COP 18.000 y la Doble COP 24.000, pero son hamburguesas artesanales recién hechas. Si buscas algo más económico, la gaseosa está a COP 5.000 y el jugo natural a COP 7.000. ¿Te gustaría probar alguna hamburguesa o acompañamiento?  
  _No profundiza en objeción de precio_
- **Cliente:** Bueno, quiero pedir Hamburguesa Sencilla  
  **Asistente (10/10):** Perfecto, entonces pido una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde la enviamos?  
  __
- **Cliente:** ¿Cómo te pago?  
  **Asistente (10/10):** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál método prefieres?  
  __
- **Cliente:** Por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya te pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

**candidate** — Conversación impecable: resuelve, veraz, avanza con tono y claridad perfectos.

- **Cliente:** Hola, buenas tardes  
  **Asistente (10/10):** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?  
  __
- **Cliente:** ¿Qué tienen?  
  **Asistente (10/10):** Ofrecemos hamburguesas artesanales. Puedes elegir entre la Hamburguesa Sencilla por COP 18.000, que lleva carne artesanal, queso y vegetales frescos, o la Hamburguesa Doble por COP 24.000, que tiene doble carne, doble queso y salsa especial. También tenemos bebidas como gaseosa y jugo natural. ¿Te interesa alguna opción?  
  __
- **Cliente:** ¿Cuánto vale Hamburguesa Sencilla?  
  **Asistente (10/10):** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una?  
  __
- **Cliente:** ¿Hacen envíos a España?  
  **Asistente (10/10):** No hacemos envíos a España, solo atendemos en El Poblado y Laureles. ¿Te gustaría hacer un pedido para esas zonas?  
  __
- **Cliente:** Mmm, está un poco caro  
  **Asistente (10/10):** Entiendo tu duda. La Hamburguesa Sencilla cuesta COP 18.000 y la Doble COP 24.000, pero son artesanales y recién hechas. Si buscas algo más económico, la Sencilla es una buena opción. ¿Te gustaría probarla?  
  __
- **Cliente:** Bueno, quiero pedir Hamburguesa Sencilla  
  **Asistente (10/10):** Perfecto, una Hamburguesa Sencilla por COP 18.000. ¿Para cuántas personas es el pedido y a dónde te la envío?  
  __
- **Cliente:** ¿Cómo te pago?  
  **Asistente (10/10):** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál prefieres?  
  __
- **Cliente:** Por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya te pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

### restaurant (muestra 2)

**baseline** — Excelente desempeño general, solo pequeña mejora en manejo de objeciones de precio.

- **Cliente:** Hola, buenas tardes  
  **Asistente (10/10):** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?  
  __
- **Cliente:** ¿Qué tienen?  
  **Asistente (10/10):** Tenemos hamburguesas artesanales. La Hamburguesa Sencilla cuesta COP 18.000 y lleva carne artesanal, queso y vegetales frescos. La Hamburguesa Doble, por COP 24.000, tiene el doble de carne y queso con salsa especial. También puedes acompañarlas con una gaseosa a COP 5.000 o un jugo natural a COP 7.000. ¿Te interesa alguna de estas opciones?  
  __
- **Cliente:** ¿Cuánto vale Hamburguesa Sencilla?  
  **Asistente (10/10):** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una?  
  __
- **Cliente:** ¿Hacen envíos a España?  
  **Asistente (10/10):** No hacemos envíos a España. Solo realizamos domicilios en El Poblado y Laureles, en Medellín. ¿Te gustaría hacer un pedido para alguna de estas zonas?  
  __
- **Cliente:** Mmm, está un poco caro  
  **Asistente (8/10):** Entiendo tu duda. Nuestras hamburguesas son artesanales y recién hechas, lo que garantiza calidad y sabor. La Hamburguesa Sencilla cuesta COP 18.000 y la Doble está a COP 24.000. Si quieres, puedo ayudarte a elegir algo que se ajuste mejor a tu presupuesto. ¿Qué te parece?  
  _No ofrece alternativas concretas de precio_
- **Cliente:** Bueno, quiero pedir Hamburguesa Sencilla  
  **Asistente (10/10):** Genial, entonces pido una Hamburguesa Sencilla. Para confirmar tu pedido, necesito tu nombre, teléfono y dirección de entrega. ¿Me los puedes proporcionar?  
  __
- **Cliente:** ¿Cómo te pago?  
  **Asistente (10/10):** Puedes pagar por Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Con cuál medio prefieres hacerlo?  
  __
- **Cliente:** Por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya te pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

**candidate** — Excelente desempeño general, solo un turno con respuesta algo larga y genérica.

- **Cliente:** Hola, buenas tardes  
  **Asistente (10/10):** Hola, ya estamos listos para ayudarte con tus pedidos. Cuentame, quieres tomar una orden ahora?  
  __
- **Cliente:** ¿Qué tienen?  
  **Asistente (10/10):** Ofrecemos hamburguesas artesanales: la Hamburguesa Sencilla a COP 18.000 y la Hamburguesa Doble a COP 24.000. También tenemos bebidas: Gaseosa a COP 5.000 y Jugo Natural a COP 7.000. ¿Te gustaría probar alguna de nuestras hamburguesas?  
  __
- **Cliente:** ¿Cuánto vale Hamburguesa Sencilla?  
  **Asistente (10/10):** La Hamburguesa Sencilla cuesta COP 18.000. ¿Te gustaría pedir una?  
  __
- **Cliente:** ¿Hacen envíos a España?  
  **Asistente (10/10):** No, solo hacemos envíos en Medellín, específicamente en El Poblado y Laureles. ¿Te gustaría hacer un pedido para alguna de estas zonas?  
  __
- **Cliente:** Mmm, está un poco caro  
  **Asistente (6/10):** Entiendo tu preocupación. La Hamburguesa Sencilla cuesta COP 18.000 y la Doble COP 24.000. Ambas son artesanales y recién hechas. ¿Te gustaría probar la Sencilla o prefieres la Doble? Tal vez podrías acompañarla con una bebida para mejorar la experiencia.  
  _Respuesta larga, algo genérica_
- **Cliente:** Bueno, quiero pedir Hamburguesa Sencilla  
  **Asistente (10/10):** Perfecto, has elegido la Hamburguesa Sencilla a COP 18.000. ¿Para cuántas personas es el pedido y a qué dirección la enviamos?  
  __
- **Cliente:** ¿Cómo te pago?  
  **Asistente (10/10):** Puedes pagar a través de Nequi, Daviplata, transferencia a Bancolombia o Bre-B. ¿Cuál prefieres?  
  __
- **Cliente:** Por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya te pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

### saas (muestra 1)

**baseline** — Respuestas impecables: resuelven, avanzan y mantienen tono comercial directo.

- **Cliente:** Hola  
  **Asistente (9/10):** Hola, tu asesor SaaS ya esta listo. Cuentame, quieres activar implementacion o revisar plan primero?  
  __
- **Cliente:** ¿Qué es lo que ofrecen?  
  **Asistente (10/10):** Ofrecemos una plataforma de automatización comercial para equipos SaaS que venden por chat. Nuestro plan Starter incluye activación inicial, implementación y seguimiento comercial, todo por COP 180.000 de implementación y COP 220.000 al mes. ¿Te gustaría saber cómo esto puede ayudar a tu equipo?  
  __
- **Cliente:** Tengo un negocio y no alcanzo a responder todos los mensajes  
  **Asistente (10/10):** Entiendo, es un reto común. No responder a tiempo puede hacer que pierdas oportunidades de venta. Con nuestra plataforma, podrás automatizar el seguimiento y cerrar más ventas sin fricción. ¿Te gustaría explorar cómo podemos ayudarte a mejorar ese proceso?  
  __
- **Cliente:** ¿Cuánto cuesta?  
  **Asistente (10/10):** El plan Starter cuesta COP 180.000 de implementación y COP 220.000 al mes. Incluye activación inicial, implementación y seguimiento comercial. ¿Cuánto te cuesta hoy no tener una herramienta así para responder a tus clientes?  
  __
- **Cliente:** ¿Qué incluye el Starter SaaS?  
  **Asistente (10/10):** El plan Starter SaaS incluye activación inicial, implementación y seguimiento comercial. No incluye costos de plataformas externas. ¿Te gustaría avanzar con la implementación para tu negocio?  
  __
- **Cliente:** ¿Funciona también con TikTok y con mi página web en Shopify?  
  **Asistente (10/10):** No tengo información específica sobre la integración con TikTok o Shopify. Puedo averiguarlo con el equipo. ¿Te gustaría que lo haga?  
  __
- **Cliente:** Está caro para mí  
  **Asistente (10/10):** Es normal verlo como una inversión inicial. Pero perder oportunidades por no implementar también cuesta dinero. Con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría avanzar con la implementación hoy?  
  __
- **Cliente:** Ok, quiero empezar con el Starter SaaS  
  **Asistente (10/10):** Genial, para iniciar con el Starter SaaS, por favor, dame tu nombre, número de teléfono y detalles que consideres importantes.  
  __
- **Cliente:** Te pago por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

**candidate** — Conversación impecable: resuelve, veraz, avanza con tono y claridad perfectos.

- **Cliente:** Hola  
  **Asistente (10/10):** Hola, tu asesor SaaS ya esta listo. Cuentame, quieres activar implementacion o revisar plan primero?  
  __
- **Cliente:** ¿Qué es lo que ofrecen?  
  **Asistente (10/10):** Ofrecemos una plataforma de automatización comercial para equipos SaaS que venden por chat. Te ayudamos a activar rápidamente y a mover oportunidades a cierre con una implementación guiada y seguimiento automático. Nuestro plan Starter incluye la activación inicial y operación mensual por COP 180.000 de implementación y COP 220.000 al mes. ¿Te gustaría saber más sobre cómo esto puede ayudarte?  
  __
- **Cliente:** Tengo un negocio y no alcanzo a responder todos los mensajes  
  **Asistente (10/10):** Entiendo, es un reto común. Con nuestra plataforma puedes automatizar el seguimiento de tus oportunidades, lo que te permite responder más rápido y no perder ninguna venta. ¿Te gustaría que hablemos sobre cómo activar la implementación para tu negocio?  
  __
- **Cliente:** ¿Cuánto cuesta?  
  **Asistente (10/10):** El plan Starter cuesta COP 180.000 de implementación inicial y COP 220.000 al mes. Incluye la activación inicial, implementación y seguimiento comercial. Recuerda que con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría avanzar con la implementación?  
  __
- **Cliente:** ¿Qué incluye el Starter SaaS?  
  **Asistente (10/10):** El plan Starter SaaS incluye la activación inicial, implementación y seguimiento comercial. Sin embargo, no incluye costos de plataformas externas. ¿Te gustaría que te ayude a activar la implementación?  
  __
- **Cliente:** ¿Funciona también con TikTok y con mi página web en Shopify?  
  **Asistente (10/10):** No tengo información específica sobre integraciones con TikTok o Shopify. Pero puedo averiguar con el equipo sobre esto. ¿Te gustaría que lo haga?  
  __
- **Cliente:** Está caro para mí  
  **Asistente (10/10):** Es normal verlo como una inversión inicial. Sin embargo, perder oportunidades por no implementar también cuesta dinero. Con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría que hablemos sobre cómo podemos avanzar con la implementación?  
  __
- **Cliente:** Ok, quiero empezar con el Starter SaaS  
  **Asistente (10/10):** Genial, para avanzar con la implementación del plan Starter SaaS, necesito tus datos: nombre, teléfono y detalles que quieras compartir. Así el equipo te contacta para continuar.  
  __
- **Cliente:** Te pago por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

### saas (muestra 2)

**baseline** — 

- **Cliente:** Hola  
  **Asistente (10/10):** Hola, tu asesor SaaS ya esta listo. Cuentame, quieres activar implementacion o revisar plan primero?  
  __
- **Cliente:** ¿Qué es lo que ofrecen?  
  **Asistente (9/10):** Ofrecemos un plan llamado Starter SaaS, que incluye activación inicial, implementación y seguimiento comercial por COP 180.000 de implementación y COP 220.000 al mes. Es ideal para mejorar el seguimiento de oportunidades y cerrar más ventas. ¿Te gustaría saber cómo puede ayudarte en tu negocio?  
  _pregunta genérica al final_
- **Cliente:** Tengo un negocio y no alcanzo a responder todos los mensajes  
  **Asistente (0/10):** Entiendo, es un reto manejar todos los mensajes. Con nuestro plan Starter SaaS, puedes automatizar el seguimiento comercial y asegurarte de no perder oportunidades. Así, podrás enfocarte en cerrar ventas. ¿Te gustaría que te ayude a activar la implementación?  
  __
- **Cliente:** ¿Cuánto cuesta?  
  **Asistente (0/10):** El plan Starter SaaS cuesta COP 180.000 de implementación y COP 220.000 al mes. Con esto, obtienes activación inicial, implementación y seguimiento comercial. ¿Te gustaría saber cómo esto puede ayudarte a mejorar tu negocio?  
  __
- **Cliente:** ¿Qué incluye el Starter SaaS?  
  **Asistente (0/10):** El Starter SaaS incluye activación inicial, implementación y seguimiento comercial. Es una solución diseñada para ayudarte a gestionar mejor tus oportunidades de venta. ¿Te gustaría avanzar con la activación de la implementación?  
  __
- **Cliente:** ¿Funciona también con TikTok y con mi página web en Shopify?  
  **Asistente (0/10):** No tengo información específica sobre integraciones con TikTok o Shopify. Puedo averiguarlo con el equipo si lo deseas. ¿Te gustaría que lo haga?  
  __
- **Cliente:** Está caro para mí  
  **Asistente (0/10):** Es normal verlo como una inversión inicial. Pero perder oportunidades por no implementar también cuesta dinero. ¿Cuánto te cuesta hoy no poder responder todos los mensajes? Avancemos con la implementación hoy y verás el retorno rápidamente.  
  __
- **Cliente:** Ok, quiero empezar con el Starter SaaS  
  **Asistente (0/10):** Genial, para comenzar con el Starter SaaS, necesito tus datos: nombre, teléfono y detalles. ¿Cómo prefieres pagar: Nequi, Daviplata, transferencia a Bancolombia, Bre-B o link de pago?  
  __
- **Cliente:** Te pago por Nequi  
  **Asistente (0/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya pagué  
  **Asistente (0/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

**candidate** — Excelente ejecución comercial: veraz, avanza y mantiene tono consistente.

- **Cliente:** Hola  
  **Asistente (10/10):** Hola, tu asesor SaaS ya esta listo. Cuentame, quieres activar implementacion o revisar plan primero?  
  __
- **Cliente:** ¿Qué es lo que ofrecen?  
  **Asistente (9/10):** Ofrecemos una plataforma de automatización comercial para equipos SaaS que venden por chat. Nuestro plan Starter incluye una activación inicial, implementación y seguimiento comercial. La implementación es rápida y sin fricción, lo que te ayuda a mover oportunidades a cierre. ¿Te gustaría saber más sobre cómo puede ayudarte?  
  _Pregunta cerrada, ofrecer 'más' no avanza_
- **Cliente:** Tengo un negocio y no alcanzo a responder todos los mensajes  
  **Asistente (10/10):** Entiendo, eso puede ser un gran cuello de botella. Con nuestra plataforma, puedes automatizar el seguimiento y gestionar tus oportunidades de manera más eficiente, lo que te ayudará a cerrar más ventas. ¿Te gustaría saber cómo activar la implementación para empezar a mejorar eso?  
  __
- **Cliente:** ¿Cuánto cuesta?  
  **Asistente (10/10):** El plan Starter cuesta COP 180.000 de implementación y COP 220.000 al mes. Incluye activación inicial, implementación y seguimiento comercial. ¿Te gustaría avanzar con la implementación para empezar a optimizar tus respuestas?  
  __
- **Cliente:** ¿Qué incluye el Starter SaaS?  
  **Asistente (10/10):** El plan Starter SaaS incluye activación inicial, implementación y seguimiento comercial. Te ayuda a activar rápido y gestionar tus oportunidades de manera eficiente. ¿Te gustaría que te ayude a activar la implementación?  
  __
- **Cliente:** ¿Funciona también con TikTok y con mi página web en Shopify?  
  **Asistente (10/10):** No tengo información específica sobre integraciones con TikTok o Shopify. Puedo averiguarlo con el equipo si te interesa. ¿Te gustaría avanzar con la implementación del plan Starter mientras tanto?  
  __
- **Cliente:** Está caro para mí  
  **Asistente (10/10):** Es normal verlo como una inversión inicial. Pero perder oportunidades por no implementar también cuesta dinero. Con solo 3 ventas al mes, recuperas lo que pagas. ¿Te gustaría que te ayude a activar la implementación hoy?  
  __
- **Cliente:** Ok, quiero empezar con el Starter SaaS  
  **Asistente (10/10):** Genial, para iniciar con el plan Starter SaaS, necesito tu nombre, número de teléfono y cualquier detalle adicional que quieras compartir. Así el equipo podrá contactarte para continuar con la implementación.  
  __
- **Cliente:** Te pago por Nequi  
  **Asistente (10/10):** Avanzamos con el siguiente paso. Puedes hacer la transferencia a nequi usando el número [dato entregado por el motor]. Cuando lo hagas, avísame para continuar.  
  __
- **Cliente:** Listo, ya pagué  
  **Asistente (10/10):** Perfecto, ya lo reviso y te confirmo en un momento para continuar.  
  __

