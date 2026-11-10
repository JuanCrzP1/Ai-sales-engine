# Plan de la versión 1: auditoría y fases

Auditoría del sistema completo (motor, panel, nube) del 10 de noviembre de 2026 y el plan para terminar la versión 1. Cada
hallazgo dice dónde está y cómo se comprobó. Ninguna fase se da por terminada sin sus pruebas.

## 1. Dónde estamos

**Ya funciona, en la nube (Vercel + Neon):**

- Cuentas con Neon Auth. Cada usuario solo ve y modifica sus negocios (`business_members`).
- Panel SaaS: entrada directa al negocio, selector de negocios, Inicio con la actividad del día, Asistente IA por pestañas.
- Configuración del negocio con contrato versionado (`BusinessConfig`): borrador, publicar, volver atrás.
- Clave de OpenRouter por negocio, cifrada. La plataforma no tiene clave propia.
- Probar el asistente con la IA real.
- Bandeja de conversaciones con historial en la base, y avisos al equipo cuando el asistente pasa a una persona.
- Producción: `asesor_ai_prod`, a nombre de su dueño, con su configuración completa.

**Todavía no hay clientes reales escribiendo:** ningún canal (WhatsApp, Telegram, Instagram, web) está conectado en la nube.

**Avance (10 de noviembre de 2026):**

| Hallazgo | Estado | Cómo quedó |
|---|---|---|
| S1, S2 | Hecho | Ningún `print` en `project/app` (una prueba lo impide). Los registros de OpenRouter, del analizador y del orquestador ya no llevan mensajes, respuestas, cargas ni cuerpos: solo modelo, estado, tiempo y tipo de error. |
| S3 | Hecho | El webhook de WhatsApp solo acepta lo que firmó Meta (`X-Hub-Signature-256` con `META_APP_SECRET`). Sin secreto, rechaza todo. |
| S4 | Pendiente | Cambiar la contraseña en Neon (las dos ramas) y pegar las URL nuevas en Vercel y en el `.env`. |
| S5 | Hecho en «Probar» | Límites en la base (`rate_limits`, migración 0006), compartidos por todas las instancias: 20 mensajes por minuto por persona, 300 por hora por negocio y 10 comprobaciones de clave cada 10 minutos. Más allá, 429 con `Retry-After` y un mensaje en español. Queda el límite por IP en Vercel (Fase 7). |
| T1 | Hecho | Una sola llamada por mensaje (ver T1). |
| T2 | Hecho | El panel usa las cuatro intenciones del motor; una prueba compara ambos lados. |
| Modelo de IA | Hecho | El panel lista los modelos de OpenRouter que responden en JSON (consulta pública, guardada una hora), con buscador, recomendados y el costo aproximado de 1.000 respuestas. El servidor no guarda un modelo que no esté en la lista. |
| A1, A2, Q5 | Hecho (Fase 1) | El motor solo lee lo publicado; un negocio creado en el panel responde sin carpeta YAML. Si la base falla, mensaje neutro y alerta, nunca el YAML. El mensaje de respaldo se escribe en el panel. Sin negocio por defecto. |
| Q1, Q2 | Hecho (Fase 2) | Prompt por bloques (`prompting/`): instrucciones fijas en un archivo, un módulo por bloque, compositor con presupuesto por bloque. La identidad del negocio va en todos los mensajes. Un catálogo grande ya no infla el prompt: con 300 productos mide lo mismo que con 20. Verificado con el laboratorio (`exp_20261110_fase2*`). |
| Contenido del prompt | Hecho (v2) | Prompt por capas en una sola voz: plataforma (cómo vende, la verdad primero, dudas, pagos, formato), manual por tipo de negocio, el negocio completo en todos los mensajes, la conversación como mensajes reales y la versión del prompt en cada respuesta. Medido con la IA real en el laboratorio de calidad (`experiments/quality_lab`, `exp_20261110_calidad_prompt_v2`): puntaje 9,59 → 9,84, no inventa 1,72 → 1,92, pregunta trampa 9,06 → 10, gana 17 de 18 a ciegas, menos tokens y más rápido. Línea base A/A: 9,52 contra 9,52. Ajuste v2.1 confirmado en vivo (`exp_20261110_calidad_prompt_v2_1`): 9,44 → 9,70, dudas por precio 7,72 → 8,44, pregunta trampa 8,83 → 9,72. Un intento v2.2 empeoró y se descartó (`exp_20261110_calidad_v2_2_objeciones`). |
| Q3, Fase 3 | Hecho | Todo lo que el panel deja configurar llega al motor (prompt v3): 184 campos conectados, 0 pendientes. Solo quedan fuera, a propósito, lo que es del equipo (la etiqueta de una cuenta y el código de una variante) y lo que enviará la plataforma ante un evento (pago confirmado y seguimiento). Capas nuevas: cómo compra y recibe el cliente, políticas, el cliente y la estrategia de venta. Laboratorio de regresión (`exp_20261110_fase3_campos_conectados`): mismas respuestas, webhook y rutas; los prompts solo suman lo nuevo. Calidad con la IA real (`exp_20261110_calidad_fase3_ficha_completa`): 9,64 contra 9,62 por respuesta, 0 precios inventados y gana 15 de 18 a ciegas; en los negocios con estrategia avanzada (`exp_20261110_calidad_fase3_objeciones`): 9,58 → 9,81, dudas por precio 9,25 → 9,5 y gana 7 de 8. Hallazgo: varios negocios de ejemplo tienen la estrategia avanzada escrita como si vendieran el asistente a su sector (p. ej. la agencia responde una duda de precio con «perder reservas por falta de seguimiento cuesta dinero»): son datos de ejemplo por corregir, no un error del motor. |
| T3 | Hecho | Cada respuesta suma a `ai_usage` (migración 0007) por negocio, día y modelo, con el costo si OpenRouter lo informa. El panel lo muestra en «Inteligencia artificial». |

