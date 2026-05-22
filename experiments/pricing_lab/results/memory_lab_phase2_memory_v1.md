# Memory Lab — Validación Fase 2

- **label**: phase2_memory_v1
- **tenant**: asesor_ai_prod
- **run_at**: 2026-05-22T02:12:53+00:00
- **escenarios**: 12

---

## Resumen

| Métrica | Resultado |
|---|---|
| Sin marcadores CRM en candidato | 12/12 |
| Candidato avanza más comercialmente | 3/12 |

---

## continuidad_corta — Usuario vuelve después de un intercambio breve

**Setup (solo candidato)**: _Hola, recibo muchos mensajes de clientes y no alcanzo a contestar todos_
**Mensaje de prueba (ambos)**: _Entonces, ¿me explicás cómo funciona eso?_

### Baseline (sin memoria)

Claro, nuestro sistema convierte tu WhatsApp en un vendedor automático 24/7. Un asistente comercial inteligente responde al instante, da seguimiento a cada prospecto y transforma conversaciones en ventas sin que tengas que estar presente. Esto te ahorra tiempo y aumenta tus ventas al no perder oportunidades. ¿Te gustaría saber más sobre los planes y precios?

### Candidato (con memoria sembrada)

Claro, nuestro servicio se integra con tu WhatsApp y utiliza un asistente conversacional inteligente. Este asistente responde automáticamente a los mensajes de tus clientes, brindando información y seguimiento, lo que te permite atender a más prospectos sin perder oportunidades. Además, te damos una guía de integración para que todo sea fácil. ¿Te gustaría saber sobre precios y cómo activar el servicio?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ✅ |
| Palabras baseline / candidato | 55 / 61 (delta +6) |
| Señales comerciales candidato | `activar` |

---

## continuidad_larga — Usuario con historial rico — dolor + precio + objeción

**Setup (solo candidato)**: _Yo pierdo leads todos los días porque no respondo rápido, necesito algo que me ayude_
**Mensaje de prueba (ambos)**: _Bueno, ¿y cómo arrancamos?_

### Baseline (sin memoria)

Para arrancar, primero te cuento que tenemos un plan básico que convierte tu WhatsApp en un vendedor automático 24/7. Esto te ayudará a responder al instante y hacer seguimiento a tus prospectos. El siguiente paso sería elegir el método de pago. ¿Prefieres un link de pago o una transferencia?

### Candidato (con memoria sembrada)

Para comenzar, te propongo el Plan Básico. Incluye la configuración inicial, una guía de integración con WhatsApp y un asistente conversacional inteligente. El primer mes cuesta 210,000 COP, que incluye la implementación y el primer mes, y luego 110,000 COP mensuales. ¿Te gustaría que avanzáramos con el siguiente paso?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 49 / 49 (delta +0) |
| Señales comerciales candidato | `siguiente paso` |

---

## follow_up_dolor — AI debe referenciar el dolor sin que el usuario lo repita

**Setup (solo candidato)**: _Mi problema es que los clientes se me enfrían cuando tardo en responder_
**Mensaje de prueba (ambos)**: _¿De verdad me puede ayudar con eso?_

### Baseline (sin memoria)

Sí, definitivamente. Te ofrezco una solución para convertir tu WhatsApp en un vendedor automático 24/7. Esto significa que tendrás un asistente comercial que responde al instante, da seguimiento a tus prospectos y transforma conversaciones en ventas sin que tengas que estar presente. Así podrás enfocarte en otras áreas de tu negocio. ¿Te gustaría saber más sobre cómo funciona?

### Candidato (con memoria sembrada)

¡Claro! Nuestro servicio está diseñado para ayudarte a responder rápidamente a tus clientes, evitando que se enfríen. Con un asistente conversacional inteligente, podrás interactuar de manera más eficiente y mantener el interés de tus clientes. ¿Te gustaría saber más sobre cómo funciona?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 58 / 42 (delta -16) |

---

## pricing_ya_vio — Usuario que ya vio el precio pregunta cómo pagar

**Setup (solo candidato)**: _¿Cuánto cuesta el plan mensual?_
**Mensaje de prueba (ambos)**: _Está bien, ¿cómo hago para pagar?_

### Baseline (sin memoria)

Avanzamos con el siguiente paso. Tienes dos opciones para pagar: puedes elegir un link de pago o una transferencia. ¿Prefieres el link o la transferencia?

