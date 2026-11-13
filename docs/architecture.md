# Arquitectura Del Sistema

## Propósito De Este Documento

Este documento describe la arquitectura activa del sistema según el código actual del repositorio. No documenta módulos eliminados ni capas teóricas no presentes en el runtime.

El foco está en responder tres preguntas:

1. Por dónde entra un mensaje y cómo sale una respuesta.
2. Qué rol cumple cada capa del runtime actual.
3. Cómo el contexto del tenant modifica el comportamiento final.

## Flujo Completo Del Sistema

Hay tres entradas activas:

- WhatsApp por código QR (uazapi): el canal en uso en la nube
- webhook de WhatsApp Cloud API de Meta
- «Probar asistente» en el panel (y el endpoint de simulación, apagado por defecto)

Las tres usan el mismo pipeline y la misma fuente: la versión publicada del negocio en el almacén (Neon en la nube).

### WhatsApp Por Código QR (uazapi)

```text
uazapi (aviso de la instancia del negocio)
-> project/app/api/controllers/whatsapp_qr_webhook.py      POST /api/v1/channels/whatsapp/{webhook_id}: identifica el negocio
                                                            por el id secreto y el token de su instancia, y contesta enseguida
-> project/app/application/channels/whatsapp_inbound.py    guarda el mensaje en la bandeja (sin duplicados), y después:
                                                            «escribiendo…», entiende fotos y audios, responde o pasa a una persona
-> project/app/infrastructure/ai/media_interpreter.py      describe la foto o transcribe la nota de voz, con la clave del negocio
-> project/app/services/ai_service.py -> mismo pipeline (abajo)
-> project/app/infrastructure/channels/uazapi.py           envía la respuesta; los recibos de entregado y leído llegan por el webhook
-> project/app/infrastructure/business_config/conversation_store.py   la conversación queda en la bandeja del panel
```

### WhatsApp Cloud API De Meta

```text
WhatsApp Cloud API
-> project/app/main.py
-> project/app/api/routes.py
-> project/app/api/controllers/whatsapp_webhook.py
-> project/app/services/tenant_channel_resolver.py
-> project/app/connectors/router.py
-> project/app/connectors/whatsapp/meta/parser.py
-> project/app/application/runtime/tenant_runtime_loader.py
-> project/app/application/runtime/runtime_yaml_builder.py
-> project/app/infrastructure/business_config/runtime_access.py
-> project/app/services/ai_service.py
-> project/app/application/ai_pipeline.py
-> project/app/application/pipeline/conversation_flow.py
-> project/app/application/pipeline/sales_flow.py
-> project/app/application/pipeline/ai_execution.py
-> project/app/application/pipeline/response_router.py
-> project/app/services/ai/ai_orchestrator.py
-> project/app/infrastructure/ai/prompting/builder/prompt_builder.py
-> project/app/domain/ai/prompt_context.py
-> project/app/services/ai_runtime/runtime_llm/client.py
-> project/app/services/ai/structured_output.py
-> project/app/application/pipeline/response_postprocessor.py
-> project/app/application/response_guard.py
-> project/app/connectors/whatsapp/transport_runtime.py
-> project/app/connectors/whatsapp/transport/sender.py
-> project/app/connectors/whatsapp/meta/sender.py
-> respuesta al canal
```

### Flujo De Simulación

```text
Cliente HTTP
-> project/app/main.py
-> project/app/api/routes.py
-> project/app/api/controllers/simulation.py
-> project/app/api/dependencies.py
-> project/app/services/ai_service.py
-> mismo pipeline AI-first del runtime
-> respuesta JSON
```

La diferencia es operativa:

- `whatsapp_webhook.py` recibe un evento real y envía respuesta al canal.
- `simulation.py` usa el mismo motor de respuesta, pero devuelve JSON sin enviar mensaje por connector.

## Componentes Activos

## FastAPI Y Capa HTTP

- `project/app/main.py`: inicia FastAPI, prepara logger, valida entorno y monta las rutas.
- `project/app/api/routes.py`: registra controladores HTTP.
- `project/app/api/controllers/whatsapp_qr_webhook.py`: entrada de WhatsApp por código QR (uazapi), una ruta secreta por negocio.
- `project/app/api/controllers/whatsapp_webhook.py`: entrada de WhatsApp Cloud API de Meta (exige su firma).
- `project/app/api/controllers/simulation.py`: entrada controlada para simulación y validación.
- `project/app/api/dependencies.py`: resuelve el tenant para endpoints públicos y autenticados.