## 2. Cómo funcionaba antes y cómo funciona hoy

| | Antes (YAML) | Hoy (plataforma) |
|---|---|---|
| Configuración | 5 archivos por negocio (`business`, `sales`, `pricing`, `inventory`, `config`) y `bot_config.yaml`, editados a mano | Panel → contrato validado y versionado en Neon → compilado a las secciones que lee el motor |
| Negocios | Una carpeta por negocio | Filas en la base, con dueño |
| Clave de IA | Una general en el `.env` | Una por negocio, cifrada |
| Canal | Telegram por *polling*, un negocio por proceso (`TENANT_SLUG`) | Ninguno en la nube todavía |
| Pasar a una persona | `human_handoff: enabled: true` y un comentario, sin reglas | Igual, más el aviso al equipo y la conversación marcada |
| Conversaciones | Solo la memoria del motor | Memoria del motor + bandeja del panel (dos almacenes) |

`asesor_ai_prod` conserva todos sus datos de los YAML (164 campos). Una prueba compara lo que recibe el motor desde el panel con lo
que recibía de los YAML: es lo mismo, más las mejoras (preguntas frecuentes, promociones, perfil comercial, textos completos).

## 3. Hallazgos

Severidad: **crítico** (se arregla antes de cualquier cliente), **alto** (bloquea la versión 1), **medio** (la versión 1 queda
incompleta sin él).

### 3.1 Seguridad y privacidad

