# Contrato De Configuración De Negocios (BusinessConfig v1)

`BusinessConfig v1` es la única estructura con la que se describe un negocio para el motor de ventas:
qué vende, a qué precio, cómo cobra, cómo debe hablar y vender el asistente y qué puede hacer. Todos
los negocios usan el mismo contrato versionado; cada uno tiene su propio documento con sus datos.

- Referencia campo por campo (audiencia, estado en el motor, origen) y matriz de la configuración
  antigua: [business-config-traceability.md](business-config-traceability.md) (generada).
- Diagnóstico de los nueve negocios: `project/config/contracts/v1/migration-report.md` (generado).

## Estado De Esta Fase

| | Estado |
|---|---|
| Contrato (modelos, validaciones, diagnóstico, compilador, importador, catálogo) | **Terminado** |
| Esquema JSON, tipos TypeScript, matriz y referencia de campos | **Terminados**, generados desde el modelo canónico |
| Nueve documentos de negocio | **Terminados**: válidos, sin pérdida, sin datos de pago |
| Pruebas del contrato y de su integración con el motor actual | **Pasan** |
| Integración con el motor de los campos `pendiente` | **No iniciada** (requiere cambios en el motor, no autorizados) |
| Activación del contrato en algún negocio | **No realizada**: todos siguen con sus YAML |
| Retiro de los YAML | **No realizado** ni autorizado |
| Pantallas del panel para los campos nuevos | **No iniciadas** (fuera de alcance) |

## Fuente Canónica Y Archivos Generados

| Elemento | Ruta | Origen |
|---|---|---|
| Modelos del contrato (**fuente canónica**) | `project/app/domain/business_config/contract.py` | a mano |
| Políticas del motor y límites del contrato | `project/app/domain/business_config/engine_policy.py` | a mano |
| Diagnóstico (incoherencias que no bloquean) | `project/app/domain/business_config/diagnostics.py` | a mano |
| Compilador al formato que lee el motor | `project/app/domain/business_config/compiler.py` | a mano |
| Importador de los YAML | `project/app/infrastructure/config/legacy_yaml_importer.py` | a mano |
| Catálogo de campos antiguos | `project/app/infrastructure/config/legacy_field_catalog.py` | a mano |
| JSON Schema publicado | `project/config/contracts/v1/business-config.schema.json` | generado |
| Tipos TypeScript del panel | `apps/admin-web/src/contracts/businessConfig.v1.ts` | generado |
| Matriz y referencia de campos | `docs/business-config-traceability.md` | generada |
| Documento de cada negocio + informe | `project/config/tenants/<slug>/business-config.json`, `migration-report.md` | generados desde sus YAML |
| Ejemplo sin datos reales | `project/config/contracts/v1/business-config.example.json` | a mano |

Después de cambiar el contrato, en este orden (cada script acepta `--check`, que no escribe y falla si
algo está desactualizado; las pruebas comprueban los cuatro):

```
python scripts/export_business_config_schema.py      # JSON Schema
python scripts/generate_business_config_types.py     # tipos TypeScript del panel
python scripts/migrate_tenants_to_contract.py        # documentos de los nueve negocios + informe
python scripts/generate_traceability_matrix.py       # matriz y referencia de campos
```

## Estructura

Un único documento por negocio, con secciones comunes a todos los modelos comerciales. Solo
`tenant_slug`, cuatro textos de `identity` (`name`, `industry`, `description`, `value_proposition`),
`offer`, `capabilities` (cierre y datos) y `messages.welcome` son obligatorios; todo lo demás se omite
si no aplica, sin rellenarlo con datos inventados.

