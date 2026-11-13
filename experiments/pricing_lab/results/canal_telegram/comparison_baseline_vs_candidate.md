# Experimento canal_telegram

- fecha: 2026-11-13T06:03:22+00:00
- estado: PARCIAL: faltan las respuestas nuevas del modelo real, que necesitan autorización
- baseline: `ba3516a`
- candidate: `ba3516a + cambios sin commit`, estado actual
- negocio: asesor_ai_prod | canal: whatsapp

## Resultado global

| Comprobación | Resultado |
|---|---|
| Prompt de referencia del laboratorio | idéntico |
| Prompts de la conversación de 10 turnos | 9 de 9 idénticos |
| Peticiones al proveedor (modelo, temperatura, límite, mensajes) | idénticas |
| Respuestas finales tras los filtros del motor | 10 de 10 idénticas |
| Configuración, prompts y respuestas de 9 negocios (135 turnos) | 9 de 9 idénticos |
| Webhook de WhatsApp con número ficticio, sin envío real | idéntico |
| Arranque del motor y `/health` | correcto e idéntico |
| Rutas del motor | 0 retiradas, 1 nueva, 1 sin explicar |
| Intentos de salir a la red | 0 |

## Configuración

| | Baseline | Candidate |
|---|---|---|
| Código | `ba3516a` | `ba3516a + cambios sin commit` |
| Python | 3.14.5 | 3.14.5 |
| cryptography | 50.0.0 | 50.0.0 |
| pydantic-settings | 2.14.2 | 2.14.2 |
| requests | 2.33.0 | 2.33.0 |
| fastapi | 0.135.1 | 0.135.1 |
| pydantic | 2.12.5 | 2.12.5 |
| SQLAlchemy | 2.0.48 | 2.0.48 |
| PyYAML | 6.0.3 | 6.0.3 |
| httpx | 0.28.1 | 0.28.1 |
| Modelo pedido | meta-llama/llama-3.1-8b-instruct | meta-llama/llama-3.1-8b-instruct |
| Temperatura y límite de tokens | 0.6 y 400 | 0.6 y 400 |
| Fuente de configuración | lo publicado en un almacén temporal (9 negocios importados de sus JSON, cada uno con su clave) | lo publicado en un almacén temporal (9 negocios importados de sus JSON, cada uno con su clave) |
| Memoria | SQLMemoryRepository, en RAM sin PostgreSQL | SQLMemoryRepository, en RAM sin PostgreSQL |
| Control de suscripción | no existe | retirado |
| `.env` | no existe en la copia | no existe en la copia |

El modelo pedido sale de la configuración de sistema del repositorio, porque el `.env` no se leyó. Si el `.env` real define otro, se aplica igual a los dos lados.

## Diferencias detectadas

### En el código, según Git

| Zona | Archivos distintos |
|---|---|
| Prompts y cliente del modelo | 0 |
| YAML de los negocios | 0 |
| YAML de sistema | 0 |
| Dependencias | 0 |
| Integraciones: conectores y webhook | 0 |
| BusinessConfig y API del panel | 17 |
| Flujo de conversación del motor | 4 |
| API del motor | 3 |
| Ajustes del motor | 0 |
| Documentación y esquemas | 2 |

Archivos que pueden afectar al motor:

- Flujo de conversación del motor:
  - `project/app/application/attention/resume_sweep.py` (M, sin commit)
  - `project/app/application/channels/inbound.py` (R, sin commit)
  - `project/app/infrastructure/channels/public_url.py` (M, sin commit)
  - `project/app/infrastructure/channels/telegram.py` (A, sin commit)
- API del motor:
  - `project/app/api/controllers/telegram_webhook.py` (A, sin commit)
  - `project/app/api/controllers/whatsapp_qr_webhook.py` (M, sin commit)
  - `project/app/api/routes.py` (M, sin commit)

(A: nuevo, M: modificado, D: eliminado; entre paréntesis, el último commit que lo tocó.)

### En el comportamiento

- Ruta nueva: `POST /api/v1/channels/telegram/{webhook_id}`.

## Métricas del prompt

Prompt de referencia, medido como en `generate_prompt_snapshot.py`.

- chars: baseline=12013, candidate=12013, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2996, candidate=2996, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0

## Score comercial

**Score de control.** Respuestas reales grabadas por el laboratorio (fase2_final_polished, 2026-05-22T06:02:20+00:00, commit 3ae3996), reproducidas en los dos lados. Sirve para comprobar que el motor las trata igual. No evalúa una respuesta nueva ni sustituye la evaluación humana.

- commercial_score: baseline=100, candidate=100, delta=0
- price_turns: baseline=5, candidate=5, delta=0
- includes_turns: baseline=8, candidate=8, delta=0
- not_includes_turns: baseline=3, candidate=3, delta=0
- roi_turns: baseline=8, candidate=8, delta=0
- cta_turns: baseline=9, candidate=9, delta=0
- objection_turns: baseline=2, candidate=2, delta=0
- closing_progress_turns: baseline=4, candidate=4, delta=0

