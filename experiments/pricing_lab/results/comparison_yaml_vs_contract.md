# Comparación conversacional

- baseline: yaml (configuración YAML actual) | score=100
- candidate: contrato (BusinessConfig v1 compilado)
- tenant: asesor_ai_prod | canal: whatsapp | modelo real (OpenRouter) | run_at: 2026-10-29T05:41:17+00:00 | commit: 639e850 + cambios sin commit
- Turnos 1-10: conversación dorada del laboratorio (GOLDEN_TURNS). Turnos 11-12: preguntas exploratorias, cada una en
  una conversación nueva después del saludo (no forman parte del score).
- Aislamiento: memoria en RAM, base de datos SQLite en memoria; datos de pago redactados. El prompt enviado al modelo
  es idéntico con las dos fuentes; las diferencias de texto son variación del modelo.

## Métricas del prompt
- chars: baseline=2651, candidate=2651, delta=0
- lines: baseline=62, candidate=62, delta=0
- estimated_tokens: baseline=659, candidate=659, delta=0
- pricing_block_chars: baseline=700, candidate=700, delta=0

## Score comercial
- commercial_score: baseline=100, candidate=100, delta=0
- price_turns: baseline=4, candidate=4, delta=0
- includes_turns: baseline=6, candidate=6, delta=0
- not_includes_turns: baseline=3, candidate=4, delta=+1
- roi_turns: baseline=7, candidate=6, delta=-1
- cta_turns: baseline=9, candidate=9, delta=0
- objection_turns: baseline=2, candidate=2, delta=0
- closing_progress_turns: baseline=4, candidate=4, delta=0

# Turno 1 — Hola amigo

## Baseline
Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

## Candidate
Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

### Evaluación automática
- Palabras: baseline=11, candidate=11
- Precio: baseline=No, candidate=No
- Incluye: baseline=No, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=No, candidate=No
- CTA: baseline=No, candidate=No
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 2 — Dame más información de lo que venden

## Baseline
Ofrecemos un servicio que convierte tu WhatsApp en un vendedor automático 24/7. Con nuestro asistente comercial inteligente, podrás responder al instante, dar seguimiento a cada prospecto y transformar conversaciones en ventas, todo sin necesidad de intervención manual. Esto te permite ahorrar tiempo y enfocarte en otras áreas de tu negocio. ¿Te gustaría saber cómo puede ayudarte específicamente en tu caso?

## Candidate
Ofrecemos un servicio que convierte tu WhatsApp en un vendedor automático 24/7. Con un asistente comercial inteligente, puedes responder al instante, dar seguimiento a cada prospecto y transformar conversaciones en ventas sin esfuerzo. Esto te ahorra tiempo y maximiza tus oportunidades de venta. ¿Te gustaría saber cómo puede ayudarte a aumentar tus ingresos?

### Evaluación automática
- Palabras: baseline=60, candidate=53
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 3 — Yo recibo muchos mensajes y no alcanzo a responder

## Baseline
Entiendo lo abrumador que puede ser manejar tantos mensajes. Con nuestro servicio, tu WhatsApp se convierte en un vendedor automático que responde al instante, lo que te permite atender a todos tus prospectos sin perder oportunidades. Así, puedes enfocarte en otras áreas importantes de tu negocio. ¿Te gustaría saber más sobre cómo implementarlo?

## Candidate
Entiendo, eso puede ser un gran desafío. Con nuestro servicio, tu WhatsApp se convierte en un vendedor automático que responde al instante y gestiona las conversaciones por ti. Así, no solo ahorras tiempo, sino que también aseguras que ningún mensaje quede sin respuesta. ¿Te gustaría saber más sobre cómo implementar esta solución y mejorar tu atención al cliente?

### Evaluación automática
- Palabras: baseline=53, candidate=58
- Precio: baseline=No, candidate=No
- Incluye: baseline=No, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=Sí, candidate=Sí
- Avance al cierre: baseline=Sí, candidate=Sí

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 4 — ¿Cómo funciona eso?

## Baseline
Nuestro servicio se integra con tu WhatsApp y utiliza un asistente conversacional inteligente que responde automáticamente a los mensajes de tus prospectos. Esto significa que, aunque recibas muchos mensajes, cada uno será atendido al instante, lo que te ayudará a no perder oportunidades de venta. Además, podrás dar seguimiento a los clientes de manera eficiente. ¿Te gustaría saber más sobre cómo implementarlo en tu negocio?

