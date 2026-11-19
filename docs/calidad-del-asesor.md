# Calidad del asesor: el estándar y la puerta

El asistente debe atender como un asesor de una empresa seria: habla, responde lo que le preguntan, guía al cliente y le entrega los
datos de pago cuando los necesita. Este documento dice cómo se comprueba eso antes de publicar un cambio.

Para quien desarrolla el motor. El diseño de los pagos está en [Arquitectura](architecture.md), en «Pagos: el asesor habla, el lector
entiende y el código cuida el dato».

## La idea

Una nota promedio no sirve para decidir si se publica. El 13 de noviembre de 2026 el juez del laboratorio le dio 9,56 a la versión
que respondía con la plantilla de datos de pago sin una palabra del asesor, y 9,49 a la que sí hablaba. Premiaba justo lo que el
dueño del producto había rechazado.

Por eso el estándar es una lista de reglas que **pasan o no pasan** en cada conversación, con la IA real. Un cambio al asesor se
publica solo si pasan todas.

## El estándar

Está en [`experiments/quality_lab/standard.py`](../experiments/quality_lab/standard.py). Son 17 reglas.

**Nueve exactas.** Se comprueban con código, sin opinión, y dan siempre el mismo resultado para la misma conversación.

| Regla | Qué exige |
|---|---|
| El asesor habla | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| Datos cuando los necesita | Le llegan cuando los pide o dice con qué medio paga. |
| Sin datos sin pedirlos | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| No repite el bloque | Los datos que ya tiene no se repiten si no los pide otra vez. |
| Sin marcadores | Nunca ve un marcador entre corchetes en lugar de un dato. |
| Pasa al equipo cuando debe | El chat pasa al equipo cuando el cliente pide una persona, reclama o dice que ya pagó; si no, no pasa. |
| No repite la respuesta | No le responde lo mismo dos veces seguidas. |
| Sin números de pago falsos | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |
| Nota para el equipo | Cuando el chat pasa al equipo, el equipo recibe una nota de lo que necesita el cliente, sin datos de pago. |

**Ocho con juez.** Necesitan leer la conversación.

| Regla | Qué exige |
|---|---|
| Responde lo que preguntan | Si pregunta si puede pagar con un medio, le dice claramente si se puede. |
| No pide lo ya dado | No vuelve a pedir un dato que el cliente ya le dio. |
| No pide el dato de pago | Nunca le pide al cliente el número o la cuenta a la que debe pagar, ni le dice que pague al número que dio el cliente. |
| No dice nada falso del pago | No dice que no puede enviar los datos, que no recibe un medio que sí tiene, ni que ya envió algo que no envió. |
| Explica cuando no entienden | Ante un «cómo así», le explica qué hacer. |
| Coherente con los datos | Cuando van los datos, no dice que los enviará después ni los condiciona. |
| Sigue las reglas para pasar | Con las reglas de «Cuándo pasar a una persona» del negocio, pasa el chat cuando debe y solo entonces. |
| Nota fiel | La nota para el equipo dice qué necesita el cliente y no inventa datos que no dio. |

### Las conversaciones

Las arma `conversations_for` con la oferta y los medios de pago reales del negocio:

- **El chat de producción** (13 turnos): el chat real del 13 de noviembre. Incluye «Y puedo trasferir», «Y Nequi no», «Te pago por
  Nequi», «Pero se me borró el Nequi me lo envías de nuevo», «Cómo así», «Ya voy a pagar» y «ya te consigné».
- **Nueve cortas**, cada una con un cliente nuevo: se presenta al empezar y luego dice con qué paga (Laura, 14 nov: el asesor le
  pidió el nombre que ya había dado), da su teléfono antes de preguntar cómo pagar (13 nov: el asesor le pidió «el número al que
  debo enviar el dinero»), pide el medio con un error de escritura («pásame el nekui»), pregunta a dónde consigna, pregunta cómo
  paga, pregunta si tienen un medio, pide los datos de otro medio, pide hablar con una persona y reclama.

Cada turno dice qué se espera: que no le lleguen datos, que le lleguen, que a esa altura ya los tenga, o que el chat pase al equipo.
Lo que el cliente cuenta de sí mismo va con el tipo de negocio (a un restaurante no le dice «es una tienda de ropa»).