| Sección | Contenido |
|---|---|
| `identity` | nombre, marca, sector, descripción, propuesta de valor, posicionamiento, diferenciadores, ubicación y cobertura, modalidades, cliente ideal, credibilidad, horarios |
| `offer` | `plans` (planes o servicios) o `catalog` (categorías y productos); disponibilidad por elemento |
| `terms` | condiciones, impuestos incluidos, promociones con vigencia, financiación, políticas (garantía, devoluciones, cancelación); encuadre del precio y retorno (avanzado) |
| `payments` | perfiles de pago: link y transferencias como referencias a secretos; indicaciones |
| `sales` | básica: motivos de compra, problemas e impactos, beneficios, argumentos, preguntas, recomendaciones, instrucciones; avanzada: ángulos, objeciones, cierre, calificación, atención, solución, mezcla de ofertas |
| `capabilities` | canales, acciones, métodos de cierre, datos a pedir y aviso de tratamiento, cuándo pasar a una persona, restricciones y promesas prohibidas |
| `messages` | bienvenida, pago reportado y confirmado, posventa, pedir datos, seguimiento, pasar a una persona |
| `response_style` | tono, voz, formalidad, emojis, indicaciones; largo de respuesta y ajuste avanzado |
| `knowledge` | preguntas frecuentes con su respuesta oficial |
| `fulfillment` | domicilio, envío, recogida y agenda |
| `inventory` | variantes (atributos, existencias, precio propio si difiere) de los productos del catálogo |
| `engine` | ventanas de conversación y modo del motor; si falta, se deriva de la oferta (operador) |
| `compatibility` | datos antiguos sin lugar en el contrato (sistema, ver abajo) |

### Modelos comerciales

| Necesidad | Cómo se representa |
|---|---|
| Servicios o planes | `offer.model = plans`; cada plan con precios por moneda |
| Productos por categoría | `offer.model = catalog`; categorías y productos con precio por moneda |
| Varias monedas | una entrada de precio por moneda ISO (sin repetir) |
| Pago único, mensual, anual, primer pago, instalación | `price`, `monthly`, `annual`, `first_payment`, `implementation` en cada precio de plan |
| Variantes (talla, color, porciones) | `inventory.items[].variants[]` con `attributes`, `stock` y `prices` opcional |
| Elemento que se deja de vender sin borrarlo | `available: false` |
| Entrega, envío, recogida, citas | `fulfillment` con solo los modos que aplican |

Las diferencias entre tipos de negocio son datos (secciones y campos opcionales), no contratos ni
excepciones aparte: los nueve negocios (planes SaaS, clínica, agencia, escuela, restaurante, tiendas)
usan el mismo contrato.

## Marcas De Cada Campo

Cada campo del esquema lleva (o hereda de su sección) dos marcas, generadas en la referencia de campos
y en los comentarios de los tipos TypeScript:

- `x-audience` (quién lo configura): `cliente` (el negocio, en lenguaje comercial), `avanzado`
  (estrategia comercial detallada, opcional), `operador` (ajustes internos del motor: `engine`,
  etapas de `sales.conversation_flow`) o `sistema` (`schema_version`, `tenant_slug`, `compatibility`).
- `x-engine` (si el motor actual lo usa): `conectado` solo con una prueba en
  `tests/test_business_config_engine_integration.py` que demuestra que cambiarlo cambia el prompt, la
  respuesta o la acción del motor (`CONNECTED_EVIDENCE`; una prueba exige que la lista coincida con las
  marcas); `pendiente` si está representado y conservado pero el motor actual no lo usa;
  `conservado` para `compatibility`.

Con esto la matriz distingue cuatro situaciones que no son equivalentes:

- **Representado en el contrato:** el campo existe con tipo y validaciones (191 campos hoja).
- **Conservado en los datos:** el valor antiguo está en el documento del negocio (1211 campos de los
  nueve negocios, comprobado campo por campo) y vuelve intacto al compilar.
- **Configurable en la interfaz:** columna Interfaz (`pantalla`, `modelo` o `no`).
- **Ejecutado por el motor:** `x-engine = conectado` (58 campos hoja).

Conectados hoy: sector, propuesta de valor, tipo de oferta, planes (id, nombre, precios por moneda,
incluye, no incluye, perfil de pago, disponibilidad), categorías del catálogo y categoría y
disponibilidad de cada producto (deciden qué categorías se ofrecen), condiciones, encuadre del precio y retorno en ventas, pagos (link y transferencias: el motor
entrega los datos al elegir el método), motivos de compra, impactos de los dos primeros problemas,
casos de uso (respaldo), canales, acciones, métodos de cierre, datos a pedir, mensajes de bienvenida
y de pago, largo de respuesta, ventanas de conversación y modo de catálogo.