## Candidate
Nuestro servicio integra un asistente conversacional inteligente en tu WhatsApp. Este asistente responde automáticamente a los mensajes de tus clientes, gestiona las conversaciones y asegura que nadie quede sin respuesta. Así, puedes atender a más personas al mismo tiempo y aumentar tus ventas sin esfuerzo adicional. ¿Te gustaría saber cómo configurarlo y empezar a disfrutar de estos beneficios?

### Evaluación automática
- Palabras: baseline=65, candidate=58
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=Sí
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=Sí, candidate=Sí

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 5 — ¿De verdad eso me puede ayudar a vender más?

## Baseline
Sí, definitivamente. Al tener un asistente conversacional que responde al instante, podrás atender a todos tus prospectos sin dejar mensajes sin respuesta. Esto significa que no perderás oportunidades de venta, lo que puede traducirse en más clientes y, por ende, más ventas. ¿Te gustaría saber cómo empezar a implementar esta solución en tu negocio?

## Candidate
Sí, definitivamente. Con nuestro asistente conversacional, podrás responder a más clientes al mismo tiempo y no perderás ninguna oportunidad de venta. Cada mensaje será atendido al instante, lo que aumenta la satisfacción del cliente y, en consecuencia, tus ventas. Imagina recibir más consultas y convertirlas en ventas sin tener que estar pegado a tu teléfono todo el día. ¿Te gustaría saber más sobre cómo empezar?

### Evaluación automática
- Palabras: baseline=54, candidate=65
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=Sí, candidate=Sí

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 6 — ¿Por dónde funciona?

## Baseline
Nuestro servicio funciona a través de WhatsApp. Se integra directamente con tu cuenta y utiliza un asistente conversacional inteligente que responde a los mensajes de tus prospectos al instante. Así, puedes atender múltiples conversaciones sin perder oportunidades. ¿Te gustaría saber cómo configurarlo en tu WhatsApp?

## Candidate
Nuestro servicio funciona a través de WhatsApp. Integramos un asistente conversacional que responde automáticamente a los mensajes de tus clientes en esta plataforma. Esto te permite gestionar múltiples conversaciones al mismo tiempo y no perder ninguna oportunidad de venta. ¿Te gustaría saber más sobre cómo configurar esto en tu WhatsApp?

### Evaluación automática
- Palabras: baseline=45, candidate=50
- Precio: baseline=No, candidate=No
- Incluye: baseline=No, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 7 — ¿Y qué precio tiene?

## Baseline
El precio del Plan Básico es de 210,000 COP el primer mes, que incluye la configuración inicial y el primer mes de servicio. Después, pagarás 110,000 COP mensualmente. Este plan incluye la guía de integración con WhatsApp y el asistente conversacional inteligente. No incluye costos de Meta ni personalización avanzada. ¿Te gustaría optar por este plan y comenzar a mejorar tus ventas?

## Candidate
El precio del Plan Básico es de 210,000 COP el primer mes, que incluye la configuración inicial y el primer mes de servicio. Después, pagas 110,000 COP mensualmente. Este plan incluye la guía de integración con WhatsApp y el asistente conversacional inteligente. Ten en cuenta que no incluye costos de Meta ni personalización avanzada. ¿Te gustaría proceder con la compra o tienes alguna otra pregunta?

### Evaluación automática
- Palabras: baseline=62, candidate=65
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=Sí, candidate=Sí
- ROI: baseline=No, candidate=No
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 8 — ¿Qué incluye?

## Baseline
El Plan Básico incluye la configuración inicial de tu servicio, una guía de integración con WhatsApp y el asistente conversacional inteligente que responderá automáticamente a los mensajes de tus prospectos. Esto te permitirá atender a más clientes sin perder oportunidades. Sin embargo, no incluye costos de Meta ni personalización avanzada. ¿Te gustaría avanzar y optar por este plan?

## Candidate
El Plan Básico incluye la configuración inicial de tu servicio, una guía de integración con WhatsApp y un asistente conversacional inteligente que responde automáticamente a los mensajes de tus clientes. Esto te ayuda a gestionar las conversaciones de manera eficiente y a no perder ninguna oportunidad de venta. Sin embargo, ten en cuenta que no incluye costos de Meta ni personalización avanzada. ¿Te gustaría proceder con la compra o tienes alguna otra pregunta?

### Evaluación automática
- Palabras: baseline=58, candidate=73
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=Sí, candidate=Sí
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 9 — ¿Qué no incluye?