La capa HTTP no decide la respuesta. Su trabajo es recibir, validar, resolver tenant y delegar al runtime.

## Orquestación Del Runtime

- `project/app/services/ai_service.py`: fachada de alto nivel para generar respuesta comercial.
- `project/app/application/ai_pipeline.py`: coordinador central del pipeline.

`AIService` no contiene el negocio completo. Su responsabilidad es delegar al pipeline, consolidar metadata, aplicar guardas de salida y exponer una interfaz simple al resto del sistema.

## Pipeline Activo

El pipeline actual no está separado en archivos llamados `decision_engine` o `narrative_builder`. Esas responsabilidades existen, pero están distribuidas en componentes activos.

### Intent

No existe un archivo activo llamado `intent.py` para la decisión final del runtime. La interpretación actual se apoya en:

- el modelo LLM
- `project/app/services/ai/structured_output.py`
- `project/app/application/pipeline/response_router.py`

`structured_output.py` normaliza la salida del modelo y expone `intent`, `stage`, `next_step` y metadata útil para el resto del flujo.

### Decision Engine

No hay un módulo activo con ese nombre. La decisión efectiva se reparte entre:

- `project/app/application/pipeline/conversation_flow.py`
- `project/app/application/pipeline/sales_flow.py`
- `project/app/application/pipeline/response_router.py`

Qué hace cada uno:

- `conversation_flow.py`: decide early responses, continuidad, memoria y contexto del turno.
- `sales_flow.py`: decide qué contexto comercial, pricing, features e inventario deben inyectarse al runtime.
- `response_router.py`: decide si la salida proviene de IA o fallback por excepción, y conserva metadata operativa.

### Narrative Builder

Tampoco existe como archivo aislado. La construcción narrativa del turno actual se distribuye así:

- `project/app/infrastructure/ai/prompting/` (el prompt por bloques)
- `project/app/domain/ai/prompt_context.py`
- `project/app/services/ai/ai_orchestrator.py`

En la práctica:

- `prompt_context.py` resume memoria y contexto reciente.
- `prompting/` arma el prompt de cada mensaje por capas, de lo más fijo a lo más cambiante:
  1. Plataforma (`instructions.py`): cómo vende el asistente, la verdad primero, cómo responder una duda, pagos y el formato de
     respuesta. Igual para todos los negocios, en una sola voz; lleva su versión (`PROMPT_VERSION`).
  2. Manual del tipo de negocio (`sections/playbook.py`): productos, planes, servicios o servicios con cita.
  3. El negocio (`sections/business.py`: identidad, cliente ideal, horario y estilo), lo que vende con sus precios en palabras, sus
     opciones y existencias (`offer.py`, `money.py`, `inventory.py`), cómo compra y recibe el cliente (`delivery.py`), cómo se paga y
     se cierra (`payments.py`, sin datos de pago), sus políticas (`policies.py`), sus indicaciones (`guidance.py`), su cliente
     (`customer.py`: problemas, motivos, objeciones), su estrategia de venta (`strategy.py`) y sus preguntas frecuentes
     (`knowledge.py`). `vocabulary.py` dice en español los identificadores del panel (`detect_pain`, `license_type`).
  4. Esta conversación (`conversation.py`): el momento y lo que se sabe del cliente.
  - `composer.py` las ordena así para que el proveedor reutilice de su caché el comienzo del prompt, mide cada capa contra
    `budgets.py` y quita los datos de pago antes de que el prompt salga.
  - `relevance.py`: cuando las preguntas frecuentes o el catálogo no caben, elige lo más relacionado con lo que busca el cliente.
  - `history.py`: los últimos mensajes van al modelo como conversación (cliente y asistente), sin datos de pago.
  - `builder/prompt_builder.py`: la entrada pública (`PromptBuilderService.build`), delgada.
- `ai_orchestrator.py` hace una sola llamada al modelo (instrucciones, conversación reciente y mensaje del cliente), parsea la salida
  estructurada y marca cada respuesta con la versión del prompt.

Todo cambio al prompt se mide en dos laboratorios:
- `experiments/pricing_lab/run_regression_experiment.py`: la mecánica del motor (rutas, webhook, entrega de pagos), sin IA.
- `experiments/quality_lab/run_quality_eval.py`: la calidad con la IA real, con escenarios por tipo de negocio, revisiones exactas
  (precios inventados, datos de pago, formato) y un juez IA con rúbrica que califica a ciegas. Usa la clave del `.env` y cuesta centavos.