| # | Hallazgo | Dónde | Severidad |
|---|---|---|---|
| S1 | El token de acceso de WhatsApp se imprime en los registros (`TOKEN USADO`) | `connectors/whatsapp/meta/sender.py:174` | crítico |
| S2 | Los registros imprimen mensajes de clientes, teléfonos, respuestas y el token de verificación (`PAYLOAD`, `META RESPONSE`, `RESPUESTA IA`, `DESTINO`, `VERIFY TOKEN`) | `sender.py`, `api/controllers/whatsapp_webhook.py`, `connectors/telegram/` | crítico |
| S3 | El webhook de WhatsApp no comprueba la firma de Meta (`X-Hub-Signature-256`): cualquiera podría enviar mensajes falsos | `whatsapp_webhook.py` | crítico |
| S4 | La contraseña de la base de Neon quedó escrita en un chat | Neon, ramas `production` y `pruebas` | crítico |
| S5 | No hay límites de uso: cualquiera puede crear cuentas (registro abierto) y llamar la API sin tope; «Probar» gasta la clave del negocio | API del panel | alto |
| S6 | Sin verificación de correo ni recuperación de contraseña (requieren un proveedor de correo) | Neon Auth | alto |

### 3.2 Consumo de tokens

| # | Hallazgo | Dónde | Severidad |
|---|---|---|---|
| T1 | **Doble consumo.** Si el modelo no devuelve JSON válido o usa una intención fuera de las 4 aceptadas, el motor repite la llamada completa: el mensaje cuesta el doble. Medido: 1 llamada cuando la salida es válida, 2 cuando no. **Causa de fondo:** el prompt principal nunca pedía el JSON; solo lo pedía la repetición, así que casi todo mensaje costaba dos llamadas. **Corregido:** el formato va al final de la primera llamada (`services/ai/output_contract.py`), se pide `response_format: json_object` al proveedor y, si la salida no es perfecta, se usa el texto que escribió el modelo sin volver a llamarlo | `services/ai/ai_orchestrator.py`, `structured_output.py` | alto |
| T2 | Intenciones desalineadas: el motor acepta `pain`, `info`, `objection`, `buy`; el panel muestra `price`, `greeting`, `support`, que el motor nunca devuelve | `structured_output.py`, `PlaygroundPage.tsx` | medio |
| T3 | El consumo no se guarda por negocio (solo se registra en el log): no se puede mostrar al cliente, limitar ni cobrar | `prompting.py` (`tokens_usage`) | medio |

Tamaño medido del prompt de `asesor_ai_prod`: unos 1.000 a 1.300 tokens por mensaje, más la respuesta (hasta 400). Es razonable.
El problema es la repetición de T1, no el tamaño.

Encontrado al corregir T1: el motor reemplazaba `runtime.generate` en un objeto compartido para agregar el marco del canal. Con
dos mensajes a la vez, uno podía salir con el marco repetido y el cambio quedar pegado para los siguientes. Ahora el marco viaja
como parámetro (`route_response(preamble=...)`) y una prueba con dos mensajes simultáneos lo cubre.

### 3.3 Calidad del asistente y del prompt

| # | Hallazgo | Dónde | Severidad |
|---|---|---|---|
| Q1 | **Desde el segundo mensaje, «CONTEXTO DEL NEGOCIO» va vacío.** El perfil del negocio solo va en el primer mensaje: después la IA ya no sabe qué hace el negocio, solo precios y pagos | `prompting/business_profile.py` (`include_facts`), `prompt_builder.py` | alto |
| Q2 | El prompt se arma en un solo archivo de 973 líneas, con instrucciones escritas en el código y mezcladas con los datos | `prompting/builder/prompt_builder.py` | alto |
| Q3 | 100 de los 187 campos del contrato se guardan, pero el motor no los usa. Varios tienen pantalla en el panel y el cliente cree que funcionan: estilo (voz, formalidad, emojis), mensajes (seguimiento, pedir datos, postventa, al pasar a una persona), horarios, cliente ideal, posicionamiento, credibilidad, políticas (garantía, devoluciones, cancelaciones), aclaración del precio, financiación y la estrategia comercial avanzada (objeciones, motivos, cierre, flujo, casos de uso) | `docs/business-config-traceability.md` | alto |
| Q4 | El panel no avisa qué campos no se usan todavía | panel | alto |
| Q5 | El mensaje de emergencia (cuando la IA falla) es genérico y sale de un YAML | `pipeline/fallback.py` | medio |