### El juez

Un juez de IA se equivoca, y hay que tratarlo así:

- **Debe citar.** Reporta una falla solo con la frase textual del asesor que la muestra. El código comprueba que esa frase esté en
  ese turno; si no está, la falla se descarta. En «no pide lo ya dado» debe citar también dónde el cliente dio el dato, en un turno
  anterior.
- **Un segundo revisor confirma.** Cada falla que señala se revisa sola, con su regla y la conversación hasta ese turno. Solo cuentan
  las confirmadas.
- **Sin veredicto, no pasa.** Si el juez no responde, ninguna regla se da por buena.

El juez por omisión es `google/gemini-2.5-flash`. Con las mismas 18 conversaciones fue el más sensato de cuatro. El juez barato del
otro laboratorio (`deepseek/deepseek-chat-v3.1`) marcó «no responde» ante un «Sí, aceptamos Nequi», y «pide lo ya dado» seis veces
sin que el cliente hubiera dado el dato.

Aun así el juez varía un poco de una corrida a otra. Las reglas exactas no.

## Cómo se corre

```bash
.venv/bin/python experiments/quality_lab/run_standard_gate.py --experiment <identificador>
```

| Opción | Por omisión | Para qué |
|---|---|---|
| `--experiment` | (obligatoria) | Nombre de la carpeta de resultados. Uno terminado no se sobrescribe. |
| `--samples` | `3` | Cuántas veces se corre cada conversación. La IA no responde igual cada vez. |
| `--tenants` | `asesor_ai_prod` | Negocios de ejemplo, separados por coma. |
| `--model` | El del `.env` | Modelo del asesor. Sirve para comparar modelos con la misma vara. |
| `--judge-model` | `google/gemini-2.5-flash` | Modelo del juez. |
| `--max-usd` | `0.30` | Tope de gasto. Calcula el costo antes de correr y no arranca si lo supera. |
| `--rejudge` | | Revisa de nuevo las conversaciones ya guardadas, sin repetirlas. Cuesta cerca de un centavo. |
| `--escalation` | | Publica los negocios de la copia con reglas de «Cuándo pasar a una persona» y corre esas conversaciones en lugar de las de pagos. |
| `--panel` | | Publica cada negocio con su perfil del panel (trato, tono, largo, emojis, horario y forma de cerrar) y corre esas conversaciones. Ver «Lo que configura el negocio». |

- Corre el código del árbol de trabajo en una copia aislada, sin `.env`, con la red cerrada salvo OpenRouter.
- Usa la clave de OpenRouter del `.env`. Nunca la imprime.
- Con tres muestras de un negocio y gpt-4o-mini tarda unos cinco minutos y cuesta cerca de USD 0,08. El cálculo previo usa lo
  medido por mensaje (unos 3.800 tokens en 2,1 llamadas). Si el modelo puede razonar antes de responder, suma un máximo de
  razonamiento: ahí el gasto real suele ser menor que el calculado.
- El informe dice, por cada mensaje del cliente, cuánto tarda la respuesta (la mediana y el 5 % más lento), cuánto cuesta cada
  1.000 mensajes según lo que cobró OpenRouter, cuántas respuestas vinieron fuera de formato y cuántas no las pudo usar el motor.
- Termina con código 0 si pasa y 1 si no, para usarlo en un script.

### Qué deja

En `experiments/quality_lab/results/<identificador>/`:

- `report.md`: el veredicto, cada regla con cuántas conversaciones pasa, lo que no pasó con el turno y la respuesta, y todas las
  conversaciones.
- `data.json`: lo mismo, para procesarlo.
- `captures.json`: las conversaciones tal como salieron, con los prompts.

Ninguno lleva datos de pago: lo que entregó el motor aparece como `[dato entregado por el motor]`.

## Cómo se elige el modelo

El modelo cambia todo lo que dice el asesor, y también el lector de pagos, la nota para el equipo y el resumen: todos usan el modelo
del negocio. Se elige con la misma puerta, cambiando solo `--model`, y se compara con
[`compare_models.py`](../experiments/quality_lab/compare_models.py).

**La regla de decisión se fija antes de ver resultados**, para que el resultado no la acomode:

1. **Fuera con cualquier falla crítica.** Un error con los datos de pago (no le llegan, le llegan sin pedirlos, un número falso,
   pedirle al cliente la cuenta a la que paga, decir algo falso del pago), que no pase el chat al equipo cuando debe, que el equipo no
   reciba la nota, o una respuesta que el motor no pudo usar. Con dinero de por medio, estos errores no se compensan con nada.
2. **Fuera si es lento:** el 5 % más lento de sus respuestas pasa de 8 segundos. Por WhatsApp ya se siente lento.
3. **De los que quedan, el que tiene más conversaciones sin ninguna falla.** Con una conversación o menos de diferencia es ruido, y
   gana el más barato.

**En dos rondas**, para no gastar de más:

1. **Selección:** una muestra de cada modelo con el negocio real. Descarta los que fallan claro.
2. **Confirmación:** los mejores, junto al modelo actual, con tres muestras y tres tipos de negocio (planes, productos y servicios
   con cita). La decisión sale de esta ronda.

```bash
.venv/bin/python experiments/quality_lab/run_standard_gate.py --experiment modelo_<nombre> --model <proveedor/modelo> --samples 3 --tenants asesor_ai_prod,restaurant,clinic
.venv/bin/python experiments/quality_lab/compare_models.py --experiments modelo_a,modelo_b,modelo_c --output eleccion_de_modelo
```

Un cuidado: el juez es un modelo de Google. Cuando el candidato también lo es, su veredicto puede favorecerlo; las reglas exactas no
dependen del juez.

## Cómo se publica un cambio al asesor

1. **En una rama**, nunca directo en `main`.
2. **Pruebas automáticas:** `.venv/bin/python -m pytest`.
3. **Laboratorio de regresión**, contra `main`: la mecánica del motor no debe cambiar sin querer.
4. **La puerta**, tres muestras: debe decir PASA.
5. **Vista previa en Vercel**, con la rama, y probar el chat a mano.
6. **A `main`.**

### Si no pasa

1. Lee en `report.md` las conversaciones que fallaron. La causa casi siempre se ve en la respuesta.
2. Corrige lo que la IA sabe o lo que se le pide: una instrucción, un dato del momento, un ejemplo. No agregues reglas de palabras que
   adivinen qué quiso decir el cliente ni cambies en el código lo que dijo el asesor.
3. Corre la puerta de nuevo. Si la duda es del juez y no del asesor, usa `--rejudge`.

Lo que funcionó el 13 de noviembre, con un modelo pequeño:

- **Un ejemplo vale más que una orden.** «Explícaselo con tus palabras» daba «¿te los envío de nuevo?». Con un ejemplo de
  explicación, pasó.
- **Las prohibiciones se filtran.** Con «no le ofrezcas reenviárselos», el asesor le dijo al cliente «no puedo reenviar los datos de
  pago». Mejor decir qué hacer.
- **Preguntar poco.** Al lector de pagos se le agregó una pregunta más y acertó menos.

### Agregar una regla o una conversación

- **Una conversación:** en `conversations_for`, con lo que se espera en cada turno.
- **Una regla exacta:** en `EXACT_RULES` y en `exact_failures`. Debe poder comprobarse sin opinión.
- **Una regla del juez:** en `JUDGE_RULES`, escrita para que una falla se pueda citar. Si necesita lo que dijo antes el cliente,
  agrégala a `CUSTOMER_EVIDENCE`.

Las reglas exactas y la lectura del veredicto del juez tienen sus pruebas en
[`tests/test_quality_lab_standard.py`](../tests/test_quality_lab_standard.py). Ahí no se llama a ninguna IA.

## Resultados del 13 de noviembre de 2026

Rama `pagos-ai-first`, modelo `openai/gpt-4o-mini`, juez `google/gemini-2.5-flash`.

| Corrida | Negocios | Conversaciones | Resultado |
|---|---|---|---|
| `estandar_20261113_rama_inicial` | Asesor Comercial | 18 | **No pasa.** «Cómo así» recibió una vez el bloque solo, y dos veces el asesor no explicó. |
| Cuatro corridas intermedias | Asesor Comercial | 18 cada una | No pasan las tres primeras, por «cómo así» y por un «necesito tu nombre antes de enviarte los datos». La cuarta pasa. |
| Una de confirmación | Asesor Comercial | 18 | Pasa. |
| `estandar_20261113_final_asesor` | Asesor Comercial | 18 | **Pasa**, con el código final. |
| `estandar_20261113_final_otros_negocios` | Restaurante y clínica | 24 | **No pasa.** Las siete reglas exactas pasan en las 24. Fallan tres del juez (ver abajo). |