### AI

La integración activa con OpenRouter vive en:

- `project/app/services/ai_runtime/runtime_llm/client.py`

Ese archivo:

- construye el cliente HTTP real
- prepara payloads hacia `/chat/completions`
- registra trazas de request y response
- reporta `tokens_usage`

### Salida

La salida se consolida en varias capas:

- `project/app/services/ai/structured_output.py`: parsea contenido y metadata
- `project/app/application/pipeline/response_postprocessor.py`: aplica reglas de postproceso del texto
- `project/app/application/response_guard.py`: valida la salida contra la configuración del negocio
- `project/app/infrastructure/channels/uazapi.py` (WhatsApp por QR) o `project/app/connectors/whatsapp/meta/sender.py` (Meta): envían al canal

## ai_orchestrator.py

### Archivo Activo

- `project/app/services/ai/ai_orchestrator.py`

### Qué Recibe

El método principal `generate_business_reply()` recibe:

- `service`: la implementación runtime del LLM
- `tenant`: tenant actual
- `bot_config`: configuración opcional del runtime/modelo
- `user_message`: mensaje actual del usuario
- `conversation_history`: historial inmediato del turno
- `faq_results`: resultados FAQ ya resueltos
- `yaml_config`: el runtime del negocio, compilado de su versión publicada

### Qué Hace

Su rol exacto es:

1. pedir al runtime que construya el prompt
2. llamar al modelo con ese prompt y el mensaje actual
3. parsear la respuesta estructurada
4. devolver texto final y metadata sin reescribir el contenido comercial

No decide negocio. No clasifica manualmente. No fuerza respuestas.

### Qué Retorna

Retorna una tupla:

```text
(response_text, ai_used, metadata)
```

Donde:

- `response_text`: texto principal de respuesta
- `ai_used`: bool indicando si la respuesta provino de IA
- `metadata`: intent, stage, next_step y demás datos extraídos del structured output

## Construcción Del Prompt

### Entradas Reales Del Prompt

La construcción activa del prompt toma insumos de:

- `yaml_config` del negocio (su versión publicada, compilada)
- memoria conversacional resumida
- `conversation_history`
- `faq_results`
- contexto comercial consolidado en `sales_flow.py`
- reglas activas del builder

### Cadena Activa

```text
tenant_runtime_loader.py
-> runtime_yaml_builder.py
-> sales_flow.py
-> services/ai_runtime/runtime_llm/prompting.py
-> infrastructure/ai/prompting/builder/prompt_builder.py
-> domain/ai/prompt_context.py
```

### Qué Controla El Prompt

El prompt final controla, como mínimo:

- identidad conversacional
- grounding por negocio
- uso de pricing real
- foco del turno actual
- comportamiento comercial esperado
- límites de veracidad
- contexto reciente del cliente

`prompt_builder.py` no crea reglas de venta por hardcode. Estructura y prioriza el contexto que el modelo debe usar.

## Multi-Tenant

## Resolución Del Tenant

| Entrada | Cómo sabe de qué negocio es |
|---|---|
| WhatsApp por QR | El `webhook_id` secreto de la ruta (`business_channels`) y el token de la instancia que trae cada aviso |
| WhatsApp de Meta | El `phone_number_id` del aviso, con `project/app/services/tenant_channel_resolver.py` |
| «Probar» en el panel | El negocio abierto en el panel, con la cuenta de Neon Auth que es su dueña |
| Simulación (apagada) | `X-Tenant-Slug` y el administrador del sistema anterior (`project/app/api/dependencies.py`) |

Ver `docs/tenants.md`.

## Carga De La Configuración Publicada

Cada mensaje carga la versión publicada del negocio:

- `project/app/application/runtime/tenant_runtime_loader.py`: lee lo publicado por `runtime_access` (la única puerta del motor al
  almacén: solo lee) y lo compila con `project/app/domain/business_config/compiler.py`.
- `project/app/application/runtime/runtime_yaml_builder.py`: arma el `runtime_yaml` del turno (el nombre es histórico: ya no hay
  YAML de negocios).

Las secciones compiladas son:

- `sales`
- `business`
- `pricing`
- `inventory`
- `config`