Pendientes (todo lo demás), entre ellos: nombre, marca y descripción del negocio, diferenciadores,
ubicación, modalidades, horarios, tono y estilo, productos y precios del catálogo, descripciones de
planes y productos, promociones, políticas, impuestos, financiación, preguntas frecuentes,
recomendaciones, instrucciones, preguntas de diagnóstico, beneficios, argumentos, estrategia avanzada,
mensajes de posventa y seguimiento, entrega, inventario y precio por variante.

## Decisiones De Diseño

1. **Se mejora la v1 existente sin romperla.** El panel ya produce documentos v1 y hay nueve documentos
   migrados: todos los cambios son compatibles (campos opcionales nuevos y validaciones que los nueve
   documentos cumplen). Unificar planes y catálogo en una sola lista de ofertas o mover `engine` fuera
   del documento serían cambios incompatibles: quedan para una v2 (ver Pendientes).
2. **El compilador solo produce lo que el motor actual lee.** Todo campo con ruta en los YAML vuelve a
   esa ruta con su forma original; lo que solo existe en el contrato no se compila. Resultado
   comprobado: para los nueve negocios, la compilación es idéntica a sus YAML y el motor produce los
   mismos prompts y respuestas con el contrato que con los YAML. Las claves `config.profile`,
   `config.knowledge` y `features` de productos ya no se generan: ningún lector del motor actual las
   consume (las usaba el bloque de perfil que se retiró del motor).
3. **Validación frente a diagnóstico.** El contrato rechaza lo que ningún negocio puede querer
   (referencias inexistentes, valores imposibles, combinaciones contradictorias). Lo que es una decisión
   del negocio se reporta sin bloquear (`diagnostics.py`, ver abajo).
4. **Estado en el motor como dato del esquema, no como texto.** Las descripciones solo explican el
   campo; `x-engine` y `x-audience` son la única fuente del estado, y la matriz y las pruebas se derivan
   de ellas.
5. **Campos nuevos con propósito concreto:** cobro anual y precio por variante (modelos comerciales que
   faltaban); políticas de garantía, devoluciones y cancelación e impuestos incluidos (preguntas
   habituales que el asistente debe responder con la versión oficial); aviso de tratamiento de datos
   (se piden datos personales en los nueve negocios); cuándo pasar a una persona y promesas prohibidas
   (límites del asistente). Todos `pendiente`: el motor actual no los usa.

### Campos duplicados, derivados, obsoletos o técnicos

| Campo | Tipo | Tratamiento |
|---|---|---|
| `sales.buying_motivation`, `motivation_drivers`, `angles` | mismo concepto en tres lugares | Se conservan (formas distintas en los YAML); validación: motivos y ángulos solo pueden referirse a motivos definidos en `motivation_drivers` |
| `sales.closing.required_data` y `capabilities.data_collection.fields` | solapados (inglés/español) | Se conservan; diagnóstico `dato_de_cierre_no_solicitado` si el cierre pide un dato que no se recoge |
| `closing_methods.data_collection` y `data_collection.enabled` | dependientes | Validación: cerrar pidiendo datos exige recogida de datos activa |
| `engine.features.catalog_mode`, `business_model` | derivables de `offer.model` | Audiencia `operador`; si falta `engine`, se derivan; diagnóstico `modo_catalogo_contradice_oferta` (ecommerce) |
| `engine.features.pricing_enabled` | obsoleto en la práctica | `pendiente`: el motor solo lo consulta sin precios ni pagos, que el contrato exige |
| `sales.conversation_flow.steps` | identificadores internos del motor | Audiencia `operador` |
| `response_style.max_words` | ajuste fino de `length` | Audiencia `avanzado`; rango validado contra `length` |
| `response_style.tone` y `voice` | cercanos | Se conservan con significados distintos (tono de las respuestas / personalidad de marca) |
| `terms.roi_break_even_sales` y `roi_break_even_bookings` | mismo concepto, distinta unidad | Se conservan; solo el de ventas está conectado |
| `sales.offer_mix` | texto libre, no referencias | Documentado como texto libre: no se valida contra los ids de la oferta |
| `engine.conversation` con 0 | el motor trata 0 como "sin valor" | Validación: mínimo 1 |
| `business.brand_name`, `business.city`, `business.type`, `config.capabilities.channels`, `config.features.multi_*`, `config.flags`, plantillas de cierre y progresión | duplicados, derivados o internos | En `compatibility` con justificación por campo (matriz) |

