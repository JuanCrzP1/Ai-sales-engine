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

Está en [`experiments/quality_lab/standard.py`](../experiments/quality_lab/standard.py). Son 13 reglas.

**Ocho exactas.** Se comprueban con código, sin opinión, y dan siempre el mismo resultado para la misma conversación.

| Regla | Qué exige |
|---|---|
| El asesor habla | Cuando van los datos de pago, el asesor dice algo: el mensaje no es solo la plantilla. |
| Datos cuando los necesita | Le llegan cuando los pide o dice con qué medio paga. |
| Sin datos sin pedirlos | No le llega la cuenta cuando solo pregunta, saluda o habla de otra cosa. |
| No repite el bloque | Los datos que ya tiene no se repiten si no los pide otra vez. |
| Sin marcadores | Nunca ve un marcador entre corchetes en lugar de un dato. |
| Pago avisado al equipo | Si dice que ya pagó, el chat pasa al equipo; si no, no pasa. |
| No repite la respuesta | No le responde lo mismo dos veces seguidas. |
| Sin números de pago falsos | El asesor nunca escribe un número como dato de pago («Nequi: 315…»): el único es el que pone el sistema. |

**Cinco con juez.** Necesitan leer la conversación.

| Regla | Qué exige |
|---|---|
| Responde lo que preguntan | Si pregunta si puede pagar con un medio, le dice claramente si se puede. |
| No pide lo ya dado | No vuelve a pedir un dato que el cliente ya le dio. |
| No dice nada falso del pago | No dice que no puede enviar los datos, que no recibe un medio que sí tiene, ni que ya envió algo que no envió. |
| Explica cuando no entienden | Ante un «cómo así», le explica qué hacer. |
| Coherente con los datos | Cuando van los datos, no dice que los enviará después ni los condiciona. |

### Las conversaciones

Las arma `conversations_for` con la oferta y los medios de pago reales del negocio:

- **El chat de producción** (13 turnos): el chat real del 13 de noviembre. Incluye «Y puedo trasferir», «Y Nequi no», «Te pago por
  Nequi», «Pero se me borró el Nequi me lo envías de nuevo», «Cómo así», «Ya voy a pagar» y «ya te consigné».
- **Cinco cortas**, cada una con un cliente nuevo: pide el medio con un error de escritura («pásame el nekui»), pregunta a dónde
  consigna, pregunta cómo paga, pregunta si tienen un medio y pide los datos de otro medio.

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

- Corre el código del árbol de trabajo en una copia aislada, sin `.env`, con la red cerrada salvo OpenRouter.
- Usa la clave de OpenRouter del `.env`. Nunca la imprime.
- Con tres muestras de un negocio tarda unos cinco minutos y cuesta cerca de USD 0,05. El cálculo previo es conservador: muestra
  cuatro o cinco veces más.
- Termina con código 0 si pasa y 1 si no, para usarlo en un script.

### Qué deja

En `experiments/quality_lab/results/<identificador>/`:

- `report.md`: el veredicto, cada regla con cuántas conversaciones pasa, lo que no pasó con el turno y la respuesta, y todas las
  conversaciones.
- `data.json`: lo mismo, para procesarlo.
- `captures.json`: las conversaciones tal como salieron, con los prompts.

Ninguno lleva datos de pago: lo que entregó el motor aparece como `[dato entregado por el motor]`.

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

## Lo que la puerta no cubre

- Solo mira los momentos de pago. La oferta, los precios y las objeciones los mide
  [`run_quality_eval.py`](../experiments/quality_lab/run_quality_eval.py).
- El cliente sigue un guion: no reacciona a lo que le responde el asesor.
- No prueba los canales. Eso lo hacen los recorridos de WhatsApp ([`apps/wa-sim`](../apps/wa-sim/README.md)).
- No reemplaza mirar los chats reales. Los avisos del motor que conviene vigilar están en [Operación](operations.md), en «Avisos de
  pagos».