### 3.4 Pasar a una persona

| # | Hallazgo | Severidad |
|---|---|---|
| H1 | No hay reglas: la IA decide sola cuándo pasar. Si alguien escribe «quiero un asesor», lo pasa de una vez, sin intentar resolver | alto |
| H2 | El traspaso se detecta buscando frases en la respuesta («te paso con…»), no como una decisión estructurada con su motivo | alto |
| H3 | No hay horario del equipo: fuera de horario promete algo que nadie cumple | alto |
| H4 | Mientras espera, la IA sigue respondiendo en ese chat | alto |
| H5 | El mensaje de traspaso que el negocio escribe en el panel no se usa | medio |
| H6 | Los avisos solo llegan al panel abierto: no hay correo | medio |

### 3.5 Arquitectura

| # | Hallazgo | Dónde | Severidad |
|---|---|---|---|
| A1 | El motor exige la carpeta YAML del negocio: **un negocio creado desde el panel no puede atender un canal** | `infrastructure/config/config_service.py` (`_default_client_id`) | alto |
| A2 | Si la base falla, el motor responde con el YAML viejo sin avisar | `runtime/tenant_runtime_loader.py` | alto |
| A3 | Dos almacenes de conversaciones: el del motor (`clients`, `conversation_messages`, `conversation_memory`) y la bandeja (`conversations`, `conversation_entries`) | persistencia | alto |
| A4 | Sistema anterior todavía en el código: modelos con ids enteros (`app/models`), la API de administración vieja (`/auth`, `/clients`, `/conversations`...), autenticación con `python-jose`, tablas `admin_users`, `tenant_secrets`, `tenant_settings`, `tenant_channels`, Telegram por *polling* y `asesor_ai_prod` como negocio por defecto | varios | medio |
| A5 | Módulos demasiado grandes: `prompt_builder.py` (973 líneas), `memory_repository.py` (818), `ai_execution.py` (741, con errores silenciados por `except Exception: pass`), `config_service.py` (667) | motor | medio |
| A6 | La memoria de «Probar» vive en el servidor: en Vercel a veces se pierde entre mensajes | `assistant_lab/engine_runner.py` | medio |

### 3.6 Operación del SaaS

| # | Hallazgo | Severidad |
|---|---|---|
| O1 | El plan Hobby de Vercel no permite uso comercial | alto |
| O2 | Sin monitoreo de errores ni alertas | alto |
| O3 | Copias de seguridad de Neon sin probar su restauración | alto |
| O4 | Sin términos de uso ni política de tratamiento de datos (Ley 1581 de 2012, Habeas Data) | alto |
| O5 | Sin correo transaccional (verificación, contraseña, avisos) | alto |

## 4. Cómo debe funcionar pasar a una persona

Principio: **el asistente resuelve primero; pasa a una persona solo cuando corresponde, y nunca deja al cliente esperando a nadie.**

**Configuración del negocio** (panel → Asistente IA → «Atención humana»):

- Activado sí o no.
- Cuándo pasar:
  - **El cliente lo pide.** Primero ofrece ayudar él mismo («Con gusto te ayudo yo, ¿qué necesitas?»). Si el cliente insiste o el
    tema no está en lo que sabe, pasa.
  - **Reclamo** o problema con un pedido o un pago: pasa directo.
  - **No sabe la respuesta** después de intentarlo (la información no está en la configuración).
  - **Venta especial**: por encima de un valor que el negocio define (opcional).