## Validaciones Y Diagnóstico

**Validaciones** (el documento se rechaza):

- Tipos, valores cerrados y campos desconocidos rechazados en todo el documento; `schema_version` fijo
  en `1.0`; `compatibility` solo con las cinco secciones antiguas.
- Textos obligatorios no vacíos; listas de frases de hasta 10 elementos de hasta 300 caracteres; tono y
  voz hasta 160; políticas y aviso de datos hasta 800; hasta 30 preguntas frecuentes (pregunta ≤ 200,
  respuesta ≤ 800); hasta 10 promociones.
- Oferta: planes o catálogo según `offer.model`, al menos un elemento disponible, ids únicos, monedas ISO
  sin repetir, cada precio con algún importe, productos con categorías existentes.
- Pagos: perfiles referenciados existentes, transferencias activas con métodos, cada método con sus
  datos obligatorios; datos sensibles solo como `SecretRef`.
- Referencias: recomendaciones hacia planes, productos o categorías existentes; solución y ángulos solo
  hacia problemas y ángulos existentes; motivos y ángulos hacia motivos definidos; inventario solo de
  productos del catálogo, sku únicos y precios de variante en monedas de su producto.
- Coherencia: al menos un método de cierre y una acción; datos a pedir si se activa la recolección;
  cierre pidiendo datos solo con recolección activa; `human_handoff_when` solo con cierre con una
  persona; costo "gratis" en 0; horarios que abren antes de cerrar; ventanas de conversación ≥ 1.

**Diagnóstico** (el documento es válido; el negocio decide): cierre por link sin link, perfil de pago
sin uso, modo de catálogo que contradice la oferta, modalidad sin entrega o entrega sin modalidad, dato
de cierre que no se pide, recomendación hacia algo no disponible, promoción vencida, sin canales de
atención, datos personales sin aviso de tratamiento, agenda sin horarios. El informe de migración lista
los hallazgos de los nueve negocios; no se corrigen automáticamente porque cambiarían su configuración.

## Largo De Las Respuestas

| `length` | Opción del panel | Límite | Ajuste avanzado `max_words` permitido |
|---|---|---|---|
| `short` (por defecto) | Cortas | 60 palabras | 20–60 |
| `medium` | Equilibradas | 75 palabras | 61–75 |
| `long` | Detalladas | 100 palabras | 76 o más (sin tope) |

El motor aplica el límite efectivo en el prompt y al recortar la respuesta, en todos los canales. Sin
configuración usa su respaldo de 80 palabras (ningún negocio está en ese caso).

## Datos De Pago

El contrato no guarda links, números de cuenta ni referencias: usa `{"secret_ref": "<origen>:<clave>"}`
(`legacy_yaml:` para los negocios migrados; `secret_store:` para datos guardados aparte). Ningún
documento del contrato contiene esos valores (comprobado en los nueve negocios y en la migración).

**Limitación del motor actual (pendiente):** el prompt de la IA y el registro `conversation_trace`
contienen hoy los datos de pago, con YAML y con contrato. Sacarlos de ahí exige cambiar el motor;
`payment_data.redact_payment_values` es la redacción preparada para esa integración.

## Compatibilidad

`compatibility` conserva, con su ruta original, lo que no forma parte del contrato (139 campos de los
nueve negocios). No contiene configuración que el cliente deba editar (lo comprueba una prueba):

| Datos | Motivo |
|---|---|
| `business.brand_name`, `business.city`, `business.type`, `config.capabilities.channels` | Duplicados de otros campos o estructura antigua |
| `config.features.multi_currency`, `config.features.multi_plan` | Derivables de la oferta y contradictorios en varios negocios |
| `config.flags.*`, `sales.closing.next_step.action`, `sales.progression_rules.forbid` | Parámetros internos sin consumidor |
| `sales.closing.behavior.*`, `sales.progression_rules.required_flow` | Plantillas idénticas en los nueve negocios: políticas del motor |
| `config.initial_message.recency` (demo) | Ubicación antigua de las ventanas de conversación |
| `sales.offer.recommendation_rules` (asesor_ai_prod, demo) | Apuntan a planes inexistentes: requiere decisión del negocio |