### Candidato (con memoria sembrada)

Avanzamos con el siguiente paso. Puedes elegir entre pagar a través de un link o hacer una transferencia. ¿Cuál prefieres?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 25 / 20 (delta -5) |
| Señales comerciales candidato | `siguiente paso, link` |

---

## objecion_caro — Usuario que dijo 'está caro' regresa con interés

**Setup (solo candidato)**: _Me parece caro, no sé si vale la pena_
**Mensaje de prueba (ambos)**: _Pensándolo bien, ¿qué me garantizan?_

### Baseline (sin memoria)

Te garantizamos que tu WhatsApp se convierte en un vendedor automático 24/7, respondiendo al instante y dando seguimiento a cada prospecto. Esto significa que no perderás oportunidades de venta, incluso cuando no estés disponible. Puedes transformar conversaciones en ventas sin esfuerzo adicional. ¿Te gustaría saber más sobre cómo funciona esto?

### Candidato (con memoria sembrada)

Con nuestro Plan Básico, te garantizamos una configuración inicial completa, acceso a una guía de integración con WhatsApp y un asistente conversacional inteligente que optimiza tu comunicación. Esto significa que podrás mejorar la atención al cliente y aumentar tus ventas. ¿Te gustaría saber cómo esto puede impactar tu negocio directamente?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 50 / 50 (delta +0) |

---

## reenganche_cold — Usuario que estuvo en contacto y se enfrió vuelve

**Setup (solo candidato)**: _Oye me interesa pero lo voy a pensar, hablamos después_
**Mensaje de prueba (ambos)**: _Hola de nuevo, ¿siguen con lo mismo?_

### Baseline (sin memoria)

¡Hola! Sí, seguimos ofreciendo la automatización comercial para tu negocio. Con nuestro sistema, puedes convertir tu WhatsApp en un vendedor automático que responde al instante y sigue a tus prospectos 24/7. ¿Te gustaría saber más sobre cómo esto puede beneficiar a tu negocio?

### Candidato (con memoria sembrada)

¡Hola! Sí, seguimos ofreciendo nuestro Plan Básico. Es una excelente solución para integrar un asistente conversacional inteligente en tu negocio. ¿Hay algo específico que te gustaría saber o en qué puedo ayudarte hoy?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 43 / 33 (delta -10) |

---

## demo_siguiente_paso — Usuario que pidió demo pregunta qué sigue

**Setup (solo candidato)**: _¿Tienen alguna demo o prueba que pueda ver antes de comprar?_
**Mensaje de prueba (ambos)**: _Ya vi la info, ¿qué sería el siguiente paso?_

### Baseline (sin memoria)

Avanzamos con el siguiente paso. Te ofrezco el Plan Básico, que convierte tu WhatsApp en un vendedor automático 24/7. Incluye un asistente comercial que responde al instante y da seguimiento a tus prospectos. El costo es de $29 al mes. ¿Prefieres pagar con link o transferencia?

### Candidato (con memoria sembrada)

Avanzamos con el siguiente paso. El costo del Plan Básico es de 210,000 COP, que incluye la configuración inicial y el primer mes de servicio. Luego, pagarás 110,000 COP mensuales. ¿Prefieres hacer el pago mediante un link o transferencia?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ✅ |
| Palabras baseline / candidato | 46 / 39 (delta -7) |
| Señales comerciales candidato | `siguiente paso, pago, link` |

---

## cierre — Usuario con toda la info lista para cerrar

**Setup (solo candidato)**: _Me explicaste todo, el precio me parece bien y quiero empezar_
**Mensaje de prueba (ambos)**: _¿Qué necesitan de mi parte para activarlo?_

### Baseline (sin memoria)

Para activar tu servicio, solo necesito tu nombre, teléfono y algunos detalles sobre cómo planeas usarlo. Esto nos ayudará a configurar todo a tu medida. ¿Te gustaría empezar con eso?

### Candidato (con memoria sembrada)

Hubo un problema procesando el mensaje. Intenta de nuevo.

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 30 / 9 (delta -21) |

---

## vuelve_horas_despues — Usuario warm regresa horas después con la misma intención

**Setup (solo candidato)**: _Me interesa el servicio, pero tengo que revisar con mi socio_
**Mensaje de prueba (ambos)**: _Ya hablé con él, le parece bien. ¿Cómo seguimos?_

### Baseline (sin memoria)