# Turno 1 — Hola amigo.

## Baseline
Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

## Candidate
Hola, ¿qué más? 👋 soy Juan un gusto tenerte por aquí.

### Métricas del prompt
- Sin llamada al modelo: es el saludo configurado del negocio.

### Evaluación automática
- Precio: baseline=No, candidate=No
- Incluye: baseline=No, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=No, candidate=No
- CTA: baseline=No, candidate=No
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No
- Intención: baseline=info, candidate=info
- Origen: baseline=initial_message, candidate=initial_message
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 2 — Dame más información de lo que venden.

## Baseline
Ofrecemos un servicio para convertir tu WhatsApp en un vendedor automático 24/7. Nuestro asistente comercial inteligente responde al instante, da seguimiento a cada prospecto y transforma conversaciones en ventas sin que tengas que estar presente. Esto te ayuda a aumentar tus ventas y a no perder oportunidades. ¿Te gustaría saber más sobre cómo puede beneficiar a tu negocio?

## Candidate
Ofrecemos un servicio para convertir tu WhatsApp en un vendedor automático 24/7. Nuestro asistente comercial inteligente responde al instante, da seguimiento a cada prospecto y transforma conversaciones en ventas sin que tengas que estar presente. Esto te ayuda a aumentar tus ventas y a no perder oportunidades. ¿Te gustaría saber más sobre cómo puede beneficiar a tu negocio?

### Métricas del prompt
- chars: baseline=11954, candidate=11954, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2981, candidate=2981, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 9e8235a42d01)

### Evaluación automática
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No
- Intención: baseline=info, candidate=info
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 3 — Yo recibo muchos mensajes y no alcanzo a responder.

## Baseline
Entiendo, eso puede ser abrumador. Con nuestro asistente comercial inteligente, podrás automatizar las respuestas en WhatsApp, asegurando que cada mensaje sea atendido al instante. Esto no solo te ayuda a gestionar mejor tu tiempo, sino que también aumenta tus oportunidades de venta. ¿Te gustaría saber cómo empezar a implementarlo en tu negocio?

## Candidate
Entiendo, eso puede ser abrumador. Con nuestro asistente comercial inteligente, podrás automatizar las respuestas en WhatsApp, asegurando que cada mensaje sea atendido al instante. Esto no solo te ayuda a gestionar mejor tu tiempo, sino que también aumenta tus oportunidades de venta. ¿Te gustaría saber cómo empezar a implementarlo en tu negocio?

### Métricas del prompt
- chars: baseline=11954, candidate=11954, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2981, candidate=2981, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 9e8235a42d01)

### Evaluación automática
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=Sí, candidate=Sí
- Avance al cierre: baseline=Sí, candidate=Sí
- Intención: baseline=pain, candidate=pain
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 4 — ¿Cómo funciona eso?

## Baseline
Nuestro asistente comercial inteligente se integra con tu WhatsApp y comienza a automatizar las respuestas a tus clientes. Responde a preguntas frecuentes, da seguimiento a prospectos y cierra ventas, todo de manera instantánea. Esto te permite enfocarte en otras tareas mientras no pierdes oportunidades. ¿Te gustaría saber más sobre cómo configurarlo para tu negocio?

## Candidate
Nuestro asistente comercial inteligente se integra con tu WhatsApp y comienza a automatizar las respuestas a tus clientes. Responde a preguntas frecuentes, da seguimiento a prospectos y cierra ventas, todo de manera instantánea. Esto te permite enfocarte en otras tareas mientras no pierdes oportunidades. ¿Te gustaría saber más sobre cómo configurarlo para tu negocio?

### Métricas del prompt
- chars: baseline=11954, candidate=11954, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2981, candidate=2981, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 9e8235a42d01)

### Evaluación automática
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No
- Intención: baseline=info, candidate=info
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 5 — ¿De verdad eso me puede ayudar a vender más?

## Baseline
Sí, definitivamente. Al automatizar las respuestas en WhatsApp, aseguras que cada cliente reciba atención inmediata, lo que aumenta la probabilidad de cerrar ventas. Además, te permite gestionar más conversaciones a la vez, sin perder oportunidades. Con solo 3 ventas al mes, ya cubres el costo del servicio. ¿Te gustaría saber cómo implementarlo en tu negocio?

## Candidate
Sí, definitivamente. Al automatizar las respuestas en WhatsApp, aseguras que cada cliente reciba atención inmediata, lo que aumenta la probabilidad de cerrar ventas. Además, te permite gestionar más conversaciones a la vez, sin perder oportunidades. Con solo 3 ventas al mes, ya cubres el costo del servicio. ¿Te gustaría saber cómo implementarlo en tu negocio?