- Horario del equipo (días y horas). Fuera de horario, lo dice, toma los datos y avisa cuándo lo contactarán.
- Datos que pide antes de pasar (nombre, motivo), para que el equipo no empiece de cero.
- Mensaje de traspaso (ya existe en el contrato, hoy sin usar).
- Mientras espera: la IA no responde en ese chat, salvo para confirmar que ya lo atienden. Vuelve a responder cuando el equipo
  marca «Ya lo atendí» o si nadie atiende en el tiempo que el negocio elija.

**En el motor**, la decisión es estructurada: el modelo devuelve el traspaso y su motivo en la salida JSON (`handoff: {reason}`), y
el motor aplica la política del negocio (horario, intentos, pausa). Deja de buscar frases en el texto.

**Avisos**: campana del panel (hecho) y correo. Más adelante, WhatsApp al dueño.

**Medición**: cuántos chats pasan a una persona y por qué.

## 5. Cómo debe quedar el prompt

Sin archivos gigantes. El prompt se arma con **bloques pequeños**, cada uno en su propio módulo, con una sola responsabilidad, un
presupuesto de tokens y su prueba:

| Bloque | Va | Contenido |
|---|---|---|
| Identidad | Siempre (compacto) | Nombre, a qué se dedica, propuesta de valor |
| Estilo | Siempre | Tono, formalidad, emojis, largo de respuesta, instrucciones |
| Oferta | Siempre (nombres y precios); detalle por relevancia | Planes, productos, categorías |
| Pagos y cierre | Siempre | Medios disponibles (sin datos de pago), cómo cerrar |
| Políticas | Por relevancia | Garantía, devoluciones, cancelaciones, financiación |
| Conocimiento | Por relevancia | Preguntas frecuentes |
| Proceso de venta | Siempre (resumido) | Descubrimiento, objeciones, motivos, siguiente paso |
| Atención humana | Si está activada | Cuándo pasar y cómo |
| Estado de la conversación | Siempre | Memoria, último paso, pago en curso |
| Formato de salida | Siempre | Esquema JSON |

Cada campo del panel llega a un bloque o no se muestra en el panel: no quedan campos que no hacen nada.

## 6. Plan por fases

Tamaño: S (horas), M (1–2 días), L (3–5 días). El orden importa: cada fase deja el sistema funcionando.

### Fase 0: seguridad urgente (S)

- ~~Quitar del código todo `print` con tokens, mensajes o teléfonos; registros estructurados sin datos personales (S1, S2).~~ Hecho.
- ~~Comprobar la firma de Meta en el webhook de WhatsApp (S3).~~ Hecho.
- Cambiar la contraseña de la base en las dos ramas y actualizar Vercel y el `.env` (S4).
- ~~Límites de uso por usuario en la API, más estrictos en «Probar» (S5).~~ Hecho; el límite por IP pasa a la Fase 7 (Vercel Firewall).

**Terminada cuando:** ninguna prueba ni registro contiene tokens o mensajes de clientes; un webhook sin firma válida se rechaza.

### Fase 1: el motor sin YAML (M) — terminada el 10 de noviembre de 2026

- ~~El motor deja de exigir la carpeta del negocio: lo identifica por la base (A1).~~ Hecho.
- ~~Si la base falla, error claro y alerta: nunca el YAML viejo (A2).~~ Hecho: `business_config_unavailable` y mensaje neutro.
- ~~Mensaje de emergencia desde el panel (Q5).~~ Hecho: `messages.fallback`, en Mensajes y canales.
- ~~Quitar `asesor_ai_prod` como negocio por defecto.~~ Hecho.
- Los YAML quedan solo como origen de la importación; se borran en la Fase 6.

**Terminada cuando:** un negocio creado desde el panel responde en «Probar» y por la ruta de un canal, sin ninguna carpeta. Lo
comprueban `test_a_business_created_in_the_panel_answers_without_any_yaml_folder` (ruta de un canal) y
`test_a_business_created_in_the_panel_answers_in_the_test_area` («Probar»), que fallaba con el código anterior.