Lo que tenga lugar en el contrato sale de `compatibility` (la matriz documenta cada sustitución); nada
se elimina de ella mientras existan los YAML; el compilador la reinyecta sin sobrescribir datos del
contrato y un conflicto invalida el documento en lugar de perder datos.

## Conexión Con El Motor

`load_tenant_runtime_yaml` elige la fuente por negocio con `BUSINESS_CONFIG_CONTRACT_TENANTS` (vacío:
todos con YAML, que es el estado actual; lista de slugs; `*`: todos). Si el documento no existe o no es
válido, se registra `business_config_contract_invalid` y el negocio sigue con sus YAML.

Comprobado en los nueve negocios con el motor actual: con el contrato como fuente, el runtime es
idéntico al de los YAML y una conversación de cuatro turnos produce exactamente los mismos prompts y
respuestas. Activar el contrato hoy no cambia el comportamiento de la IA.

La persistencia en base de datos de una fase anterior (`business_config_repository.py`,
`payment_secret_store.py`, `business_config_tables.py`, `project/db/migrations/0001_business_config_store.sql`,
`BUSINESS_CONFIG_STORE=database`) no forma parte de esta fase: no se ha modificado ni ejecutado contra
ninguna base real.

## Correspondencia Con El Panel

El panel (`apps/admin-web`, no modificado en esta fase) traduce su modelo al contrato con
`contractAdapter.ts`. Una prueba de Vitest guarda el documento que produce
(`src/test/fixtures/sampleContractDocument.json`) y `test_panel_document_is_valid_against_the_contract`
lo valida con el contrato canónico y lo compila. Los campos nuevos de esta fase son opcionales: el
panel sigue compilando con los tipos regenerados.

| Panel | Contrato |
|---|---|
| `business.name`, `brandName`, `businessType`, `description`, `valueProposition` | `identity.name`, `brand_name`, `industry`, `description`, `value_proposition` |
| `business.differentiators`, `location`, `serviceModes` | `identity.differentiators`, `location`, `service_modes` |
| `business.salesMode` + `offerings[]` | `offer.model` + `offer.plans[]` u `offer.catalog` |
| `payments.paymentLink`, `transferMethods` | `payments[0]` con `secret_store:` (valores aparte) |
| `payments.conditions`, `promotions` | `terms.conditions`, `terms.promotions` |
| `closing.*` | `capabilities.closing_methods`, `data_collection`, `actions_primary/support` |
| `behavior.tone`, `responseLength`, `maxWords` | `response_style.tone`, `length`, `max_words` |
| `behavior.primaryMotivation/secondaryMotivation`, `customerProblems` | `sales.buying_motivation`, `customer_problems` |
| `behavior.benefits`, `sellingPoints`, `discoveryQuestions`, `recommendationRules`, `salesInstructions` | `sales.benefits`, `arguments`, `discovery.questions`, `recommendation_rules`, `instructions` |
| `behavior.faqs` | `knowledge.faqs` |
| `messages.*` | `messages.welcome`, `payment_reported`, `payment_confirmed`; `capabilities.service_channels` |

Dependencias del panel (fuera de alcance, sin cambios): varios avisos y textos del panel suponen la
integración del perfil comercial que el motor actual no tiene (p. ej. que el asistente usa la
descripción del negocio o de cada oferta, el tono, las promociones o las recomendaciones). El límite
de la descripción del negocio que el panel muestra viene de `PROMPT_WORD_LIMITS.description`, ahora 20
palabras (el recorte real del motor, que solo la usa si falta el sector). Los campos nuevos de esta fase
no tienen pantalla.

## Hallazgos En Los Nueve Negocios

Diagnóstico automático: ver `migration-report.md`. Además, datos dudosos que la migración conserva tal
cual (cambiarlos es decisión del negocio):

- **asesor_ai_prod:** `business_channels` vacío mientras la lista antigua `channels` tiene whatsapp,
  instagram y web; tres reglas de cierre son validaciones del texto de la respuesta, no instrucciones de
  venta; recomendaciones hacia `plan_pro`, que no existe; `multi_plan` es `true` con un solo plan.