Además se derivan bloques como:

- `capabilities`
- `post_payment`
- `channel`

Si el negocio no existe, no tiene versión publicada o el almacén falla, el motor no responde con datos viejos: el cliente recibe
un mensaje neutro y queda la alerta `business_config_unavailable`. Los datos de pago se descifran solo al compilar y nunca llegan
a la IA: el prompt nombra los medios y el motor entrega los datos cuando el cliente elige uno.

## Eliminar Un Chat

El panel elimina un chat con `DELETE /api/conversations/{id}` (o todos los de «Probar asistente» con
`DELETE /api/businesses/{slug}/conversations/tests`):

```text
panel (papelera del chat o de Clientes)
-> project/app/admin_api/conversation_routes.py
-> project/app/business_config_application/conversations.py   ConversationsService.delete: comprueba que el chat sea del usuario
-> project/app/application/channels/contact_memory.py         EngineContactMemory: el motor olvida al cliente
   -> project/app/infrastructure/persistence/memory_repository.py   SQLMemoryRepository.forget_contact
-> project/app/infrastructure/business_config/conversation_store.py   ConversationStore.delete
```

- **Primero la memoria del motor:** borra el historial (`conversation_messages`), la memoria comercial (`conversation_memory`) y el
  registro del cliente (`clients`), y su copia en RAM. Si falla, responde 503 y no se borra nada.
- **Después la conversación:** sus mensajes, archivos y avisos se borran en cascada en la base; las ventas quedan con
  `conversation_id` en `NULL`.
- Cada instancia del motor guarda el registro de cada cliente en una caché que vence en `IDS_CACHE_SECONDS` (60 s), para que
  ninguna siga usando uno borrado.
- Los chats de prueba no tienen memoria en el motor: solo se borra la conversación.

## Eliminar Un Negocio

`DELETE /api/businesses/{slug}?confirm=<nombre>` (Configuración → Eliminar negocio, o Tus negocios):

```text
panel (DeleteBusinessDialog)
-> project/app/admin_api/routes.py
-> project/app/business_config_application/business_deletion.py   BusinessDeletionService.delete
   1. BusinessAccess.require_owner + el nombre escrito (sin distinguir mayúsculas ni espacios de más)
   2. WhatsAppChannelService.disconnect: cierra la sesión y borra la instancia en uazapi (si falla: 409 y no se borra nada)
   3. BusinessConfigRepository.delete_business: DELETE de `tenants`; todo lo demás cae en cascada en una transacción
   4. EngineContactMemory.forget_business: la RAM del motor sobre los clientes de ese negocio (si falla, se registra)
```

- **Todo cae en cascada:** cada tabla con `tenant_id` lo declara con `ON DELETE CASCADE`, en las migraciones del panel y en el esquema
  del motor (`project/docs/postgresql_schema.sql`: `clients`, `conversation_messages`, `conversation_memory`...). Si alguna no
  pudiera, la transacción falla entera. `tests/test_business_deletion.py` comprueba que no queda ni una fila en ninguna tabla.
- **Claves de la cuenta:** las de «algunos» pierden ese negocio; las de un solo negocio se borran con él.
- **Los agentes por MCP no pueden eliminar negocios**, a propósito.

## Atención Humana

Qué pasa cuando un chat necesita a una persona. Lo decide `domain/business_config/attention.py` (puro: sin base, sin red y con la
hora como argumento), con los ajustes de Configuración → Atención humana (`business_attention_settings`, se aplican sin publicar) y lo
publicado del negocio (el horario de «Mi negocio» y los mensajes `after_hours` y `ai_resumed`, compilados en
`config.attention_messages`).

1. **El traspaso** (`application/channels/whatsapp_inbound.py`, `_hand_off`). Si el asistente marca `handoff`:
   - dentro del horario del equipo, la IA se pausa, el cliente empieza a esperar (`conversations.customer_waiting_since`) y recibe
     «Una persona de nuestro equipo te responderá en unos 10 minutos» (o nada, si el negocio lo eligió);
   - fuera del horario, el chat también espera a una persona, pero la IA no se pausa: le dice el horario y cuándo lo atienden (o el
     mensaje del negocio) y sigue ayudando.
   En los dos casos se crea un aviso en la campana (uno por espera) y `TeamAlerts` lo envía.