Cómo quedó:
- Una sola fuente: `load_tenant_runtime_yaml` lee la versión publicada (`published_sections`). Ya no existen
  `BUSINESS_CONFIG_STORE` ni `BUSINESS_CONFIG_CONTRACT_TENANTS`, ni el almacén en archivos (`business-config.json`) para el motor.
- Sin respaldos escondidos: el flujo de ventas, el saludo, el prompt, el mensaje de respaldo, el envío por WhatsApp y Telegram ya no
  leen YAML. Una prueba de arquitectura (`test_the_engine_never_reads_the_business_yaml`) impide volver a conectarlos.
- Si la IA falla, el cliente recibe el mensaje del negocio o uno neutro; antes recibía un texto fijo de los YAML globales que
  aparentaba ayudar («Te ayudo encantada…») y, si el negocio no se podía leer, «Error de configuración de tenant».
- Las pruebas usan la misma ruta que producción: un almacén con los nueve negocios importados y publicados. Tres archivos que
  calificaban a la IA sin modelo (solo medían el texto de respaldo) pasaron a integración (`pytest -m integration`).

### Fase 2: prompt modular y sin doble consumo (L)

- ~~Prompt por bloques (sección 5), reemplazando `prompt_builder.py` (Q2).~~ Hecho: `infrastructure/ai/prompting/` con
  `instructions.py`, `sections/` (un módulo por bloque, ninguno de más de 220 líneas), `composer.py`, `budgets.py` y `relevance.py`.
- ~~Bloque de identidad en todos los mensajes (Q1).~~ Hecho: nombre, sector y promesa en cada mensaje.
- Hecho además: el catálogo (detalle de la oferta y lista de precios) entra entero si cabe; si no, lo más relacionado con lo que
  busca el cliente y cuántas opciones más hay. Antes, 300 productos eran unos 205.000 caracteres por mensaje; ahora unos 23.500 en
  el peor caso (todo el contrato al máximo).

Cómo se verificó (laboratorio de regresión contra la versión en producción, `ea82a36`):
1. `exp_20261110_fase2_linea_base`: línea base; control negativo (una palabra cambiada) detectado en los 9 negocios.
2. `exp_20261110_fase2a_prompt_modular`: la reorganización, sin cambiar nada: motor sin diferencias, más 288 prompts idénticos
   byte a byte (9 negocios × 2 canales × 16 estados de conversación).
3. `exp_20261110_fase2b_identidad_y_catalogo`: los cambios intencionales. Solo cambian las líneas de identidad; respuestas,
   intenciones, uso de IA, modelo, webhook y configuración de los 9 negocios, idénticos.
- ~~Salida estructurada del proveedor: sin repetir la llamada completa (T1).~~ Hecho: `json_object` y aprovechamiento sin repetir.
- ~~Un solo juego de intenciones en motor y panel (T2).~~ Hecho.
- ~~Guardar el consumo de tokens por negocio (T3).~~ Hecho: por negocio, día y modelo, visible en el panel.

**Terminada cuando:** cada mensaje hace una sola llamada salvo fallo del proveedor; hay pruebas de presupuesto por bloque; el
consumo de cada negocio está en la base.

### Fase 3: cada campo del panel conectado (L) — hecha

- Conectar al motor, con su prueba, todo lo que tiene pantalla (Q3): estilo, mensajes, horarios, cliente ideal, posicionamiento,
  credibilidad, políticas, aclaración del precio, financiación y la estrategia avanzada.
- Envíos, domicilios, recogida y agenda, e inventario con existencias, con pantalla en el panel y conectados al motor: son
  parte de la versión 1.

**Terminada cuando:** la matriz de trazabilidad no tiene ningún campo «pendiente» con pantalla.

### Fase 4: atención humana profesional (M)

Sección 4 completa: configuración, decisión estructurada, horario, pausa de la IA por chat, mensaje de traspaso y aviso por correo
(H1–H6).