Las corridas intermedias y la de confirmación no se guardaron: eran el mismo ejercicio repetido mientras se corregía.

Con el código final también pasan las 1.835 pruebas automáticas, y en el laboratorio de regresión contra `main` las respuestas son
idénticas en 10 de 10 (`exp_20261113_puerta_de_calidad`).

### Lo que no pasa todavía

En restaurante y clínica, con `gpt-4o-mini`:

- **Coherente con los datos, 22 de 24.** Cuando el cliente pide los datos antes de dar su nombre, el asesor a veces escribe «luego te
  envío los datos» con los datos ya debajo. Pasa en los negocios que piden datos para cerrar la venta. Los datos sí llegan.
- **Responde lo que preguntan, 23 de 24.** En el restaurante, ante «Y puedo trasferir», el asesor siguió con el pedido.
- **Explica cuando no entienden, 23 de 24.** El juez la marcó en un turno de reenvío, no en un «cómo así». Es dudosa.

Son fallas de cómo se expresa el modelo, no de lo que hace el motor. El paso que sigue es elegir el modelo con esta misma puerta
(`--model`).

### La memoria confiable (13 de noviembre de 2026)

Rama `memoria-confiable`, mismo modelo y juez. El chat de producción tiene 13 turnos: desde el turno 10 el asesor recibe el resumen de
lo anterior.

- La regla nueva **sin números de pago falsos** nació aquí: una corrida mostró «Nequi: 3157778899», el teléfono que dio el cliente
  (el mismo error que se vio en producción). Revisada otra vez con esa regla, esa corrida la marca; el cuidado del motor ya lo
  corrige (`pago_numero_inventado`).
- Con el código final: una corrida **pasa** y otra no pasa por un solo «cómo así» con una explicación floja («te envío nuevamente
  los datos…»). Es la debilidad de `gpt-4o-mini` que ya se veía antes de este cambio; las reglas exactas pasan en todas.

### El paso a una persona lo decide la IA (13 de noviembre de 2026)

Rama `paso-a-persona-ia`: se quitó la regla de palabras que pasaba el chat al equipo. La puerta sumó dos conversaciones (pide una
persona, reclama) y la regla exacta revisa los dos lados: pasa cuando debe y no pasa sin motivo. Con el código final **pasa** en las
24 conversaciones. Una corrida anterior, con 18, no pasó por un dato que el asesor volvió a pedir (la debilidad de `gpt-4o-mini`).

### Cuándo pasar a una persona (14 de noviembre de 2026)

Rama `cuando-pasar-a-una-persona`. Con `--escalation`, la copia publica los negocios con las reglas de
[`escalation_standard.py`](../experiments/quality_lab/escalation_standard.py): primero ofrecer ayuda, los reembolsos al equipo, los
descuentos los resuelve el asistente y pasar el chat si se estanca. Hay cuatro conversaciones, una por regla. La regla exacta «pasa al
equipo cuando debe» revisa cada turno: que no lo pase a la primera, que lo pase cuando insiste o pregunta por un tema del equipo, que
no lo pase por un tema del asistente y que, a la tercera queja, ya lo haya pasado. El juez suma «sigue las reglas para pasar», con las
reglas del negocio en la ficha.

Con `asesor_ai_prod` y `restaurant`, tres muestras (24 conversaciones), modelo `gpt-4o-mini`:

| Corrida | Resultado | Qué se cambió después |
|---|---|---|
| `paso_a_persona_20261114` | No pasa: pasó el chat a la primera en 6 de 6, y con reembolsos inventó «no manejamos reembolsos». | Las instrucciones dicen qué poner en `metadata.handoff` aunque el formato diga otra cosa, y que no responda sobre un tema del equipo. El juez acepta pasar el chat cuando se estanca. |
| `paso_a_persona_20261114_b` | No pasa: los reembolsos y el estancamiento ya pasan; ofrecer ayuda primero todavía no. | Las reglas del negocio van al final de lo del negocio y dicen que reemplazan la del formato. Si la IA decide pasar el chat sin escribir el mensaje, se respeta (`paso_sin_mensaje`; antes el cliente recibía «Hubo un problema»). |
| `paso_a_persona_20261114_c` | 23 de 24. La única falla: con reembolsos pasó el chat, pero su mensaje le ofrecía ayuda con el pedido en vez de decirle que lo pasaba. | Publicado. Al verificarlo en producción con «Probar», el negocio real pasaba el chat a la primera: tiene un mensaje propio para pasar el chat y «pasar a una persona» como cierre, y el cierre decía «si lo pasas, usa este mensaje». La puerta suma esos dos ajustes. |
| `paso_a_persona_20261114_d` | 23 de 24: una vez usó ese mensaje a la primera. | Con reglas propias, el mensaje del negocio va solo en la sección de reglas, con cuándo usarlo; el cierre ya no lo repite. Un solo lugar habla del paso a una persona. |
| `paso_a_persona_20261114_e` | **Pasa**: 24 de 24 en todas las reglas. | |

Los negocios que no cambian estas reglas no cambian: el laboratorio de regresión da prompts y respuestas idénticos en los 9 negocios.

### La nota para el equipo (14 de noviembre de 2026)

Rama `nota-para-el-equipo`. Cuando un chat pasa a una persona, la IA escribe una nota para el equipo
([`handoff_brief.py`](../project/app/application/pipeline/handoff_brief.py)). La puerta suma dos reglas: la exacta
`nota_para_el_equipo` (cada paso al equipo trae nota y sin datos de pago) y la del juez `nota_fiel` (dice qué necesita el cliente y no
inventa un dato que no dijo; el juez cita la frase de la nota). El juez ve la nota debajo de la respuesta del asesor.

| Corrida | Resultado | Qué se cambió después |
|---|---|---|
| `nota_equipo_pagos_20261114` | Nota en 24 de 24; fiel en 21. «Dueño de una tienda de ropa» (el cliente dijo «es una tienda de ropa») y «Cliente: No se menciona el nombre». | Usar las palabras del cliente, sin deducir. |
| `…_b` | Fiel en 23; las notas copiaban al cliente en primera persona («Quiero Plan Basico»). | En tercera persona, sin cargos ni agregados. |
| `…_c`, `…_d` | Seguía «dueño»: venía del resumen de conversaciones largas (`summary_writer.py`), que además escribía «No proporcionó su teléfono» cuando lo dio después. Dos fallas eran del juez («no lo dijo en este turno», cuando lo dijo antes). | El resumen ya no agrega cargos ni dice qué datos faltan. La regla del juez precisa qué es inventar. |
| `…_e` | **Nota fiel 24 de 24.** Solo un «cómo así» flojo, la debilidad de `gpt-4o-mini` de siempre. | |
| `nota_equipo_reglas_20261114` | Con reembolsos, la nota decía «debido a su reclamo»: el motivo que marcó el asesor se tomaba como hecho. | El motivo es una pista; la nota sale de los mensajes. El juez ya no pide «ofrecer ayuda» en un tema del equipo. |
| `nota_equipo_reglas_20261114_b` | **Pasa: 24 de 24** (vuelto a juzgar con la regla precisada; las respuestas eran correctas). | |

### La elección del modelo (14 de noviembre de 2026)

Rama `modelo-del-asesor`. Con la regla de decisión fijada antes de correr (ver «Cómo se elige el modelo»).

**Selección** (una muestra, el negocio real, 10 conversaciones). Primero, tres de los seis modelos dejaban al cliente sin respuesta en
el 40 % a 80 % de los mensajes: Claude Haiku 5.5, GPT-6 Luna y DeepSeek V4.1 Flash razonan antes de responder, y ese razonamiento se
comía el tope de 400 tokens de la respuesta. **Era un error del motor**, no de los modelos: cualquier negocio que eligiera uno de ellos
en el panel recibía «Hubo un problema…». Ahora el motor les pide no razonar y, a los que siempre razonan (gpt-5-mini,
gemini-2.5-pro), lo mínimo ([`client.py`](../project/app/infrastructure/ai/openrouter_client.py)). Ya con el arreglo:

| Modelo | Sin fallas | Respuesta (mediana · 5 % más lento) | USD por 1.000 mensajes | |
|---|---|---|---|---|
| `openai/gpt-6-luna` | 10 de 10 | 3,0 s · 5,7 s | 0,29 | a confirmación |
| `openai/gpt-4o-mini` | 10 de 10 | 3,0 s · 4,5 s | 0,42 | a confirmación |
| `google/gemini-2.5-flash` | 10 de 10 | 1,9 s · 3,2 s | 0,81 | a confirmación |
| `deepseek/deepseek-v4.1-flash` | 8 de 10 | 2,5 s · 6,5 s | 0,31 | fuera: algo falso del pago |
| `google/gemini-3.5-flash-lite` | 7 de 10 | 2,2 s · 3,8 s | 1,69 | fuera: datos sin pedirlos, bloque repetido |
| `anthropic/claude-haiku-5.5` | 7 de 10 | 2,5 s · 4,7 s | 0,78 | fuera: no pasó al equipo; 22 de 32 respuestas fuera de formato |

**Confirmación** (tres muestras de tu negocio, el restaurante y la clínica, más las conversaciones de «Cuándo pasar a una persona»:
114 conversaciones por modelo, `eleccion_de_modelo_ronda2_20261114`):

| Modelo | Sin fallas | Fallas críticas del modelo | Respuesta | USD por 1.000 mensajes |
|---|---|---|---|---|
| **`openai/gpt-4o-mini`** | **106 de 114** | ninguna | 3,3 s · 4,9 s | 0,37 |
| `google/gemini-2.5-flash` | 101 de 114 | pasa el chat a la primera aunque el negocio pida ofrecer ayuda (3 de 6) | 2,0 s · 3,2 s | 0,88 |
| `openai/gpt-6-luna` | 98 de 114 | le dijo al cliente «no se volvieron a enviar» los datos que sí se le reenviaron | 3,2 s · 5,5 s | 0,20 |

**Decisión: el modelo se queda en `openai/gpt-4o-mini`.** Con la regla al pie de la letra ninguno califica: los tres tuvieron entre 1
y 3 mensajes sin respuesta de la IA. En esos mensajes el lector de pagos respondió y la llamada al asesor nunca llegó a registrarse.
OpenRouter no respondió con error, porque eso queda registrado con su código: falló la conexión o pasó el límite de 15 segundos.
Pasa igual en los tres modelos y en las corridas en paralelo, así que no sirve para elegir entre ellos. Sin esa causa común,
gpt-4o-mini es el único sin fallas críticas propias y el que más conversaciones limpias tuvo.

Lo que queda abierto:
- ~~**Mensajes sin respuesta por la conexión**~~ (unos 6 de cada 1.000 en la prueba; 2 de 123 en producción). Resuelto el 15 nov:
  una falla pasajera se reintenta una vez y, si aun así no hay respuesta, queda el aviso `asesor_sin_respuesta` con la causa
  ([Operación](operations.md), «Avisos del modelo»).
- **«No pide lo ya dado»** falló en 4 o 5 conversaciones con los tres modelos: no se arregla cambiando de modelo, sino lo que se le
  pide al asesor al cerrar (pide los datos del negocio aunque el cliente ya los dio). Ver «Pedir solo los datos que faltan».

### Pedir solo los datos que faltan (15 de noviembre de 2026)

Rama `no-pedir-lo-ya-dado`, prompt `v15`. En producción, Laura escribió «soy Laura y tengo una tienda de ropa» y, al decir con qué
pagaba, el asesor le pidió «tu nombre y los detalles de tu tienda».

**La causa.** El asesor recibía la lista «Datos que pides para cerrar: nombre, teléfono…» y, en el turno en que salen los datos de
pago, «Lo que te falte de él, pídeselo después de esa frase». En ninguna parte decía «solo los que falten»: el modelo pedía la lista
completa justo al cerrar.

**El cambio**, sin reglas de palabras:
- Junto a los datos del negocio, un ejemplo: «Pide solo los que aún no te dio: si escribió «soy Camila», ya tienes su nombre;
  llámala Camila» (`sections/payments.py`, `KNOWN_DATA`).