2. **Los avisos** (`business_config_application/attention.py`, `TeamAlerts`): por correo con Resend
   (`infrastructure/notifications/resend_email.py`, solo cuando un chat pasa a una persona) y como notificación Web Push a todos los
   dispositivos de los dueños (`infrastructure/notifications/web_push.py`: cifrado `aes128gcm` y firma VAPID). Cada canal se
   reserva en `notification_deliveries` antes de enviar: aunque dos procesos lo intenten, sale una vez. Nunca lanza.
3. **La espera.** Un mensaje del cliente con la IA pausada empieza la espera si no había una; la respuesta del equipo (desde el
   panel o desde el celular del negocio) y «Ya lo atendí» la terminan.
4. **La IA retoma** (`application/attention/resume_sweep.py`). La revisión busca chats pausados con un cliente esperando desde antes
   del tiempo que eligió su negocio, los reserva de forma atómica (`ConversationStore.resume_waiting`: una sola vez), envía la
   disculpa, responde lo que el cliente escribió mientras esperaba y avisa. El chat sigue esperando a una persona, y la IA no se
   vuelve a pausar sola (`ai_resumed_at`) hasta que alguien del equipo lo atienda. La corren Vercel cada 15 minutos
   (`project/vercel.json` → `/api/v1/internal/attention/run`, con `CRON_SECRET`), el tráfico del motor y del panel (una vez por
   minuto por proceso) y cada mensaje que llega a un chat pausado (una vez cada 5 s).
5. **Respuestas desde el celular.** El webhook ya no excluye lo que escribe el negocio desde su teléfono: `uazapi.parse_own_message`
   lo lee, queda en la bandeja como respuesta del equipo (sin repetirse) y la IA se pausa en ese chat. Lo que envía la API sigue
   excluido.

Lo prueban `tests/test_human_attention.py` y `tests/test_whatsapp_qr_channel.py`.

## Respuestas Rápidas

Los mensajes guardados de cada negocio que el equipo pone en un chat (Configuración → Respuestas rápidas). No pasan por el motor ni
por el prompt: el panel los pone en el cuadro de texto y salen como cualquier respuesta del equipo (`POST /conversations/{id}/messages`).

- **Reglas** (`domain/business_config/quick_replies.py`, puro): el atajo se normaliza («/Crédito » → «credito») y no se repite en el
  negocio; categoría opcional; de 1 a 10 mensajes de hasta 4.000 caracteres; máximo 500 por negocio. `{nombre}` se cambia por el
  primer nombre del cliente al usarla (lo hace el panel, `domain/quickReplies/quickReplies.ts`).
- **Servicio** (`business_config_application/quick_replies.py`): verlas y marcarlas como usadas, quien llega al negocio; crearlas,
  editarlas y borrarlas, su dueño (el único rol que existe hoy; cuando haya asesores, ellos solo las usarán).
- **Almacén** (`infrastructure/business_config/quick_reply_store.py`, tabla `quick_replies`, migración 0015): cada operación se filtra
  por el negocio; una respuesta de otro negocio responde como inexistente. Se borran con el negocio (cascada).
- **API** (`admin_api/quick_reply_routes.py`): `GET/POST /businesses/{slug}/quick-replies`, `PUT/DELETE .../{id}` y
  `POST .../{id}/use`.
- **Panel:** la página `features/quickReplies/` y, en el chat, `features/conversations/Composer.tsx` con `QuickReplyPicker.tsx`
  («/» o ⚡). Las respuestas de varios mensajes quedan en espera y salen en orden; si uno no sale, lo que falta vuelve a la espera.

- **Archivos** (migración 0017, `quick_reply_files`): se suben una vez (`POST /businesses/{slug}/quick-replies/files`, el cuerpo es
  el archivo como en el chat) y cada respuesta los nombra en sus mensajes (`{"kind": "file", "file_id", "text"}`). El almacén revisa
  que cada archivo sea del negocio, y borra los que ninguna respuesta usa pasada una hora. En el chat, el archivo sale desde el
  servidor (`POST /conversations/{id}/quick-reply-file`, sin bajarlo y volverlo a subir) por el mismo camino que un archivo adjunto.

Lo prueban `tests/test_quick_replies.py`, `tests/test_business_deletion.py` y `apps/admin-web/src/app/QuickReplies.test.tsx`. El
laboratorio `exp_20261112_respuestas_rapidas` dio motor sin diferencias.

## Archivos Desde El Chat