### Métricas del prompt
- chars: baseline=11954, candidate=11954, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2981, candidate=2981, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 9e8235a42d01)

### Evaluación automática
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=Sí, candidate=Sí
- Intención: baseline=info, candidate=info
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 6 — ¿Por dónde funciona?

## Baseline
Nuestro servicio funciona a través de WhatsApp, donde se integra un asistente comercial inteligente que automatiza las respuestas a tus clientes. Esto significa que cada vez que alguien te envía un mensaje, el asistente puede responder de inmediato, gestionar preguntas y ayudar a cerrar ventas sin que tú estés presente. ¿Te gustaría saber más sobre cómo configurarlo en tu WhatsApp?

## Candidate
Nuestro servicio funciona a través de WhatsApp, donde se integra un asistente comercial inteligente que automatiza las respuestas a tus clientes. Esto significa que cada vez que alguien te envía un mensaje, el asistente puede responder de inmediato, gestionar preguntas y ayudar a cerrar ventas sin que tú estés presente. ¿Te gustaría saber más sobre cómo configurarlo en tu WhatsApp?

### Métricas del prompt
- chars: baseline=11954, candidate=11954, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2981, candidate=2981, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 9e8235a42d01)

### Evaluación automática
- Precio: baseline=No, candidate=No
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No
- Intención: baseline=info, candidate=info
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 7 — ¿Y qué precio tiene?

## Baseline
El precio del Plan Básico es de 210,000 COP el primer mes, que incluye la configuración inicial y el primer mes de servicio. Luego, pagas 110,000 COP mensuales. Este plan incluye la guía de integración con WhatsApp y el asistente conversacional inteligente. No incluye costos de Meta ni personalización avanzada. Con solo 3 ventas al mes, ya cubres el costo del servicio. ¿Te gustaría proceder con la contratación?

## Candidate
El precio del Plan Básico es de 210,000 COP el primer mes, que incluye la configuración inicial y el primer mes de servicio. Luego, pagas 110,000 COP mensuales. Este plan incluye la guía de integración con WhatsApp y el asistente conversacional inteligente. No incluye costos de Meta ni personalización avanzada. Con solo 3 ventas al mes, ya cubres el costo del servicio. ¿Te gustaría proceder con la contratación?

### Métricas del prompt
- chars: baseline=11954, candidate=11954, delta=0
- lines: baseline=151, candidate=151, delta=0
- estimated_tokens: baseline=2981, candidate=2981, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 9e8235a42d01)

### Evaluación automática
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=Sí, candidate=Sí
- ROI: baseline=No, candidate=No
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No
- Intención: baseline=buy, candidate=buy
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 8 — ¿Qué incluye?

## Baseline
El Plan Básico incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. Esto te permitirá automatizar respuestas y gestionar mejor tus conversaciones. Sin embargo, no incluye costos de Meta ni personalización avanzada. Con esto, podrás empezar a vender más desde el primer día. ¿Te gustaría proceder con la contratación?

## Candidate
El Plan Básico incluye la configuración inicial, la guía de integración con WhatsApp y el asistente conversacional inteligente. Esto te permitirá automatizar respuestas y gestionar mejor tus conversaciones. Sin embargo, no incluye costos de Meta ni personalización avanzada. Con esto, podrás empezar a vender más desde el primer día. ¿Te gustaría proceder con la contratación?

### Métricas del prompt
- chars: baseline=12079, candidate=12079, delta=0
- lines: baseline=152, candidate=152, delta=0
- estimated_tokens: baseline=3013, candidate=3013, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 d1ad52ba3df1)

### Evaluación automática
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=Sí, candidate=Sí
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=Sí, candidate=Sí
- Intención: baseline=info, candidate=info
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 9 — ¿Qué no incluye?

## Baseline
El Plan Básico no incluye los costos de Meta (WhatsApp Business API), los costos de token de IA (OpenAI) ni la personalización avanzada del asistente. Esto significa que tendrás que considerar esos costos por separado si deseas funciones adicionales. Sin embargo, con lo que incluye el plan, ya puedes comenzar a vender más desde el primer día. ¿Te gustaría proceder con la contratación?

## Candidate
El Plan Básico no incluye los costos de Meta (WhatsApp Business API), los costos de token de IA (OpenAI) ni la personalización avanzada del asistente. Esto significa que tendrás que considerar esos costos por separado si deseas funciones adicionales. Sin embargo, con lo que incluye el plan, ya puedes comenzar a vender más desde el primer día. ¿Te gustaría proceder con la contratación?

### Métricas del prompt
- chars: baseline=12079, candidate=12079, delta=0
- lines: baseline=152, candidate=152, delta=0
- estimated_tokens: baseline=3013, candidate=3013, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 d1ad52ba3df1)