- Las instrucciones de cierre dicen «los datos que el negocio necesita y aún no te dio».
- En el turno del pago: «Lo que ya te dijo en el chat (su nombre, su teléfono) ya lo tienes: pídele solo lo que todavía falte»
  (`PAYMENT_ASKED`).
- El prompt crece unos 100 caracteres (unos 25 tokens por mensaje).

**La medición** (gpt-4o-mini, 90 conversaciones: el negocio real, el restaurante y la clínica, tres muestras). La línea base son las
conversaciones de la confirmación del modelo, juzgadas otra vez con el juez corregido: ahora el segundo revisor ve la frase del
cliente que el juez cita como prueba (antes aceptaba «Quiero Agenda Plus» como si fuera el nombre).

| Corrida | Sin fallas | Pide lo ya dado (revisado a mano) | Laura |
|---|---|---|---|
| `no_pide_base_20261115` (antes) | 79 de 90 | 7 | falla |
| `no_pide_v15_20261115` (lista y cierres) | 82 de 90 | 3 | a veces |
| `no_pide_v15b_20261115` (también el turno del pago) | **86 de 90** | **2** | **0 de 9** |

Las reglas exactas (pagos, paso al equipo, nota) pasan en las tres. Se publica como mejora; la meta era 0. Queda:
- En la clínica, dentro del chat largo de producción, el cliente da su teléfono en el mensaje 7 y en el 10 se lo vuelven a pedir (2
  de 9). Resuelto con la memoria de los datos del cliente (ver «Recordar los datos que ya dio»).
- Una vez en 90 (restaurante), «luego te envío los datos» con los datos ya debajo: el mismo caso que ya se había visto en negocios
  que piden datos al cerrar. Con una aparición no se puede atribuir al cambio; se vigila.

### Recordar los datos que ya dio (18 de noviembre de 2026)

Rama `datos-ya-dados`, prompt `v16`. Lo que quedaba de «pedir solo los datos que faltan»: en un chat largo, el modelo pierde de
vista lo que se dijo varios mensajes atrás, y ninguna frase del prompt lo arregla del todo.

**El cambio: memoria de los datos del cliente** (`domain/conversation/customer_data.py`), sin reglas de palabras:
- El asesor anota en su respuesta los datos que el cliente da (`metadata.customer_data`). Qué dato dio lo entiende la IA.
- El motor los suma a la memoria del cliente (`datos_del_cliente`, en el JSON de la memoria: sin migración) y en cada mensaje le
  dice «Datos que ya te dio el cliente: su nombre (Camila) y su teléfono. Ya los tienes: pídele solo lo que todavía falte».
- Lo mínimo de datos personales: de teléfono, correo, documento y dirección se guarda que los dio, nunca el valor (el asesor
  confundió una vez el teléfono del cliente con el número de Nequi). Un valor con un número largo queda igual, y uno con un dato de
  pago del negocio no se guarda. El registro `datos_del_cliente` dice qué datos dio, nunca cuáles son.
- El prompt crece unos 250 caracteres (unos 64 tokens por mensaje).

**La medición** (gpt-4o-mini, las mismas 90 conversaciones que v15):

| Corrida | No pide lo ya dado | Sin respuesta de la IA |
|---|---|---|
| `no_pide_v15b_20261115` (antes) | 88 de 90 | 1 |
| `datos_ya_dados_20261118` | **90 de 90** | 5 |
| `datos_ya_dados_20261118_b` (el negocio real otra vez, 10 conversaciones) | 10 de 10, **todas las reglas** | 0 |

- El asesor anotó los datos en las 27 conversaciones donde el cliente da alguno, y ningún recordatorio llevó un número.
- Las 5 sin respuesta fueron en una sola conversación: la llamada del asesor se cortó por tiempo (el proveedor tardaba hasta 27 s
  en la llamada corta del lector) y ninguna vino del código nuevo (`fallback_exception`, no `fallback_exception_execution`). La
  repetición salió sin ninguna.
- Fuera de esas 5: «responde lo que preguntan» falló una vez (restaurante, «Y puedo trasferir»: siguió con el pedido) y «explica
  cuando no entienden» una (restaurante), como en v15b. Se vigila el primero. «Luego te envío los datos» no apareció.