El equipo envía fotos, documentos, videos y audios desde Conversaciones. Como una respuesta de texto: se guarda enseguida con su
archivo («enviando», en `conversation_media`, igual que lo que llega), sale por el canal y la IA se pausa en ese chat.

- **Reglas** (`domain/business_config/conversations.py`, `validated_attachment`): los tipos permitidos, hasta 4 MB (en Vercel una
  petición no puede pasar de 4,5 MB), que el archivo empiece como dice ser (una foto con nombre de PDF no sale), el nombre limpio y
  el texto de hasta 1.024 caracteres.
- **API** (`POST /conversations/{id}/attachments`): el cuerpo es el archivo tal cual con su `Content-Type`; el nombre y el texto van
  en `X-File-Name` y `X-Caption`, codificados como en una URL (así no hace falta una librería de formularios).
- **Canal:** `ChannelMessenger.send_media` → uazapi `/send/media` con el archivo en base64 (`docName` para los documentos).
- **Panel:** el clip y pegar una imagen en `features/conversations/Composer.tsx`; las reglas en `domain/inbox/attachments.ts`.

Lo prueban `tests/test_conversations_inbox.py`, `tests/test_whatsapp_qr_channel.py` y `apps/admin-web/src/app/Conversations.test.tsx`.

## Equipo Y Roles

Cada negocio tiene un equipo: **Dueño**, **Administrador** y **Asesor**. El rol decide lo que cada persona puede hacer, en el servidor
(que es quien decide) y en el panel (que solo muestra lo que el rol permite y explica por qué no).

- **Reglas** (`domain/business_config/team.py`, puro): qué puede cada rol (`ATTEND`, `REPORTS`, `CONFIGURE`, `TEAM`,
  `DELETE_BUSINESS`), quién puede tocar a quién (siempre queda un dueño; nadie se toca a sí mismo; solo un dueño nombra o toca
  dueños) y la invitación (correo, rol, vence en 7 días, enlace de 32 bytes del que solo se guarda la huella SHA-256).
- **Acceso** (`business_config_application/access.py`): `require(principal, negocio, need)` devuelve el rol; si no es miembro, el
  negocio «no existe» (404); si su rol no alcanza, `NotAllowedError` (403) con el motivo. Las rutas que cambian el negocio usan
  `ConfigurableSlug` (`admin_api/routes.py`); los servicios piden lo suyo (reportes y anular ventas: `REPORTS`; integraciones,
  atención humana y crear respuestas rápidas: `CONFIGURE`). Leer la configuración sigue siendo de todo el equipo: el panel la
  necesita para abrir el negocio.
- **Servicio** (`business_config_application/team.py`) y **almacén** (`infrastructure/business_config/team_store.py`, migración
  0016): cambiar un rol, quitar a alguien y aceptar una invitación se deciden y se aplican en la misma transacción, con las filas
  bloqueadas en PostgreSQL.
- **API** (`admin_api/team_routes.py`): `GET /businesses/{slug}/team`, invitar, renovar, retirar, cambiar rol y quitar; `GET
  /invitations/{token}` sin sesión y `POST /invitations/{token}/accept` con la cuenta del correo invitado. Solo en la nube.
- **MCP:** un agente solo trabaja en los negocios que quien lo conectó puede configurar (`mcp/access.py`, `mcp/oauth.py`).
- **Panel:** `domain/team/team.ts` (la misma tabla), `state/roleContext.ts` (el rol del negocio abierto, que llega con la lista de
  negocios), el menú y Configuración filtran por `need` (`navigation/navItems.ts`), `layout/RequireCapability.tsx` para quien llega
  con un enlace guardado, `features/team/TeamPage.tsx` (Configuración → Equipo) e `InvitationPage.tsx` (`/invitacion/<token>`).

Lo prueban `tests/test_team.py` y `apps/admin-web/src/app/Team.test.tsx`.

## Centro De Ayuda

La ayuda de la plataforma: artículos en Markdown que leen las personas en el panel y los agentes por MCP. No toca datos de ningún
negocio ni pasa por el motor.

- **Artículos** (`project/content/help/<tema>/<slug>.md`, ver su `README.md`): encabezado de metadatos y texto con un Markdown
  limitado (secciones, listas de un nivel, tablas, avisos y enlaces a otro artículo, a una pantalla `panel:ruta` o `https://`).