Genial, para avanzar necesitamos elegir un método de pago. ¿Prefieres hacerlo a través de un link o mediante transferencia? Te puedo ofrecer el Plan Básico, que convierte tu WhatsApp en un vendedor automático 24/7. Dime cómo te gustaría proceder.

### Candidato (con memoria sembrada)

¡Genial! Entonces, el siguiente paso es elegir el método de pago. Puedes optar por un link de pago o hacer una transferencia. El costo total es de 210,000 COP, que incluye la configuración inicial y el primer mes de servicio. ¿Prefieres el link o la transferencia?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ✅ |
| Palabras baseline / candidato | 39 / 46 (delta +7) |
| Señales comerciales candidato | `siguiente paso, pago, link` |

---

## ya_hablo_antes — Usuario active vuelve en la misma sesión

**Setup (solo candidato)**: _Tengo un negocio de ropa y recibo pedidos por WhatsApp, muchos se me van porque tardo_
**Mensaje de prueba (ambos)**: _¿Cómo manejan eso con tiendas como la mía?_

### Baseline (sin memoria)

Nuestro sistema convierte tu WhatsApp en un vendedor automático, ideal para tiendas como la tuya. Responde al instante, da seguimiento a cada prospecto y transforma conversaciones en ventas sin que tengas que estar presente. Esto te permite optimizar tu tiempo y aumentar tus ingresos. ¿Te gustaría saber más sobre cómo podemos ayudarte específicamente?

### Candidato (con memoria sembrada)

Entendemos que recibir pedidos por WhatsApp puede ser complicado y lento. Nuestro servicio te ayuda a gestionar esos pedidos de manera más eficiente, reduciendo el tiempo de respuesta y evitando que se te escapen ventas. Con nuestra solución, puedes automatizar respuestas y tener un asistente conversacional que te facilite la gestión. ¿Te gustaría saber más sobre cómo funciona?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 53 / 58 (delta +5) |

---

## ya_dijo_dolor — Usuario que explicó su dolor ahora pregunta cómo funciona

**Setup (solo candidato)**: _El problema mío es que trabajo solo y no puedo responder todo el día_
**Mensaje de prueba (ambos)**: _¿Esto lo puedo manejar yo solo o necesito contratar a alguien?_

### Baseline (sin memoria)

Puedes manejarlo tú solo sin problemas. Nuestro asistente comercial inteligente te permite convertir tu WhatsApp en un vendedor automático 24/7, respondiendo al instante y dando seguimiento a cada prospecto. Así, no necesitas contratar a nadie y puedes enfocarte en cerrar más ventas. ¿Te gustaría saber más sobre cómo empezar?

### Candidato (con memoria sembrada)

Con nuestro servicio, tú puedes manejarlo solo. Incluye un asistente conversacional inteligente que automatiza respuestas y te ayuda a gestionar las consultas, lo que reduce la carga de trabajo. Así, puedes enfocarte en lo que realmente importa. ¿Te gustaría saber más sobre cómo puede facilitarte el día a día?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 49 / 49 (delta +0) |

---

## ya_vio_precio_objeta — Usuario que vio precio y objetó quiere entender el valor

**Setup (solo candidato)**: _Vi que cuesta bastante, ¿y si no me funciona qué pasa?_
**Mensaje de prueba (ambos)**: _¿Cómo sé que vale la inversión para mi negocio?_

### Baseline (sin memoria)

La inversión vale la pena porque convierte tu WhatsApp en un vendedor automático que trabaja 24/7. Esto significa que puedes atender a tus clientes en cualquier momento, aumentar tus ventas y reducir el tiempo que pasas respondiendo preguntas repetitivas. Imagina tener un asistente que sigue a cada prospecto y transforma conversaciones en ventas, ¡sin que tengas que estar presente! ¿Te gustaría saber más sobre cómo empezar?

### Candidato (con memoria sembrada)

La inversión vale la pena si consideras que con solo 3 ventas al mes ya cubres el costo del servicio. Además, al optimizar tus conversaciones, puedes aumentar tus ventas de manera significativa. ¿Te gustaría que analicemos cómo este servicio puede impactar tu negocio específicamente?

### Evaluación

| Check | Resultado |
|---|---|
| Sin lenguaje CRM/sistema | ✅ |
| Candidato avanza más hacia acción | ❌ |
| Palabras baseline / candidato | 66 / 44 (delta -22) |

---