**Terminada cuando:** «quiero un asesor» primero recibe ayuda; un reclamo pasa directo; fuera de horario se toman los datos; la
IA no responde mientras alguien atiende.

### Fase 5: canales en la nube (L)

- **WhatsApp por QR con uazapi** (primero): el negocio pega su servidor y su token de uazapi en Canales, escanea el QR desde el
  panel, el webhook se registra solo y el token se guarda cifrado. Aviso en el panel: es una conexión no oficial; Meta puede
  bloquear números con envíos masivos.
- **WhatsApp Cloud API de Meta** (después): mismo contrato de canal, otro conector.
- Telegram por negocio: el negocio pega el token de su bot en Canales, el webhook se registra solo y el token se guarda cifrado.
- Todos los canales detrás de una sola interfaz (`ChannelConnector`: recibir, enviar, verificar firma): agregar un canal es
  agregar un conector, no tocar el motor.
- Un solo almacén de conversaciones: los canales escriben en la bandeja y la memoria del motor cuelga de cada hilo (A3).
- Responder desde el panel: los mensajes del equipo salen por el canal.
- Memoria de «Probar» en la base (A6).

**Terminada cuando:** un cliente escribe por Telegram y por WhatsApp, la IA responde con la configuración publicada, el chat
aparece en la bandeja y el equipo puede responder desde el panel.

### Fase 6: retirar el sistema anterior (M)

Borrar la API de administración vieja, los modelos con ids enteros, `python-jose`, el *polling* de Telegram, `ConfigService` y las
tablas `admin_users`, `tenant_secrets`, `tenant_settings`, `tenant_channels`. Dividir `memory_repository.py` y `ai_execution.py`
en módulos pequeños y quitar los errores silenciados (A4, A5).

**Terminada cuando:** no queda código ni tabla del sistema anterior y ningún módulo supera unas 400 líneas.

### Fase 7: operación para lanzar (M)

- Vercel Pro (O1).
- Monitoreo de errores y alertas (O2).
- Copias de seguridad de Neon con una restauración probada (O3).
- Correo transaccional: verificación, recuperar contraseña, avisos (O5, S6).
- Términos de uso y política de tratamiento de datos (O4).

### Fase 8: lanzamiento (S)

- Prueba completa en la rama `pruebas` (Preview) con un negocio de ejemplo.
- `asesor_ai_prod` atendiendo clientes reales por un canal, con seguimiento diario la primera semana.

## 7. La versión 1 está terminada cuando

1. Cualquier persona crea su cuenta, crea su negocio, lo configura, pega su clave y conecta un canal sin ayuda.
2. Todo lo que se configura en el panel cambia lo que hace el asistente, y hay una prueba que lo demuestra.
3. No queda ningún YAML ni código del sistema anterior.
4. Cada mensaje hace una sola llamada al modelo y su consumo queda registrado.
5. El asistente resuelve primero y pasa a una persona según las reglas del negocio, avisando al equipo.
6. Ningún registro contiene tokens, contraseñas ni mensajes de clientes.
7. Hay monitoreo, copias de seguridad probadas, correo transaccional, términos y política de datos.

## 8. Decisiones tomadas (10 de noviembre de 2026)

- **Sin pagos, suscripciones ni cobros** en la plataforma. El asistente sí comparte los medios de pago del negocio con sus
  clientes, como hoy.
- **Correo:** Resend (plan gratuito: 3.000 correos al mes, 100 al día) para los avisos al equipo. La verificación de correo y la
  recuperación de contraseña las envía Neon Auth con su proveedor incluido.
- **WhatsApp:** por QR con uazapi primero; después la API oficial de Meta.
- **Envíos, domicilios e inventario:** entran en la versión 1.
- **Atención humana por defecto:** el asistente ofrece ayudar una vez antes de pasar; si nadie atiende en 30 minutos, el asistente
  retoma la conversación (el negocio puede cambiar ambos).