- **Reglas** (`domain/business_config/help.py`, puro): los temas en el orden del menú (`HELP_MODULES`), leer un artículo y rechazar
  uno mal escrito, revisar que los enlaces entre artículos existan y buscar (título > palabras clave y resumen > texto; sin tildes,
  con la raíz de cada palabra y sin las que aparecen en todo).
- **Servicio** (`business_config_application/help.py`): lee la carpeta una vez al arrancar; un artículo mal escrito detiene el
  arranque con el motivo.
- **API** (`admin_api/help_routes.py`, con sesión): `GET /help`, `GET /help/search?q=` y `GET /help/articles/{slug}`.
- **MCP** (`mcp/tools/help.py`, sin permiso): `search_help` y `read_help_article`.
- **Panel:** `features/help/` (el Centro de ayuda en `ayuda`, cada artículo en `ayuda/<slug>`, «Empieza aquí» marcado con lo que el
  panel ve del negocio y el lector de Markdown, que nunca pinta HTML crudo) y `layout/HelpPanel.tsx` (la ayuda de la pantalla abierta,
  desde el botón **?** junto a la campana). Qué artículo explica cada pantalla está en `domain/help/help.ts`.

Lo prueban `tests/test_help_center.py` y `apps/admin-web/src/app/Help.test.tsx` (que también lee los artículos reales para revisar
cada `panel:ruta`).

## API Del Asistente

Cualquier plataforma que haga peticiones HTTP conversa con el asistente de un negocio por HTTP (`POST /api/v1/assistant/messages`). Referencia para
quien la integra: [api.md](api.md).

- **Claves** (`domain/business_config/api_keys.py`, `key_permissions.py`, `infrastructure/business_config/api_key_store.py`):
  - son de quien las crea y entran a un negocio, a todos los de su cuenta o a algunos (migración 0013);
  - tienen permisos por área y pueden vencer;
  - conversar con el asistente (`assistant:chat`) exige una clave de un negocio;
  - las de la cuenta son para el servidor MCP ([mcp.md](mcp.md)); una conexión de Claude o ChatGPT por inicio de sesión (OAuth) es una clave de la cuenta de tipo `oauth`, sin valor fijo. Se muestra una sola vez; la base guarda su huella SHA-256 y su comienzo visible. Se crean,
  listan y revocan desde Integraciones (`admin_api/integration_routes.py`, `business_config_application/integrations.py`).
- **Ruta** (`api/controllers/assistant_api.py`): reconoce la clave, comprueba el permiso y los límites (60 por minuto por clave,
  1.500 por hora por negocio), revisa el cuerpo (`domain/business_config/assistant_api.py`) y responde con `{code, message, issues}`
  en los errores.
- **Flujo** (`application/channels/assistant_api.py`): el mismo de WhatsApp en el canal `api`. Guarda el mensaje (datos de pago
  ocultos), responde con lo publicado y la memoria del cliente, y pasa a una persona con la misma regla de horario
  (`application/channels/handoff_plan.py`, compartida con WhatsApp). La respuesta sale completa para el cliente; entregarla es del
  sistema que llamó. Si la IA está pausada, no responde (`attended_by: team`).
- **Pedidos repetidos**: con `Idempotency-Key`, la respuesta queda cifrada 24 horas (`api_idempotency`,
  `infrastructure/business_config/idempotency_store.py`) y se devuelve igual, sin gastar la IA.
- **La IA retoma** los chats de la API que nadie atendió igual que los de WhatsApp, pero en silencio: no hay por dónde escribirle al
  cliente, así que responde su próximo mensaje.

## Cómo Afecta El Tenant La Respuesta

El tenant cambia directamente:

- qué vende el negocio
- cómo se explica el valor
- qué precio existe y cómo se cobra
- qué capacidades o canales están disponibles
- qué memoria reciente debe influir en la respuesta

La respuesta final no es genérica. Se construye sobre la versión publicada del negocio activo.

## Observaciones Técnicas Relevantes

- El canal en uso en la nube es WhatsApp por código QR (uazapi); la API oficial de Meta tiene su conector y su webhook.
- No hay `decision_engine.py` ni `narrative_builder.py` como archivos activos. Sus responsabilidades están distribuidas.
- El runtime es AI-first: el backend organiza contexto, acceso y validación, pero la interpretación del turno y la redacción dependen del modelo.
- La simulación es parte importante de la arquitectura porque permite probar el mismo motor sin enviar mensajes reales al canal.