- **demo:** recomendaciones hacia `plan_pro` y `plan_basico`, pero sus planes son `pro` y `basico`.
- **agencia_viajes:** el retorno está en reservas, que el motor no lee; `multi_currency` es `true` con una
  sola moneda.
- **clinic, saas:** `multi_plan` es `true` con un solo plan.
- **ecommerce:** oferta por planes con `catalog_mode = true`.
- **tienda_ropa:** modalidades presencial y envío, pero domicilio y recogida disponibles.
- **agencia_viajes, escuela_conduccion, restaurant, tienda_ropa:** cierre por link de pago sin link.
- **Todos:** piden datos personales sin aviso de tratamiento; comparten los mismos datos de
  transferencia (comparados por hash), lo que sugiere datos de ejemplo.

## Pruebas

| Archivo | Qué prueba | Estado |
|---|---|---|
| `tests/test_business_config_contract.py` | Modelo, esquema y tipos generados, marcas, conservación de los nueve negocios, compilación, validaciones, diagnóstico, panel | pasan |
| `tests/test_business_config_traceability.py` | Cada campo antiguo en su destino; catálogo coherente con las marcas; evidencias existentes; matriz al día | pasan |
| `tests/test_payment_data_protection.py` | Detección y redacción de datos de pago | pasan |
| `tests/test_business_config_engine_integration.py` | Contrato con el motor actual: equivalencia exacta con los YAML, fuente opcional y respaldo, evidencia de cada campo conectado | pasan |
| `tests/test_business_config_engine_pending.py` (`-m engine_pending`) | Comportamiento que exige cambios futuros en el motor | **xfail estricto**: se ejecutan siempre y fallan (63 "xfailed"); si una pasa, la suite falla hasta convertirla en prueba normal. Solo cuenta como fallo esperado la excepción con la que hoy falla cada prueba (`AssertionError`; `KeyError` y `AttributeError` en dos pruebas documentadas): cualquier otro error, incluido un fixture roto, es un fallo real. Detalle: `pytest -m engine_pending --runxfail` |

Los informes de fallo de cualquier prueba ocultan los datos de pago de los YAML (`tests/conftest.py`), para que no
lleguen a la consola ni a los logs de CI.

## Integración Pendiente Con El Motor

Requieren cambios en el motor (no autorizados en esta fase). Sus pruebas están en
`test_business_config_engine_pending.py`, sin cambios en sus aserciones:

1. **Perfil comercial en el prompt:** nombre o marca, descripción, diferenciadores, ubicación,
   modalidades, beneficios, argumentos, preguntas, recomendaciones, instrucciones, promociones vigentes y
   detalle de la oferta; tono en la línea de estilo. Exige que el motor lea un bloque de perfil y que el
   compilador lo emita (clave a acordar con esa integración; `config.profile` en la versión retirada).
2. **Preguntas frecuentes en el prompt** (misma situación: motor + clave de compilación).
3. **Productos y precios del catálogo en el prompt:** el prompt actual de catálogo no los lista.
4. **Datos de pago fuera del prompt y del registro de la conversación.**
5. **Presupuesto del prompt** en conversación activa con el perfil incluido.
6. Resto de campos `pendiente` (políticas, impuestos, horarios, entrega, estrategia avanzada, mensajes
   de seguimiento, precio anual y por variante...): sin pruebas pendientes aún; cada uno necesitará la
   suya al conectarse.

## Pendientes Fuera Del Contrato

1. Decisiones del negocio sobre el diagnóstico y los hallazgos.
2. Pantallas del panel para los campos nuevos y revisión de sus avisos (ver Correspondencia).
3. Activar el contrato por negocio (`BUSINESS_CONFIG_CONTRACT_TENANTS`): hoy no cambia respuestas.
4. Retirar los YAML y vaciar `compatibility` solo cuando ningún negocio dependa de ellos.
5. Contrato v2 (cambio incompatible): una sola lista de ofertas tipadas (producto, servicio, plan,
   reserva), `engine` fuera del documento del negocio y un único lugar para motivos y cierre.
6. Persistencia en base de datos: fuera de alcance.
