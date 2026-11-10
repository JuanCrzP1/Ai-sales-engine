# Contrato De Configuración De Negocios (BusinessConfig v1)

`BusinessConfig v1` es la estructura común con la que se describe un negocio: qué vende, a qué precio, cómo
cobra, cómo debe hablar y vender el asistente y qué puede hacer. Todos los negocios usan el mismo contrato
versionado; cada uno tiene su propio documento con sus datos. Es la fuente de configuración comercial de
los negocios activados (ver [Conexión Con El Motor](#conexión-con-el-motor)); sin activarlos, el motor sigue con sus YAML.

El contrato consolida las funcionalidades que ya existían en los YAML: las representa con tipos y
validaciones y conserva sus opciones y valores. Cuando es la fuente de un negocio, el motor usa además lo que solo
existe en el contrato: el perfil comercial, el tono y las preguntas frecuentes (ver
[Lo Que El Motor Usa Del Contrato](#lo-que-el-motor-usa-del-contrato)).

- Correspondencia de cada funcionalidad comercial con su campo original, referencia campo por campo y
  matriz de la configuración antigua: [business-config-traceability.md](business-config-traceability.md)
  (generada).
- Diagnóstico de los nueve negocios: `project/config/contracts/v1/migration-report.md` (generado).

## Estado De Esta Fase

| | Estado |
|---|---|
| Contrato (modelos, validaciones, diagnóstico, compilador, importador, catálogo) | **Terminado** |
| Esquema JSON, tipos TypeScript, matriz y referencia de campos | **Terminados**, generados desde el modelo canónico |
| Nueve documentos comerciales y sus ajustes técnicos | **Terminados**: válidos, sin pérdida, sin datos de pago |
| Pruebas del contrato y de su integración con el motor actual | **Pasan** |
| Integración con el motor | **Terminada** (Fase 3): los 184 campos que el panel deja configurar llegan al motor, cada uno con su prueba. Fuera, a propósito: lo que es solo del equipo (`solo panel`) y lo que enviará la plataforma ante un evento (`programado`) |
| Persistencia local (SQLite) | **Terminada** y conectada al panel por la API local |
| API local y panel de administración | **Terminados** (Fase 2): funcionan solo en este equipo; ver [Panel De Administración](#panel-de-administración) |
| Funcionamiento del almacén sin YAML | **Terminado y comprobado** en un árbol sin YAML ni motor (ver [Independencia De Los YAML](#independencia-de-los-yaml)) |
| Motor comercial | Lee **solo** lo publicado en el panel (ver [Conexión Con El Motor](#conexión-con-el-motor)). No necesita carpeta YAML |
| Retiro de los YAML | El motor ya no los lee (Fase 1 del plan, 2026-11-10). Quedan como origen de la importación hasta la Fase 6, que los borra |

## Fuente Canónica Y Archivos Generados

| Elemento | Ruta | Origen |
|---|---|---|
| Modelos del contrato (**fuente canónica**), por secciones | `project/app/domain/business_config/contract/`, con sus piezas comunes en `primitives.py` | a mano |
| Errores, registros y validación | `project/app/domain/business_config/{errors,records,validation}.py` | a mano |
| Casos de uso y puertos de almacenamiento | `project/app/business_config_application/{service,ports}.py` | a mano |
| Repositorio, tablas, datos de pago, clave y conexión | `project/app/infrastructure/business_config/{repository,tables,tenancy,payment_secret_store,secrets_key,database}.py` | a mano |
| API local del panel | `project/app/admin_api/{main,routes,schemas,errors}.py` | a mano |
| Migración inicial desde los YAML | `project/app/infrastructure/config/legacy_store_migration.py` | a mano |
| Lectura del motor (solo lo publicado, sin escribir ni crear nada) | `project/app/infrastructure/business_config/runtime_access.py` | a mano |
| Ajustes técnicos (fuera del contrato comercial) | `project/app/domain/business_config/engine_settings.py` | a mano |
| Políticas del motor y límites del contrato | `project/app/domain/business_config/engine_policy.py` | a mano |
| Diagnóstico (incoherencias que no bloquean) | `project/app/domain/business_config/diagnostics.py` | a mano |
| Compilador al formato que lee el motor | `project/app/domain/business_config/compiler.py` | a mano |
| Importador de los YAML | `project/app/infrastructure/config/legacy_yaml_importer.py` | a mano |
| Catálogo de campos antiguos | `project/app/infrastructure/config/legacy_field_catalog.py` | a mano |
| JSON Schema publicado | `project/config/contracts/v1/business-config.schema.json` | generado |
| Tipos TypeScript del panel | `apps/admin-web/src/contracts/businessConfig.v1.ts` | generado |
| Matriz y referencia de campos | `docs/business-config-traceability.md` | generada |
| Documento comercial y ajustes técnicos de cada negocio + informe | `project/config/tenants/<slug>/business-config.json`, `engine-settings.json`, `migration-report.md` | generados desde sus YAML |
| Ejemplo sin datos reales | `project/config/contracts/v1/business-config.example.json` | a mano |

Después de cambiar el contrato, en este orden (cada script acepta `--check`, que no escribe y falla si
algo está desactualizado; las pruebas comprueban los cuatro):

```
python scripts/export_business_config_schema.py      # JSON Schema
python scripts/generate_business_config_types.py     # tipos TypeScript del panel
python scripts/migrate_tenants_to_contract.py        # documentos y ajustes de los nueve negocios + informe
python scripts/generate_traceability_matrix.py       # matriz y referencia de campos
```

## Arquitectura

Las dependencias van hacia adentro y no hay ciclos. Lo comprueba `tests/test_business_config_architecture.py`; el panel tiene
su propia comprobación en `apps/admin-web/src/test/architecture.test.ts`.

| Capa | Paquete | Responsabilidad | Depende de |
|---|---|---|---|
| Dominio y contrato | `project/app/domain/business_config/` | Modelos, validación, reglas de los datos de pago, compilador, diagnóstico y errores | Solo Pydantic |
| Aplicación | `project/app/business_config_application/` | Casos de uso (`service.py`) y lo que necesitan de la persistencia (`ports.py`) | Dominio |
| Persistencia | `project/app/infrastructure/business_config/` | SQLAlchemy, transacciones, versionado, cifrado y aislamiento por negocio; `runtime_access.py` es la única puerta del motor | Aplicación y dominio |
| API | `project/app/admin_api/` | Rutas, peticiones y respuestas, errores HTTP y acceso solo local | Aplicación y dominio |
| Panel | `apps/admin-web/` | Formularios, estado de interfaz y consumo de la API, con los tipos generados del contrato | La API |

`scripts/run_admin_api.py` arma las piezas: crea la conexión, construye el servicio y se lo entrega a la API, que no conoce la
base de datos. La capa de aplicación no vive en `app.application` porque importar ese paquete carga el motor comercial.

Hay una sola excepción a las capas, explícita en esa prueba y temporal: la ruta `POST /api/businesses/import` usa la migración
desde los YAML, que se retira con ellos en la Fase 4.

**Multi-tenant.** Un único contrato para todos los negocios: las diferencias se expresan con datos y capacidades, nunca con
código por tipo de negocio. Toda operación recibe el identificador del negocio y la persistencia filtra por su id
(`tenancy.py`): las versiones, los datos de pago y los ajustes técnicos no se pueden alcanzar desde otro negocio, aunque se
conozca su número de versión o su referencia. La base lo refuerza con claves foráneas en cascada, una versión publicada como
máximo por negocio y números de versión únicos por negocio.

**Transacciones.** Una versión y sus datos de pago se guardan juntos, y el conflicto con otro guardado se decide dentro de esa
transacción. Publicar y revertir comprueban y cambian el estado en una sola transacción: si algo falla, lo publicado no cambia.

**SQLite es un detalle de la persistencia.** Ni el dominio, ni la aplicación, ni la API dependen de él. Pasar a PostgreSQL es
cambiar la URL de conexión y aplicar la migración SQL.

## Estructura

Un único documento comercial por negocio, con secciones comunes a todos los modelos comerciales. Solo
`tenant_slug`, cuatro textos de `identity` (`name`, `industry`, `description`, `value_proposition`),
`offer`, `capabilities` (cierre y datos) y `messages.welcome` son obligatorios; todo lo demás se omite
si no aplica, sin rellenarlo con datos inventados.

| Sección | Contenido |
|---|---|
| `identity` | nombre, marca, sector, descripción, propuesta de valor, posicionamiento, diferenciadores, ubicación y cobertura, modalidades, cliente ideal, credibilidad, horarios |
| `offer` | `plans` (planes o servicios) o `catalog` (categorías y productos); disponibilidad por elemento |
| `terms` | condiciones, promociones con vigencia, financiación, políticas (garantía, devoluciones, cancelación); encuadre del precio y retorno (avanzado) |
| `payments` | perfiles de pago: link y transferencias como referencias a secretos |
| `sales` | básica: motivos de compra, problemas e impactos, beneficios, argumentos, preguntas, recomendaciones, instrucciones; avanzada: ángulos y soluciones (dentro de cada motivo y problema), flujo de conversación, objeciones, cierre, calificación, atención, mezcla de ofertas |
| `capabilities` | canales, acciones, métodos de cierre, datos a pedir y restricciones |
| `messages` | saludo (sus dos modalidades), pago reportado y confirmado, posventa, pedir datos, seguimiento, pasar a una persona |
| `response_style` | tono, voz, formalidad, emojis, indicaciones; largo de respuesta y ajuste avanzado |
| `knowledge` | preguntas frecuentes con su respuesta oficial |
| `fulfillment` | domicilio, envío, recogida y agenda |
| `inventory` | variantes (atributos, existencias, precio propio si difiere) de los productos del catálogo |
| `features` | interruptores comerciales (precios, catálogo, varias monedas, varios planes) y tipo de negocio; si faltan, se derivan de la oferta |

Lo técnico no está en este documento: ver [Ajustes Técnicos](#ajustes-técnicos).

### Modelos comerciales

| Necesidad | Cómo se representa |
|---|---|
| Servicios o planes | `offer.model = plans`; cada plan con precios por moneda (excluye `catalog`) |
| Productos por categoría | `offer.model = catalog`; categorías y productos con precio por moneda (excluye `plans`) |
| Varias monedas | una entrada de precio por moneda ISO (sin repetir) |
| Pago único, mensual, anual, primer pago, instalación | `price`, `monthly`, `annual`, `first_payment`, `implementation` en cada precio de plan |
| Variantes (talla, color, porciones) | `inventory.items[].variants[]` con `attributes`, `stock` y `prices` opcional |
| Elemento que se deja de vender sin borrarlo | `available: false` |
| Entrega, envío, recogida, citas | `fulfillment` con solo los modos que aplican |

Las diferencias entre tipos de negocio son datos (secciones y campos opcionales), no contratos ni
excepciones aparte: los nueve negocios (planes SaaS, clínica, agencia, escuela, restaurante, tiendas)
usan el mismo contrato. Esta versión no admite negocios mixtos; `offer.model` es el punto donde una
versión futura añadiría otro modelo de oferta.

## Funcionalidades Comerciales

La tabla completa, con campo original, comportamiento, destino, tipo, opciones y valores de cada
negocio, está en [business-config-traceability.md](business-config-traceability.md#funcionalidades-comerciales-conservadas).

- **Dos modalidades de saludo** (`messages.welcome.enabled`, de `config.initial_message.enabled`):
  `true` envía el texto fijo ante un saludo sin más en una conversación nueva, sin IA; `false` no lo
  envía y responde la IA. El texto se conserva aunque esté desactivado. Un saludo con una intención siempre
  lo responde la IA. El motor también admite `initial_message.mode`, que ningún YAML usa: no se representa.
- **Extensión de los mensajes** (`response_style.length` y `max_words`): ver
  [Largo De Las Respuestas](#largo-de-las-respuestas).
- **Interruptores:** `features.*`, `capabilities.closing_methods.*`, `capabilities.data_collection.enabled`,
  `sales.support.explain_first` y `sell_after`, `sales.qualification.detect_offer_fit`,
  `sales.conversation_flow.no_skip_steps` y `guided_process`, y los de entrega, financiación e inventario.
  Conservan su nombre y su significado, y el motor los usa todos (ver la prueba de cada uno en
  `CONNECTED_EVIDENCE`).

## Marcas De Cada Campo

Cada campo del esquema lleva (o hereda de su sección) dos marcas, generadas en la referencia de campos
y en los comentarios de los tipos TypeScript:

- `x-audience` (quién lo configura): `cliente` (el negocio, en lenguaje comercial), `avanzado`
  (estrategia comercial detallada, opcional) o `sistema` (`schema_version`, `tenant_slug`).
- `x-engine` (si el motor actual lo usa): `conectado` solo con una prueba en
  `tests/test_business_config_engine_integration.py` que demuestra que cambiarlo cambia el prompt, la
  respuesta o la acción del motor (`CONNECTED_EVIDENCE`; una prueba exige que la lista coincida con las
  marcas); `programado` si lo enviará la plataforma cuando exista el evento que lo dispara (pago confirmado por el
  equipo, seguimiento a quien no respondió); `solo panel` si es solo para el equipo y nunca va a la IA (la etiqueta de
  una cuenta, el código de una variante); `pendiente` si está representado y conservado pero el motor no lo usa (hoy,
  ninguno).

Con esto la matriz distingue cuatro situaciones que no son equivalentes:

- **Representado en el contrato:** el campo existe con tipo y validaciones (184 campos hoja).
- **Conservado en los datos:** los 1211 campos de los nueve negocios vuelven intactos al compilar (comprobado
  campo por campo): 1166 desde el documento comercial, los datos de pago y los ajustes técnicos, y 45 desde la
  definición común del cierre.
- **Configurable en la interfaz:** columna Interfaz (`pantalla`, `modelo` o `no`).
- **Ejecutado por el motor:** `x-engine = conectado` (184 campos hoja; 2 `programado`, 2 `solo panel`, 0
  `pendiente`). Las ventanas de conversación también las usa el motor, pero son ajustes técnicos: no cuentan aquí.

Conectados hoy: sector, propuesta de valor, tipo de oferta, planes (id, nombre, precios por moneda,
incluye, no incluye, perfil de pago, disponibilidad), categorías del catálogo y categoría y
disponibilidad de cada producto (deciden qué categorías se ofrecen), condiciones, encuadre del precio y retorno en ventas, pagos (link y transferencias: el motor
entrega los datos al elegir el método), motivos de compra, impactos de los dos primeros problemas,
casos de uso (respaldo), canales, acciones, métodos de cierre, datos a pedir, mensajes de bienvenida
y de pago, largo de respuesta, modo de catálogo y tipo de negocio. Con el contrato como fuente, también: nombre,
marca y descripción del negocio, diferenciadores, ubicación, modalidades, beneficios, argumentos, preguntas de
diagnóstico, recomendaciones, instrucciones, promociones, tono, preguntas frecuentes, descripción de cada plan, y
nombre, descripción, precios y características de cada producto.

Desde la Fase 3, también: posicionamiento, pruebas de confianza, cliente ideal y horario; personalidad, trato (tú o
usted), emojis e indicaciones de estilo; para quién es cada plan, cobro anual, opciones y existencias de cada producto
(nunca cuántas unidades quedan) y precio propio de una variante; aclaración del precio, ofertas principales, mejoras y
complementos (solo si están en la oferta); pasos y requisitos para comprar, domicilio, envío, recogida y agenda;
financiación; datos del cierre (unidos a los que se piden); lo que el negocio no hace; políticas; los mensajes para pedir
datos, pasar a una persona y después de una compra; y toda la estrategia avanzada (problemas, casos, motivos, objeciones,
orden de la conversación, atención, qué averiguar, cómo presentar las opciones y cierre). Los interruptores
`pricing_enabled`, `multi_currency` y `multi_plan` deciden si se dan precios, en cuántas monedas y si se recomienda un solo
plan.

## Decisiones De Diseño

1. **Consolidación, no reconstrucción.** Las funcionalidades son las de los YAML: tipadas, con sus
   opciones y valores. Se unifican solo las estructuras que describen lo mismo con la misma clave (ver la
   tabla de abajo). Planes y catálogo siguen siendo dos modelos de oferta porque así funcionan en los
   YAML y en el motor.
2. **Comercial y técnico, separados.** El documento comercial no contiene parámetros internos ni datos
   sin tipar; lo técnico está en `EngineSettings` y se adjunta al cargar el documento. Esta consolidación
   sigue en `1.0`: ningún documento está publicado ni activo y el panel no enviaba las secciones retiradas.
3. **El compilador reproduce lo que el motor actual recibe.** Todo campo con ruta en los YAML vuelve a
   esa ruta con su forma original; lo que solo existe en el contrato no se compila. Resultado
   comprobado: para los nueve negocios, la compilación es idéntica a sus YAML y el motor produce los mismos
   prompts y respuestas con el contrato que con los YAML. Las claves `config.profile`,
   `config.knowledge` y `features` de productos ya no se generan: ningún lector del motor actual las
   consume (las usaba el bloque de perfil que se retiró del motor).
4. **Validación frente a diagnóstico.** El contrato rechaza lo que ningún negocio puede querer
   (referencias inexistentes, valores imposibles, combinaciones contradictorias). Lo que es una decisión
   del negocio se reporta sin bloquear (`diagnostics.py`, ver abajo).
5. **Estado en el motor como dato del esquema, no como texto.** Las descripciones solo explican el
   campo; `x-engine` y `x-audience` son la única fuente del estado, y la matriz y las pruebas se derivan
   de ellas.
6. **Campos propios del contrato, con finalidad comercial:** horarios; formalidad, emojis e instrucciones de
   estilo; instrucciones comerciales; mensajes de posventa, datos, seguimiento y transferencia; cobro anual,
   primer pago y pago único; precio por variante; disponibilidad; características de producto; promociones,
   preguntas frecuentes y políticas. Se conservan aunque no vengan de los YAML; su responsabilidad, tipo y
   estado en el motor están en la matriz (`Campos propios del contrato`).
7. **Campos ajenos a los YAML retirados por decisión del dueño.** Se retiraron `terms.prices_include_taxes`,
   `capabilities.data_collection.consent_notice`, `capabilities.human_handoff_when`,
   `capabilities.restrictions.forbidden_claims`, `payments[].instructions` y
   `sales.qualification.criteria`. Las obligaciones legales de la plataforma, como el aviso de tratamiento
   de datos, no se configuran en BusinessConfig; este contrato no las sustituye ni las modifica.
8. **Definición común del cierre.** `sales.closing.behavior.*.goal` y `sales.closing.next_step.action` tienen
   los mismos cinco valores en los nueve negocios, y cambiarlos no altera prompts ni respuestas: no son decisiones
   de cada negocio. Por eso no están en el contrato ni en los ajustes técnicos, sino una sola vez en
   `COMMON_CLOSING_POLICY` (`engine_policy.py`). El compilador los añade a `sales.closing` en la posición que
   tienen en los YAML, así que el motor recibe lo mismo. Un YAML con otros valores detiene la importación: esa
   diferencia sería una configuración propia del negocio.

### Campos duplicados, derivados, obsoletos o técnicos

| Campo | Tipo | Tratamiento |
|---|---|---|
| `business.value_drivers` y `sales.angles` | mismos motivos con la misma clave | **Unificados** en `sales.motivations[]` (descripción, señales y ángulo). Validación: si el negocio explica sus motivos, todo motivo que use debe tener descripción |
| `sales.solution.mapping` y `sales.pain.clusters` | mismos problemas con la misma clave | **Unificados** en `sales.customer_problems[].solutions` |
| `sales.conversation_flow` y `sales.progression_rules` | reglas de cómo avanza la conversación | **Unificados** en `sales.conversation_flow`. `steps` (pasos ideales) y `required_flow` (secuencia mínima) se conservan: significan y valen distinto |
| `business.city` y `business.location.city` | mismo dato, mismo valor en los nueve negocios | **Unificado** en `identity.location.city`; la compilación lo devuelve a las dos rutas |
| `sales.closing.required_data` y `capabilities.data_collection.fields` | solapados (inglés/español) | Se conservan; diagnóstico `dato_de_cierre_no_solicitado` si el cierre pide un dato que no se recoge. El prompt los une en una sola lista en español, sin repetir |
| `closing_methods.data_collection` y `data_collection.enabled` | dependientes | Validación: cerrar pidiendo datos exige recogida de datos activa |
| `features.catalog_mode`, `business_model` | relacionados con `offer.model` | Interruptores comerciales con sus valores; si faltan, se derivan; diagnóstico `modo_catalogo_contradice_oferta` (ecommerce) |
| `features.multi_currency`, `multi_plan` | permiten, no obligan | Interruptores comerciales con sus valores; el diagnóstico solo señala `false` con varias monedas o planes |
| `features.pricing_enabled` | si el asistente da precios | Interruptor comercial, conectado: con `false` no da valores y dice que el equipo los confirma |
| `response_style.max_words` | ajuste fino de `length` | Audiencia `avanzado`; rango validado contra `length` |
| `response_style.tone` y `voice` | cercanos | Se conservan: valen distinto en los nueve negocios (tono de las respuestas / personalidad de marca) |
| `sales.pain_points` y `customer_problems` | cercanos | Se conservan: contenido distinto (frases del cliente / problemas con impacto) |
| `terms.roi_break_even_sales` y `roi_break_even_bookings` | mismo concepto, distinta unidad | Se conservan; el de reservas se usa si no hay el de ventas (argumento de valor de los negocios de planes) |
| `sales.offer_mix` | texto libre, no referencias | Documentado como texto libre: no se valida contra los ids de la oferta |
| `conversation` con 0 (ajustes técnicos) | el motor trata 0 como "sin valor" | Validación: mínimo 1 |

## Validaciones Y Diagnóstico

**Validaciones** (el documento se rechaza):

- Tipos, valores cerrados y campos desconocidos rechazados en todo el documento; `schema_version` fijo
  en `1.0`. Interruptores solo booleanos; opciones cerradas en extensión, tipo de negocio, tipo de cierre y
  encuadre del precio. Los datos a pedir y los pasos de la conversación son listas abiertas: los YAML no las
  limitan y cada negocio puede tener los suyos. El documento comercial rechaza `engine` y `compatibility`.
- Textos obligatorios no vacíos; listas de frases de hasta 10 elementos de hasta 300 caracteres; tono y
  voz hasta 160; políticas y mensajes hasta 800; hasta 30 preguntas frecuentes (pregunta ≤ 200,
  respuesta ≤ 800); hasta 10 promociones.
- Oferta: planes o catálogo según `offer.model`, al menos un elemento disponible, ids únicos, monedas ISO
  sin repetir, cada precio con algún importe, productos con categorías existentes.
- Pagos: perfiles referenciados existentes, transferencias activas con métodos, cada método con sus
  datos obligatorios; datos sensibles solo como `SecretRef`.
- Referencias: problemas solo hacia ángulos existentes; motivos sin repetir y con descripción o ángulo;
  inventario solo de productos del catálogo, sku únicos y precios de variante en monedas de su producto.
- Coherencia: al menos un método de cierre y una acción; datos a pedir si se activa la recolección;
  cierre pidiendo datos solo con recolección activa; costo "gratis" en 0; horarios que abren antes de
  cerrar y sin días repetidos; promociones y preguntas frecuentes sin repetir.
- Ajustes técnicos: ventanas de conversación ≥ 1, banderas conocidas, `legacy` solo con las cinco secciones
  antiguas y del mismo negocio. Un conflicto entre `legacy` y el contrato invalida la compilación.
- Importación: los YAML de un negocio deben coincidir con la definición común del cierre; si no, se detiene.

**Diagnóstico** (el documento es válido; el negocio decide): cierre por link sin link, perfil de pago
sin uso, modo de catálogo, varias monedas o varios planes que contradicen la oferta, modalidad sin entrega
o entrega sin modalidad, dato de cierre que no se pide, recomendación hacia algo que no existe o no está
disponible (las reglas de asesor_ai_prod y demo se conservan tal cual), promoción vencida, sin canales de
atención, agenda sin horarios. El informe de migración lista
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
(`secret_store:` para el almacén cifrado, el único origen que admite la persistencia local; `legacy_yaml:`
solo en los `business-config.json` de las carpetas de negocio, para la fuente opcional del motor). Ningún
documento del contrato contiene esos valores (comprobado en los nueve negocios y en la migración). Los
errores de validación tampoco repiten el valor recibido.

Son datos del negocio y no se mezclan con las credenciales de canales (`tenant_secrets`), que pertenecen a
las integraciones.

### Consultarlos sin exponerlos

Quien administra necesita saber qué métodos tiene sin ver sus valores. Cada respuesta de la API con el documento incluye
`payment_fields`: por cada referencia, su estado y una versión enmascarada que calcula el servidor
(`payment_data.mask_payment_value`). Lo descriptivo (tipo, banco, tipo de cuenta, etiqueta y estado) ya está en el documento.

| Dato | Qué se muestra | Ejemplo |
|---|---|---|
| Enlace | El servidor, sin ruta, parámetros ni credenciales | `https://pagos.example.com/••••` |
| Celular o cuenta | Hasta los últimos 4 caracteres | `••••4567` |
| Llave o referencia | Hasta los últimos 3 caracteres | `••••ave` |
| Menos de 6 caracteres | Nada | `••••` |

En celulares, cuentas y llaves nunca revela la mitad del valor ni su longitud. De un enlace solo deja ver el servidor, que identifica
al proveedor; si el enlace no tiene nada más, oculta también parte del servidor, para que el valor nunca salga completo.

| `status` | Significa | `masked` |
|---|---|---|
| `configured` | Guardado y legible en este negocio | La versión enmascarada |
| `missing` | No existe en este negocio, también si la referencia es de otro | `null` |
| `unreadable` | No se puede descifrar con la clave actual | `null` |

| Operación | Qué pasa con el dato cifrado |
|---|---|
| Editar banco, tipo de cuenta o etiqueta (`label`) | No cambia |
| Guardar sin un valor nuevo | No cambia. En el panel, un campo de reemplazo vacío no se envía; por la API, un valor vacío se rechaza con 422 |
| Reemplazar | Se cifra con una referencia nueva; las versiones anteriores conservan el suyo |
| Desactivar (`transfer_methods[].enabled` o `link_enabled` en `false`) | Se conserva. No se compila ni se ofrece, y no hace falta poder leerlo para publicar |
| Eliminar | Sale de la versión nueva; las anteriores lo conservan y restaurarlas lo trae de vuelta |

`label`, `enabled` y `link_enabled` son opcionales: sin indicar, un método está activo y los documentos que no los usan no cambian
ni compilan distinto. `label` no llega al motor.

### Datos de pago en `/simulate`

`POST /api/v1/simulate` está apagado por defecto y exige el token de un administrador, que hoy nadie puede obtener porque
la autenticación definitiva queda para la fase de nube (ver `docs/operations.md`). No devuelve configuración interna ni usa
la memoria de los clientes:

| Dato | ¿Se devuelve? |
|---|---|
| Datos de pago: link, número, cuenta y referencia | No; ni el modelo los recibe, y `reply` muestra `[dato de pago]` |
| Estrategia comercial, `pricing`, `business` y `ai_metadata` | No |
| Memoria de conversaciones de clientes | No; la simulación usa una memoria propia en RAM |
| Credenciales, tokens y prompt del sistema | No |
| `reply`, `ai_used` y las etiquetas `source`, `intent`, `conversation_state` y `tenant_slug` | Sí |

`reply` es texto del modelo, igual que el que recibe un cliente: puede mencionar precios. Ningún otro campo los lleva.

**Limitación del motor actual (pendiente):** en los canales reales, el prompt de la IA y el registro
`conversation_trace` contienen hoy los datos de pago, con YAML y con contrato. Sacarlos de ahí exige cambiar el motor;
`payment_data.redact_payment_values` es la redacción preparada para esa integración.

## Ajustes Técnicos

`engine-settings.json` (o la tabla `business_engine_settings`) guarda lo que el motor necesita y no es una
decisión comercial (55 campos de los nueve negocios). El negocio no los edita y el panel no los recibe. Es
opcional: sin él, el motor usa sus valores por defecto.

| Datos | Motivo |
|---|---|
| `conversation` (`config.conversation`) | Cuándo el motor considera activa o nueva una conversación |
| `flags` (`config.flags`) | Banderas internas, sin lector en el motor |
| `legacy`: `config.capabilities.channels`, `config.initial_message.recency`, `business.type` | Estructuras antiguas o repetidas |

Nada comercial queda aquí (lo comprueba una prueba). Los ajustes técnicos no se versionan con el documento
comercial: en base de datos hay uno vigente por negocio, y se adjunta a la versión publicada al leerla.
`legacy` se retira cuando se retiren los YAML.

### YAML que no son de un negocio

Estos archivos son globales: valen igual para todos y no se representan en BusinessConfig.

| Archivo | Contenido | Por qué queda fuera |
|---|---|---|
| `system/settings.yaml`, `system/bot_config.yaml` | Aplicación, proveedor y modelos de IA, interruptores globales, límites técnicos (`max_message_length`, `history_limit`) y política de preguntas frecuentes | Parámetros técnicos del motor |
| `system/secrets.yaml` | Credenciales de plataforma y canales | Credenciales |
| `system/conversation_stage.yaml` | Objetivos y estilo del asistente por etapa de la conversación | Política global del motor; ningún negocio la cambia |
| `channels/channels.yaml` | Canales activos | Conectores |
| `assets/media.yaml` | Imágenes reutilizables | Global y sin lector (`load_media` no tiene quien la llame) |

## Conexión Con El Motor

`load_tenant_runtime_yaml` (`application/runtime/tenant_runtime_loader.py`) tiene una sola fuente: **la versión publicada de cada
negocio**, en la misma base que escribe el panel (`BUSINESS_CONFIG_DATABASE_URL` o, si no está, el SQLite local) y con la misma clave
(`BUSINESS_CONFIG_SECRETS_KEY`, `secrets.local.env` o el archivo de la carpeta del usuario, en ese orden). La lee en cada mensaje,
solo a través de `runtime_access.py`, que nunca crea la base, las tablas ni la clave. Lo único que escribe es el consumo de IA de cada
respuesta. Una prueba de arquitectura impide que otra parte del motor entre al almacén por otro camino.

Ningún negocio necesita carpeta en `project/config/tenants`: uno creado desde el panel responde igual que los importados.

Si el negocio no existe, no tiene versión publicada, lo publicado no es válido, falta la clave o la base no responde, el motor **no
responde con datos viejos**: registra la alerta `business_config_unavailable` (solo el tipo de error) y el cliente recibe un mensaje
neutro de la plataforma. Cuando lo que falla es la IA (sin clave, sin saldo, el proveedor caído), el cliente recibe el mensaje que el
negocio escribió en Mensajes → «Si el asistente no puede responder» (`messages.fallback`), o el neutro si no lo escribió.

`tests/test_business_config_engine_integration.py` y `tests/test_business_config_local_persistence.py` lo comprueban sin sustituir
ninguna pieza: publicar en el panel cambia lo que recibe el motor, volver atrás lo devuelve, un negocio sin carpeta responde y, sin
almacén, el motor no crea ningún archivo.

Comprobado en los nueve negocios: con el contrato como fuente, el runtime es el de los YAML más `config.profile`, y una
conversación de cuatro turnos produce los mismos prompts y respuestas salvo el perfil comercial (su bloque y el tono).
Activar el contrato en un negocio solo le añade eso.

### Lo Que El Motor Usa Del Contrato

El compilador deja lo que solo existe en el contrato en claves que los YAML no tienen (`commercial_profile.py`), y el motor
lo usa solo cuando las encuentra. Un negocio que sigue con sus YAML no cambia.

| Clave | En el prompt |
|---|---|
| `config.profile` | Bloque «PERFIL COMERCIAL DEL NEGOCIO» (`prompting/sections/profile.py`). En la presentación: nombre o marca, descripción, diferenciadores, ubicación, modalidades, beneficios, argumentos, preguntas de diagnóstico, recomendaciones y detalle de la oferta. En cada turno: instrucciones y promociones vigentes. El tono reemplaza a «natural y claro» en la línea ESTILO |
| `config.knowledge` | Bloque de preguntas frecuentes (`prompting/sections/knowledge.py`): todas si caben en `FAQ_PROMPT_MAX_CHARS` (1500 caracteres); si no, las que más palabras comparten con el mensaje del cliente, en el orden del negocio |
| Catálogo grande | El detalle de la oferta (perfil) y la lista de precios van enteros si caben en `OFFER_DETAILS_PROMPT_MAX_CHARS` (3000) y `PRICE_LIST_PROMPT_MAX_CHARS` (1500); si no, lo más relacionado con el mensaje del cliente y el anterior (`prompting/relevance.py`), más cuántas opciones quedan por fuera. Con 300 productos el prompt mide lo mismo que con 20 |
| `pricing.catalog.items[].features` | Características de cada producto, en el detalle de la oferta |

- Las recomendaciones apuntan por id a un plan, producto o categoría y llegan con su nombre. Las que apuntan a algo que no
  se ofrece se descartan: la IA nunca recomienda algo inexistente, y el diagnóstico se lo señala al negocio.
- Los textos del negocio llegan completos, sin recortes: el contrato limita su largo en caracteres (`MAX_INDUSTRY_CHARS` 80,
  `MAX_DESCRIPTION_CHARS` 500, `MAX_VALUE_PROPOSITION_CHARS` 300, `MAX_OFFER_DESCRIPTION_CHARS` 300) y el panel no deja escribir
  más, con un contador. Las categorías (hasta 20) y los problemas del cliente (hasta 10) también se usan todos.
- Las promociones vencidas se descartan al armar cada prompt, sin volver a publicar.
- Con cualquiera de las dos fuentes, la línea «Precios» de un catálogo lista el precio de cada producto.
- Los datos de pago nunca llegan a la IA, ni desde la configuración ni desde el historial, ni al registro
  `conversation_trace`: el motor se los entrega al cliente cuando elige el método (`ejecutar_pago`). Si la IA repitiera el
  marcador `[dato de pago]`, el cliente recibe el dato real si eligió un método o, si no, la respuesta sin esa frase.
- Para comprobar una migración, `comparable_with_yaml` quita las claves exclusivas del contrato antes de comparar con los
  YAML (lo usan el panel al importar, `scripts/migrate_tenants_to_contract.py` y las pruebas).

## Persistencia Local

`BusinessConfigService` ofrece crear y listar negocios, consultar lo publicado, recuperar el borrador en
curso, guardar cambios, publicar, revertir, consultar el historial, recuperar versiones anteriores y
compilar. Solo conoce los puertos de `ports.py`; `BusinessConfigRepository` y `PaymentSecretStore` los
implementan con SQLAlchemy.

| Tema | Comportamiento |
|---|---|
| Base | `BUSINESS_CONFIG_DATABASE_URL`; vacío: `project/data/business_config.sqlite3` (ignorado por git y por Docker). Es independiente de la base del motor (`DATABASE_URL`) |
| PostgreSQL | Cambiar la URL y aplicar `project/db/migrations/0001_business_config_store.sql`. **Sin probar** contra un PostgreSQL real |
| Versiones | Cada guardado crea una versión inmutable y validada; los números son por negocio |
| Guardar | La versión y sus datos de pago se escriben en una sola transacción. Si se indica la versión de partida y ya hay otra más reciente, no se guarda |
| Borrador en curso | El más reciente posterior a lo último publicado |
| Recuperar una versión | Crea un borrador nuevo con su contenido; no publica nada |
| Revertir | Vuelve a publicar la versión publicada anterior, en una sola transacción; si falla, lo publicado no cambia |
| Publicar | Compila la versión con sus datos de pago, en una sola transacción; si falla, lo publicado no cambia |
| Ajustes técnicos | Uno vigente por negocio, fuera de las versiones comerciales |

**Datos de pago:** se cifran con Fernet (`BUSINESS_CONFIG_SECRETS_KEY`, sin valor por defecto) y el documento
solo guarda referencias. Cada valor nuevo recibe una referencia propia, de modo que editar un borrador no
altera lo publicado y revertir devuelve también los datos de pago de esa versión. Antes de cifrar un valor nuevo se
comprueba su formato según su tipo (enlace, celular, cuenta o llave); el panel avisa con las mismas reglas mientras se
escribe, pero la autoridad es el servidor (`payment_data.py`). Se rechazan documentos que
contengan el valor de un dato de pago, ya sea uno nuevo o uno guardado antes, o que dependan de otro origen
(`legacy_yaml:`). Los negocios importados pasan sus datos de los YAML al almacén cifrado.

El panel usa este almacén a través de la API local: ver [Panel De Administración](#panel-de-administración).

### Procedimiento

1. **Comprobar la migración sin tocar ninguna base:** `pytest tests/test_business_config_nine_businesses.py
   tests/test_business_config_yaml_independence.py` importa los nueve negocios en bases temporales.
2. **Generar la clave** y guardarla fuera del repositorio. Sin ella los datos de pago no se pueden leer, y
   perderla obliga a volver a introducirlos:
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
3. **Definir `BUSINESS_CONFIG_SECRETS_KEY`** en el entorno de la sesión o del usuario (el script no lee `.env`).
4. **Crear la base:** `python scripts/init_local_business_config.py`. No necesita clave ni lee YAML, y no toca
   lo que la base ya contenga.
5. **Migración inicial, una sola vez:** `python scripts/init_local_business_config.py --import-tenants`.
   Comprueba la clave y que cada negocio reproduzca sus YAML antes de escribir nada. Repetirla no duplica ni
   sobrescribe: un negocio con versiones no se toca, y uno registrado sin versiones se completa.

### Independencia De Los YAML

Una vez importados, los negocios no vuelven a leer YAML. Lo comprueba
`tests/test_business_config_yaml_independence.py` en un proceso aparte, sobre una copia del código sin YAML,
sin motor, sin `.env` y sin carpetas de negocio, con un registro de los archivos abiertos: crear un negocio,
guardar, recuperar borradores, publicar, consultar el historial, revertir, recuperar versiones y compilar,
también al reabrir la base en otro proceso. Los nueve negocios compilan allí a la misma huella que sus YAML.

Lo único que sigue relacionado con los YAML:

| Elemento | Para qué | Hasta |
|---|---|---|
| `legacy_store_migration.py` y `init_local_business_config.py --import-tenants` | Migración inicial; solo con esa opción se carga, y lee únicamente los cinco YAML de cada negocio, sin motor ni `.env` | Fase 4 |
| `legacy_yaml_importer.py`, `payment_secrets.py`, `migrate_tenants_to_contract.py` y los `business-config.json` con `legacy_yaml:` | Fuente opcional del motor por contrato y documentos de referencia | Fase 4 |
| `tenant_runtime_loader.py` y `config_service.py` | El motor sigue leyendo sus YAML salvo en los negocios activados (ver [Conexión Con El Motor](#conexión-con-el-motor)) | Fase 4 |
| `legacy_field_catalog.py`, `generate_traceability_matrix.py` y las pruebas | Trazabilidad y comparación con la referencia original | Fase 4 |
| `legacy` en los ajustes técnicos | Copia en la base de tres estructuras antiguas; no lee los YAML | Fase 4 |

## Panel De Administración

El panel (`apps/admin-web`) edita directamente este contrato a través de la API local (`project/app/admin_api`), sobre el almacén
descrito en [Persistencia Local](#persistencia-local). No tiene un modelo propio: sus tipos se generan del contrato, los campos sin
pantalla propia se generan del esquema y lo demás se conserva al guardar. Cómo ejecutarlo: `apps/admin-web/README.md`. El documento
ficticio con el que se prueba (`src/test/fixtures/sampleContractDocument.json`) lo valida
`test_panel_document_is_valid_against_the_contract`.

**Lo publicado es lo que responde el asistente.** Publicar deja una versión oficial en el almacén, comprobada con el compilador, y
llega a los clientes en el siguiente mensaje (ver [Conexión Con El Motor](#conexión-con-el-motor)). El motor solo usa los campos
marcados `conectado`. El panel lo dice en la pantalla de publicación. Algunos avisos
suponen la integración del perfil comercial que el motor actual no tiene: ver [Integración Pendiente](#integración-pendiente-con-el-motor).

| Pantalla | Contrato |
|---|---|
| Mi negocio | `identity.*`, `offer.model` |
| Productos y servicios | `offer.plans[]` u `offer.catalog`, `inventory`, `fulfillment` |
| Pagos y cierre | `payments[]` (referencias `secret_store:`, valores aparte), `terms.*`, `capabilities.closing_methods`, `data_collection`, `actions_primary/support` |
| Cómo atiende | `response_style.*`, `sales.*`, `knowledge.faqs`, `features` |
| Mensajes y canales | `messages.*`, `capabilities.service_channels`, `product_channels`, `restrictions` |
| Revisión y publicación | Versiones, publicación y diagnóstico del almacén |

### API local

La arrancan `run_local.bat` y `run_local.sh`. Sin `BUSINESS_CONFIG_SECRETS_KEY`, usa la clave de `.ai-sales-engine/business_config_secrets.key`
en la carpeta del usuario, que crea la primera vez. Escucha solo en `127.0.0.1:8010` (`scripts/run_admin_api.py`, host fijo). Rechaza clientes, `Host` y `Origin` ajenos, no publica su
documentación y responde `Cache-Control: no-store`. **No tiene autenticación:** la autenticación y la autorización multiusuario deben
incorporarse antes de desplegarla en la nube.

| Método y ruta | Qué hace |
|---|---|
| `GET /api/health` | Comprueba que está en marcha |
| `GET /api/contract` | El esquema publicado del contrato |
| `GET /api/businesses` | Lista los negocios |
| `POST /api/businesses` | Registra un negocio (`slug`, `name`). 409 si ya existe |
| `POST /api/businesses/import` | Importa los YAML que falten; no los modifica y no toca lo ya guardado |
| `DELETE /api/businesses/{slug}?confirm={slug}` | Borra el negocio con sus versiones y datos de pago. Exige repetir el identificador. Solo en SQLite |
| `GET /api/businesses/{slug}/config` | El documento que se edita y `payment_fields`: los datos de pago solo enmascarados ([Consultarlos sin exponerlos](#consultarlos-sin-exponerlos)) |
| `PUT /api/businesses/{slug}/config` | Guarda una versión (`document`, `payment_values`, `base_version`). 409 si cambió desde `base_version`; 422 con los campos por corregir, incluido el formato de los datos de pago |
| `POST /api/businesses/{slug}/validate` | Valida sin guardar |
| `GET /api/businesses/{slug}/review` | Diagnóstico y si la versión se puede compilar. Nunca devuelve lo compilado |
| `GET /api/businesses/{slug}/versions` | Historial |
| `POST /api/businesses/{slug}/versions/{version}/restore` | Crea un borrador con esa versión; no publica |
| `POST /api/businesses/{slug}/publish` | Publica una versión; si no compila, lo publicado no cambia |
| `POST /api/businesses/{slug}/rollback` | Vuelve a publicar la versión publicada anterior |

Los errores son `{code, message, issues: [{path, message}]}` en español y nunca repiten el valor recibido. Códigos: `invalid`, `duplicate`,
`conflict`, `not_found`, `confirmation_required`, `forbidden`, `payment_key`, `unexpected`.

## Inteligencia Artificial Y Área De Pruebas

Cada negocio responde con **su propia clave de OpenRouter** y, si quiere, con su propio modelo. No es parte del contrato
comercial: vive en `business_ai_settings` (migración `0002`), con la clave cifrada como los datos de pago. La API solo devuelve si
está configurada y sus últimos caracteres. En todo el motor, la clave del negocio tiene prioridad sobre la general del `.env`, que
queda de respaldo mientras cada negocio no tenga la suya.

| Ruta | Para qué |
|---|---|
| `GET` y `PUT /api/businesses/{slug}/ai` | Ver y guardar el modelo y la clave |
| `POST /api/businesses/{slug}/ai/verify` | Comprobar la clave con OpenRouter (`GET /api/v1/key`, sin gastar créditos) |
| `POST /api/businesses/{slug}/playground` | Conversar con el asistente, con lo que se está editando o con lo publicado |
| `DELETE /api/businesses/{slug}/playground/{session_id}` | Empezar otra conversación |

El área de pruebas («Probar asistente» en el panel) ejecuta **el motor real** con la versión elegida y la clave del negocio, detrás
del puerto `AssistantRunner` (`app/business_config_application/ports.py`). El adaptador
(`app/application/assistant_lab/engine_runner.py`) se conecta al arrancar la API, así que las capas del panel siguen sin conocer el
motor. Cada conversación tiene su propia memoria en RAM, separada por negocio y sesión, que caduca sin uso: nunca toca la base ni
las conversaciones de los clientes reales.

Pendiente para la nube: en funciones sin estado, las conversaciones de prueba tendrán que guardarse en la base.

## Hallazgos En Los Nueve Negocios

Diagnóstico automático: ver `migration-report.md`. Además, datos dudosos que la migración conserva tal
cual (cambiarlos es decisión del negocio):

- **asesor_ai_prod:** `business_channels` vacío mientras la lista antigua `channels` tiene whatsapp,
  instagram y web; tres reglas de cierre son validaciones del texto de la respuesta, no instrucciones de
  venta; recomendaciones hacia `plan_pro`, que no existe.
- **demo:** recomendaciones hacia `plan_pro` y `plan_basico`, pero sus planes son `pro` y `basico`.
- **agencia_viajes:** el retorno está en reservas, que el motor no lee.
- **ecommerce:** oferta por planes con `catalog_mode = true`.
- **tienda_ropa:** modalidades presencial y envío, pero domicilio y recogida disponibles.
- **agencia_viajes, escuela_conduccion, restaurant, tienda_ropa:** cierre por link de pago sin link.
- **Todos:** comparten los mismos datos de transferencia (comparados por hash), lo que sugiere datos de
  ejemplo.

## Pruebas

| Archivo | Qué prueba | Estado |
|---|---|---|
| `tests/test_business_config_contract.py` | Modelo, esquema y tipos generados, marcas, conservación de los nueve negocios, compilación, validaciones, diagnóstico, panel | pasan |
| `tests/test_business_config_traceability.py` | Cada campo antiguo en su destino; funcionalidades comerciales con sus valores y opciones; nada técnico en el documento comercial; catálogo coherente con las marcas; evidencias existentes; matriz al día | pasan |
| `tests/test_payment_data_protection.py` | Detección y redacción de datos de pago; fuera del prompt y del registro con YAML y con el contrato; el cliente los recibe y nunca ve el marcador | pasan |
| `tests/test_business_config_repository.py` | Versiones, publicación, reversión, cifrado y runtime desde base de datos | pasan |
| `tests/test_business_config_closing_policy.py` | Definición común del cierre: los cinco valores en los nueve negocios, misma estructura que los YAML, fuera del contrato, divergencias rechazadas y motor sin cambios | pasan |
| `tests/test_business_config_local_persistence.py` | Persistencia local en archivo SQLite: creación, aislamiento, borradores, historial, reversión, protección de pagos y migración segura ante fallos | pasan |
| `tests/test_business_config_nine_businesses.py` | Los nueve negocios en una base temporal: cada campo de los YAML, compilación frente a la referencia, prompts iguales, aislamiento y repetición de la importación | pasan |
| `tests/test_business_config_yaml_independence.py` | El almacén funciona en un árbol sin YAML ni motor; procedimiento documentado; base fuera del control de versiones | pasan |
| `tests/test_business_config_engine_integration.py` | Contrato con el motor: equivalencia con los YAML más el perfil comercial; perfil, preguntas frecuentes y precios del catálogo; fuente opcional y respaldo; evidencia de cada campo conectado | pasan |
| `tests/test_commercial_profile_prompt.py` | Compilación del perfil y de las preguntas frecuentes; recortes, vigencia de las promociones, recomendaciones sin destino y selección de preguntas por espacio | pasan |
| `tests/test_admin_api.py` | API local: negocios, secciones comerciales, validaciones, conflictos, reinicio, aislamiento, datos de pago, acceso solo local, versiones e importación de los nueve negocios sin pérdida | pasan |
| `tests/test_business_config_architecture.py` | Capas, ausencia de ciclos y de dependencias del motor; el motor entra al almacén solo por `runtime_access.py`; rutas sin lógica; nada técnico en el contrato | pasan |
| `apps/admin-web`: `npm test` | Interfaz con un backend en memoria, reglas, operaciones y arquitectura (sin `localStorage`, sin recursos externos) | pasan |
| `apps/admin-web`: `npm run test:integration` | Interfaz real, API real, contrato y SQLite temporal, con reinicios reales de la API: el recorrido completo y los nueve negocios guardados desde el panel | pasan |

Los informes de fallo de cualquier prueba ocultan los datos de pago de los YAML (`tests/conftest.py`), para que no
lleguen a la consola ni a los logs de CI. `pytest.ini` usa una lista cerrada de archivos (`python_files`): una
prueba nueva que no se añada allí no entra en la suite ni en el CI.

`pytest` a secas no consume API ni usa las credenciales ni la base del `.env` local (`tests/conftest.py`): se
comporta como el CI y omite las pruebas contra el modelo real. Esas solo corren con `pytest -m integration`.

## Integración Con El Motor

Terminada en la Fase 3: todo lo que el panel deja configurar llega al motor, cada campo con su prueba (ver
[Marcas De Cada Campo](#marcas-de-cada-campo)). La primera parte fue: perfil comercial con su tono, preguntas frecuentes, productos y precios del catálogo, datos de
pago fuera de la IA y del registro, y el presupuesto del prompt en una conversación en curso (ver
[Lo Que El Motor Usa Del Contrato](#lo-que-el-motor-usa-del-contrato)). Sus 63 pruebas, antes `xfail` estricto, pasan como
pruebas normales en `test_business_config_engine_integration.py` y `test_payment_data_protection.py`, sin cambios en sus
aserciones.

La Fase 3 conectó el resto con 36 casos de prueba más (`PHASE_3_CASES`), una prueba del mensaje posventa y otra que
comprueba que lo que es solo del equipo o lo enviará la plataforma nunca llega a la IA. El marcador `engine_pending`
(xfail estricto) queda para un campo nuevo que se agregue al contrato antes de conectarse; hoy no lo usa ninguna prueba.

## Pendientes Fuera Del Contrato

1. Decisiones del negocio sobre el diagnóstico y los hallazgos.
2. ~~Activar el contrato~~: el motor ya no tiene otra fuente (Fase 1).
3. Borrar los YAML y `legacy` (Fase 6): el motor ya no los lee; solo los usa la importación.
4. Persistencia en PostgreSQL, rotación de la clave de cifrado y limpieza de datos de pago de versiones
   antiguas: fase de nube.
5. Autenticación definitiva, también para la API del panel: fase de nube. El sistema propio actual no se desarrollará ni se
   mantendrá, y `/auth/register` no está listo para producción (ver `docs/operations.md`).