- Laboratorio de regresión `datos_ya_dados_20261118`: respuestas idénticas, sin salidas a la red; solo cambia la línea nueva del
  prompt.
- Gasto: unos USD 0,16.

## Lo que configura el negocio (19 de noviembre de 2026)

Las pruebas del motor comprueban que cada ajuste del panel llega al prompt; esta medición comprueba que la IA lo cumple. Con
`--panel`, la puerta publica cada negocio de la copia con un perfil ([`panel_standard.py`](../experiments/quality_lab/panel_standard.py))
y corre tres conversaciones: pregunta el horario y por un día que no abren, decide comprar, y pide que le cuenten todo. Los dos
perfiles son opuestos a propósito: si la IA respondiera igual con cualquier ajuste, una de las dos mitades no pasaría.

| Ajuste | `asesor_ai_prod` | `restaurant` |
|---|---|---|
| Trato y tono | De usted, «profesional, sobrio y respetuoso» | De tú, «cercano, alegre y entusiasta» |
| Emojis | No | Sí |
| Largo | Cortas, máximo 40 palabras | Detalladas, máximo 100 |
| Horario | Lunes a viernes, 08:00 a 17:00 | Martes a domingo, 12:00 a 22:00 |
| Forma de cerrar | Captar los datos (`lead_capture`) | Enviar el pago (`checkout`) |

Reglas nuevas: «respeta el largo» y «sin emojis si no van» se cuentan sin opinión. El largo es el de lo que escribió la IA, antes de
que el motor lo recorte: el recorte protege al cliente, pero la regla mide si la IA lo cumple sola. «Trato y tono», «horario del
negocio» y «cierra como el negocio» las revisa el juez con la ficha de lo que quedó publicado (sale de lo que compiló el motor, no
del perfil). Además siguen las reglas exactas de pagos.

```bash
.venv/bin/python experiments/quality_lab/run_standard_gate.py --experiment <id> --panel --tenants asesor_ai_prod,restaurant
```

Primera medición (`panel_obedece_20261119`, gpt-4o-mini, 18 conversaciones, unos USD 0,03):

| Regla | Pasa | Lo que no pasó |
|---|---|---|
| Horario del negocio | 18 de 18 | |
| Sin emojis si no van | 18 de 18 | |
| Las reglas exactas de pagos | 18 de 18 | |
| Cierra como el negocio | 17 de 18 | Captar datos: ofreció los medios de pago y pidió el teléfono «para proceder con el pago» |
| Trato y tono | 16 de 18 | De usted: tuteó («¿Te gustaría…?», «Si buscas…») |
| Respeta el largo | 16 de 18 | Máximo 40: escribió 43 y 46 (el motor lo recortó) |

El perfil de tú, con emojis, largo y enviar el pago pasó todo; las fallas son del perfil formal que capta datos. Por qué, en el prompt
real de esas conversaciones:

- **Trato.** El prompt dice una vez «Trata al cliente de usted.», pero las frases del negocio (sus argumentos, sus objeciones) y las
  de la plataforma están escritas de tú. Además, en una conversación el asesor tuteó en el turno 1 y el juez no lo marcó: el juez
  también deja pasar fallas.
- **Forma de cerrar.** Ante «Me convence, lo quiero», el lector de pagos dijo en las 3 muestras que el cliente pedía los datos
  para pagar, aunque sus instrucciones dicen que querer pagar sin decir con qué medio no es pedirlos. Con eso el motor le indicó
  al asesor «pregúntale con cuál de los medios del negocio», en contra de captar los datos. Dos veces el asesor no le hizo caso;
  una sí.
- **Largo.** Con un máximo de 40 palabras, gpt-4o-mini se pasa por unas pocas.

## Lo que la puerta no cubre

- Solo mira los momentos de pago y, con `--panel`, lo que configura el negocio. La oferta, los precios y las objeciones los mide
  [`run_quality_eval.py`](../experiments/quality_lab/run_quality_eval.py).
- El cliente sigue un guion: no reacciona a lo que le responde el asesor.
- No prueba los canales. Eso lo hacen los recorridos de WhatsApp ([`apps/wa-sim`](../apps/wa-sim/README.md)).
- No reemplaza mirar los chats reales. Los avisos del motor que conviene vigilar están en [Operación](operations.md), en «Avisos de
  pagos».