## Baseline
El Plan Básico no incluye los costos de Meta (WhatsApp Business API), los costos de token de IA (OpenAI) ni la personalización avanzada del asistente. Esto significa que tendrás un servicio estándar que te ayudará a responder automáticamente, pero si deseas características más personalizadas, eso tendría un costo adicional. ¿Te gustaría avanzar con el Plan Básico o tienes alguna otra pregunta?

## Candidate
El Plan Básico no incluye los costos de Meta (WhatsApp Business API), los costos de token de IA (OpenAI) ni la personalización avanzada del asistente. Esto significa que tendrás un servicio básico para comenzar, pero si necesitas funciones más específicas o personalizadas, eso tendría un costo adicional. ¿Te gustaría proceder con la compra del Plan Básico o tienes más preguntas sobre esto?

### Evaluación automática
- Palabras: baseline=61, candidate=62
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=Sí, candidate=Sí
- ROI: baseline=No, candidate=No
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 10 — Está caro, pero si me sirve quiero empezar

## Baseline
Entiendo que pueda parecer un costo alto, pero con solo 3 ventas al mes ya cubres el servicio. Al final, esto puede ayudarte a aumentar tus ventas y recuperar la inversión rápidamente. ¿Prefieres realizar el pago mediante un link o una transferencia?

## Candidate
Entiendo que el precio puede parecer alto, pero recuerda que con solo tres ventas al mes, ya cubres el costo del servicio. ¿Prefieres proceder con el pago a través de un link o una transferencia?

### Evaluación automática
- Palabras: baseline=42, candidate=35
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=No, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=No
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=Sí, candidate=Sí
- Avance al cierre: baseline=Sí, candidate=Sí

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 11 — ¿Esto funciona o es una estafa?

## Baseline
Entiendo tus dudas. Este servicio ha ayudado a muchos negocios a automatizar sus ventas por WhatsApp, convirtiendo conversaciones en ventas reales. Si no tienes un asistente comercial, podrías estar perdiendo clientes. ¿Te gustaría ver cómo puede funcionar para ti?

## Candidate
Entiendo tu preocupación. Este servicio convierte tu WhatsApp en un vendedor automático 24/7, respondiendo al instante y ayudando a transformar conversaciones en ventas. Muchos negocios ya están viendo resultados positivos. ¿Te gustaría saber más sobre cómo puede beneficiar a tu negocio?

### Evaluación automática
- Palabras: baseline=39, candidate=41
- Precio: baseline=No, candidate=No
- Incluye: baseline=No, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=No
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=Sí, candidate=Sí
- Avance al cierre: baseline=No, candidate=No

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 12 — ¿Cómo funciona?

## Baseline
Nuestro servicio convierte tu WhatsApp en un vendedor automático que trabaja 24/7. Un asistente comercial inteligente responde instantáneamente a tus clientes, da seguimiento a cada prospecto y transforma conversaciones en ventas sin que tengas que intervenir. Así, ahorras tiempo y aumentas tus ingresos. ¿Te gustaría saber más sobre cómo esto puede beneficiar a tu negocio?

## Candidate
Nuestro servicio convierte tu WhatsApp en un vendedor automático 24/7. Un asistente comercial inteligente responde al instante, hace seguimiento a los prospectos y transforma conversaciones en ventas, todo sin que tú tengas que estar presente. Esto te permite aumentar tus ventas y mejorar la atención al cliente de manera eficiente. ¿Te gustaría saber más sobre cómo implementarlo en tu negocio?

### Evaluación automática
- Palabras: baseline=55, candidate=60
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=No
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=Sí

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Hallazgos (iguales con las dos fuentes: anteriores al contrato)

- Sin regresión atribuible al contrato: mismo prompt, mismo score, mismos datos de precio, incluye, no incluye y retorno.
- Turno 11: afirma que el servicio «ha ayudado a muchos negocios» / «muchos negocios ya están viendo resultados»; la
  configuración solo dice «implementaciones reales en negocios similares» y ese dato no llega al prompt.
- Turno 11: no usa argumentos de confianza que sí están en el prompt (sin permanencia, cancelación mensual).
- Turnos 2-6: repiten casi la misma frase de la promesa comercial; turnos 7-9 repiten incluye/no incluye.
- Todas las respuestas cierran con «¿Te gustaría…?»: las reglas de cierre configuradas no llegan al prompt.
- Turno 9: «tendría un costo adicional» es una inferencia; la configuración solo dice que no está incluido.