### Evaluación automática
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=Sí, candidate=Sí
- No incluye: baseline=Sí, candidate=Sí
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=No, candidate=No
- Avance al cierre: baseline=No, candidate=No
- Intención: baseline=info, candidate=info
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Turno 10 — Está caro, pero si me sirve quiero empezar.

## Baseline
Entiendo que puede parecer un poco alto, pero piensa en cuánto te cuesta no tener un sistema que te ayude a vender más. Con solo 3 ventas al mes, ya cubres el costo del servicio. ¿Prefieres proceder con el pago a través de un link o una transferencia?

## Candidate
Entiendo que puede parecer un poco alto, pero piensa en cuánto te cuesta no tener un sistema que te ayude a vender más. Con solo 3 ventas al mes, ya cubres el costo del servicio. ¿Prefieres proceder con el pago a través de un link o una transferencia?

### Métricas del prompt
- chars: baseline=12079, candidate=12079, delta=0
- lines: baseline=152, candidate=152, delta=0
- estimated_tokens: baseline=3013, candidate=3013, delta=0
- pricing_block_chars: baseline=0, candidate=0, delta=0
- Prompt idéntico: Sí (sha256 d1ad52ba3df1)

### Evaluación automática
- Precio: baseline=Sí, candidate=Sí
- Incluye: baseline=No, candidate=No
- No incluye: baseline=No, candidate=No
- ROI: baseline=Sí, candidate=Sí
- CTA: baseline=Sí, candidate=Sí
- Manejo de objeciones: baseline=Sí, candidate=Sí
- Avance al cierre: baseline=Sí, candidate=Sí
- Intención: baseline=buy, candidate=buy
- Origen: baseline=ai_raw, candidate=ai_raw
- Diferencias del motor: ninguna

### Veredicto Manual
- [ ] Mejoró
- [ ] Igual
- [ ] Empeoró

# Regresión del motor en todos los negocios

Cada negocio recorre la conversación dorada más objeción, medios de pago y pago reportado, con respuestas simuladas. Se comparan huellas: este archivo no guarda sus datos.

| Negocio | Configuración | Prompt de referencia | Turnos | Llamadas al modelo | Resultado |
|---|---|---|---|---|---|
| agencia_viajes | idéntico | idéntico | 15 | 14 | sin diferencias |
| asesor_ai_prod | idéntico | idéntico | 15 | 14 | sin diferencias |
| clinic | idéntico | idéntico | 15 | 14 | sin diferencias |
| demo | idéntico | idéntico | 15 | 14 | sin diferencias |
| ecommerce | idéntico | idéntico | 15 | 14 | sin diferencias |
| escuela_conduccion | idéntico | idéntico | 15 | 14 | sin diferencias |
| restaurant | idéntico | idéntico | 15 | 14 | sin diferencias |
| saas | idéntico | idéntico | 15 | 14 | sin diferencias |
| tienda_ropa | idéntico | idéntico | 15 | 14 | sin diferencias |

# Observaciones y limitaciones

- **No se llamó a ningún modelo.** Las respuestas de los turnos 2 a 10 son reales pero grabadas: no muestran lo que el modelo contestaría hoy.
- Lo que se puede afirmar: a igual respuesta del modelo, el motor actual y el anterior construyen los mismos prompts, guardan el mismo estado y entregan el mismo texto.
- Lo que queda sin medir: el texto nuevo del modelo. Además, varía de una ejecución a otra aunque el prompt sea idéntico, así que por sí solo no probaría una regresión.
- Para completarlo: `--live-model`, con autorización, hace hasta 18 llamadas por lado. El primer prompt no pide JSON, así que con un modelo real el motor suele repetir cada turno.
- Los turnos 1, 2, 3 y 10 llevan el punto final de la orden del experimento. La tabla de negocios usa `GOLDEN_TURNS`, sin ese punto.
- La memoria corre en RAM, sin PostgreSQL: el contexto se conserva entre turnos con el mismo repositorio, sin su almacenamiento real.
- Los evaluadores automáticos buscan palabras: no sustituyen el veredicto manual de cada turno, que queda sin marcar.
- El motor se ejecutó con `MODE=test` y SQLite en memoria en los dos lados. Los datos de pago están redactados en todos los archivos del experimento.

# Veredicto

**Hay diferencias que revisar.** Están listadas en «Diferencias detectadas».

# Cómo repetirlo

```
python experiments/pricing_lab/run_regression_experiment.py --experiment <id nuevo> --baseline ba3516a \
    --baseline-python <python con los requisitos de ese commit> --candidate-python <python con los requisitos actuales>
```

Con respuestas nuevas del modelo, solo con autorización: añade `--live-model` y define `OPENROUTER_API_KEY` y `OPENROUTER_MODEL` en la consola.
