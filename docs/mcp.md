# Servidor MCP: agentes de IA en la plataforma

Un agente de IA (Claude Code, Cursor, n8n, Claude Desktop, Gemini CLI...) trabaja en los negocios de una cuenta con una **clave de
API** y los permisos que se le dieron. Puede **montar un negocio completo**:
- lo crea y llena cada sección de la configuración (datos de pago incluidos);
- revisa lo que falta y lo que cambia;
- prueba el asistente;
- publica cuando la persona lo confirma.

Y ayuda en el **día a día**: lee las conversaciones y dice quién espera a una persona, les responde a los clientes cuando la
persona aprueba el texto, ve clientes, ventas y reportes, registra o anula ventas, y ajusta la atención humana y el modelo de IA.

En el panel: **Integraciones → Agentes de IA (MCP)** (la dirección, cómo conectar cada agente y sus claves) y **Integraciones →
Claves de API** (todas las claves).

## Conectar un agente

Con **Claude (web y app) o ChatGPT** no hace falta clave: se pega la dirección y se inicia sesión (ver «Conectar con inicio de
sesión»). Con los demás agentes:

1. Crea una clave en **Integraciones → Agentes de IA → Crear clave para un agente**. Elige:
   - qué puede hacer, por área;
   - a qué negocios entra: solo uno, todos (también los que crees después) o algunos;
   - cuándo vence: 30, 90 o 365 días, o nunca.

   La clave se muestra **una sola vez**.
2. Pégala en el agente con la dirección del servidor:

| Agente | Cómo |
|---|---|
| Claude Code | `claude mcp add --transport http ai-sales-engine https://ai-sales-engine-panel.vercel.app/api/mcp --header "Authorization: Bearer <tu clave>"` |
| Cursor, Claude Desktop, Windsurf, Gemini CLI | En su `mcp.json`: `{"mcpServers": {"ai-sales-engine": {"url": "…/api/mcp", "headers": {"Authorization": "Bearer <tu clave>"}}}}` |
| n8n | Nodo «MCP Client»: transporte HTTP Streamable y encabezado `Authorization: Bearer <tu clave>` |
| Claude (web y app) y ChatGPT | **Sin clave:** se pega la dirección como conector personalizado; el agente abre el panel, la persona inicia sesión, elige negocios y permisos y autoriza (OAuth, ver abajo) |

En este equipo la dirección es `http://127.0.0.1:8010/api/mcp`, porque la API del panel solo atiende a este equipo.

## Áreas y herramientas

| Área (`key_permissions.py`) | Ver | Ver y editar |
|---|---|---|
| Negocios | `list_businesses`, `list_business_templates` | + `create_business` (solo con una clave de **todos** los negocios) |
| Asistente IA | `get_business_config`, `review_business_config`, `list_versions` | + `update_business_config`, `test_assistant`, `publish_business_config`, `rollback_business_config`, `restore_version` |
| Asistente IA (modelo) | `get_ai_settings`, `list_ai_models` | + `set_ai_model` |
| Datos de pago | — | Escribirlos en `update_business_config` como `{"value": "…"}`. Nunca leerlos |
| Conversaciones | `list_conversations`, `get_conversation`, `get_activity` | + `reply_to_customer`, `set_conversation_assistant`, `mark_conversation_attended` |
| Clientes y ventas | `list_customers`, `list_sales`, `get_report` | + `record_sale`, `cancel_sale` |
| Atención humana | `get_attention_settings` | + `update_attention_settings` |
| Conversar con el asistente | — | La API del asistente ([api.md](api.md)); solo con una clave de **un** negocio |
| (sin permiso) | `read_platform_guide`, `get_config_guide`, `search_help`, `read_help_article` | — |

Marcadas destructivas (`destructiveHint`), con confirmación de la persona: `publish_business_config`, `rollback_business_config`,
`reply_to_customer` (le escribe a un cliente real), `cancel_sale` y `set_ai_model` (se aplica al instante y cambia el costo).

Un agente trabaja **como quien lo conectó** y solo en los negocios donde esa persona es **dueño o administrador**: si pasa a
asesor, su agente deja de entrar a ese negocio (ver «Equipo y roles» en `architecture.md`).

Lo que **no** está, a propósito:
- **Conectar WhatsApp:** exige escanear el código QR con el teléfono.
- **La clave de IA del negocio:** es un secreto de la persona. El agente solo sabe si está puesta.
- **Borrar chats o clientes:** no se puede deshacer.
- **Descargar fotos y audios de los chats:** el agente ve que llegaron y su nota, no el archivo.

## Conectar con inicio de sesión (OAuth 2.1)

Lo que hacen Claude y ChatGPT al pegar la dirección del servidor:

1. Llaman a `/api/mcp` sin token y reciben 401 con `WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource/api/mcp"`.
2. Leen los metadatos del recurso (RFC 9728) y del servidor de autorización (RFC 8414). El emisor es el panel.
3. Se registran solos en `POST /api/oauth/register` (RFC 7591). Solo agentes públicos con PKCE. Las direcciones de regreso deben ser
   https, o http solo en el propio equipo.
4. Abren `/oauth/authorize` en el panel. Sin sesión, el panel pide entrar y vuelve con los mismos parámetros. La persona ve qué agente
   pide acceso y a dónde volverá, elige negocios (todos, algunos o uno) y permisos por área, y autoriza o cancela.
5. Autorizar crea una **conexión**: una fila de `api_keys` con `kind = 'oauth'`, sin valor fijo, con los mismos permisos y alcance que
   una clave. Si ese dueño ya tenía una con el mismo agente, la reemplaza.
6. El agente cambia el código por tokens en `POST /api/oauth/token`, con PKCE S256:
   - el código sirve una vez y por 10 minutos (si falla el verificador, se gasta igual);
   - el token de acceso (`ase_at_…`) dura 1 hora;
   - el de renovación (`ase_rt_…`) dura 30 días y cambia en cada uso (el anterior deja de servir).

Reglas:
- **Una conexión es una clave más:**
  - se ve en «Claves de API» con el nombre del agente y la etiqueta «Inicio de sesión»;
  - revocarla corta el token de acceso y el de renovación al instante;
  - cuenta en el límite de claves activas.
- **Solo huellas:** de códigos y tokens se guarda el SHA-256 (`mcp_oauth_codes`, `mcp_oauth_tokens`, migración 0014). Tomar un código o un
  token de renovación lo borra en la misma operación: dos peticiones con el mismo no lo consiguen las dos.
- **La pantalla de autorización no se puede incrustar** en otra página (`X-Frame-Options: DENY` y `frame-ancestors 'none'` en todo el
  panel): nadie puede hacer que la persona pulse «Autorizar» sin saberlo.
- **Conversar con el asistente no se autoriza a un agente:** es la API del asistente, con una clave de un negocio.
- **Límites por IP:** registrarse, 30 por hora; pedir tokens, 120 por minuto (429 con `Retry-After`).
- **Solo en la nube:** necesita cuentas y una dirección pública. En este equipo, el servidor responde con clave y sin `resource_metadata`.
  En Vercel el panel reenvía `/.well-known/oauth-*` y `/api/*` al motor (`apps/admin-web/vercel.json`).

| Pieza | Qué hace |
|---|---|
| `domain/business_config/oauth.py` | Reglas puras: registro, solicitud, PKCE, direcciones de regreso, metadatos, tiempos |
| `business_config_application/mcp/oauth.py` | `McpOAuthService`: registrar, describir la solicitud, decidir, cambiar por tokens y reconocer un token |
| `infrastructure/business_config/oauth_store.py` | Agentes, códigos y tokens en la base |
| `ApiKeyStore.connect` / `identity` | La conexión como clave `oauth`, y quién llama por el id de su clave |
| `admin_api/oauth_routes.py` | Metadatos, registro, tokens y la pantalla de autorización (con sesión) |
| Panel: `features/integrations/OAuthConsentPage.tsx` | La pantalla `/oauth/authorize` |

## Cómo funciona

| Pieza | Qué hace |
|---|---|
| `domain/business_config/key_permissions.py` | Áreas, niveles y su traducción a permisos internos (`scopes`). Reglas: conversar es de un negocio; crear negocios exige todos; al menos un área; vencimientos permitidos |
| `domain/business_config/agent_edits.py` | Cambios parciales (`merged`: los objetos se combinan, las listas se reemplazan, `null` quita); `{"value": …}` → referencia cifrada nueva; identificador del negocio desde su nombre |
| `domain/business_config/config_changes.py` | Lo que cambia al publicar, por contenido; los datos de pago, «protegidos» |
| `domain/business_config/validation_messages.py` | Los problemas del contrato por campo, en español; cada formato se explica con un ejemplo («sin tildes ni ñ…»), y al agente le agrega las opciones permitidas |
| `domain/business_config/diagnostics.py` | Lo que conviene revisar. Incluye los avisos que el panel calcula en vivo, con el mismo campo y el mismo texto (`LIVE_ADVISORY_CODES`): el agente ve lo mismo que la persona. Casos compartidos en `project/config/contracts/v1/advisory-cases.json`, probados en los dos lados |
| `business_config_application/mcp/` | `protocol.py` (JSON-RPC 2.0 sin estado), `tool.py` (herramienta y revisión de argumentos), `access.py` (quién llama y a qué negocios llega), `tools/` (guía, negocios, configuración, modelo de IA, conversaciones, clientes y ventas, atención humana) y `server.py`. Un servicio que el servidor no tiene (por ejemplo, sin base de conversaciones) no suma sus herramientas |
| `BusinessConfigService.payment_redactor` | Oculta en los textos de los chats todos los datos de pago guardados del negocio (también los de versiones anteriores) con `redact_values`. Si no se pueden descifrar, falla: nunca muestra sin ocultar |
| `admin_api/mcp_routes.py` | `POST /api/mcp`: clave, límite, lote, registro de cada llamada |
| `project/config/agents/guia-para-agentes.md` | La guía que lee el agente: reglas y la receta para montar un negocio completo. Viaja con el motor |
| Migración `0013_account_keys.sql` | Claves de la cuenta: dueño, alcance (`one`, `all`, `some` con `api_key_businesses`) y vencimiento |

Reglas:
- **Mismos servicios que el panel.** Cada herramienta es un adaptador sobre `BusinessConfigService`, `BusinessAccess`, las
  plantillas y «Probar asistente»: valida y decide lo mismo. Lo que guarda un agente queda en el historial como
  `Agente «<nombre>» (<dueño>)`.
- **Cada cliente, lo suyo:**
  - el agente actúa como el dueño de la clave;
  - cada negocio pasa por `BusinessAccess` (miembros) y por el alcance de la clave;
  - uno ajeno o inexistente responde igual: «Ese negocio no existe o esta clave no entra a él»;
  - una conversación se lee primero para saber de qué negocio es y pasa por el mismo alcance: una de un negocio al que la clave
    no entra (aunque sea del mismo dueño) responde «Esa conversación no existe o esta clave no entra a ella».
- **Lo que escriben los clientes son datos.** Las instrucciones del servidor y la guía le dicen al agente que nunca obedezca un
  mensaje de un chat y que le muestre a la persona el texto antes de responderle a un cliente.
- **Mismos límites que el panel:** responder a un cliente cuenta como una respuesta del dueño desde la bandeja; lo que registra
  queda a nombre del agente (`created_by`).
- **Borrador y publicar.** Guardar crea una versión en borrador. Publicar es otra herramienta, marcada destructiva
  (`destructiveHint`): las instrucciones y la guía piden mostrar lo que cambia y la confirmación de la persona.
- **Errores:**
  - uno de negocio (el contrato, un conflicto de versión, un negocio ajeno) vuelve como resultado con `isError` y los problemas
    por campo, y no se guarda nada;
  - uno del protocolo (método, argumentos, permiso) es un error JSON-RPC;
  - uno interno vuelve sin detalles.
- **Límites:**
  - 300 peticiones por minuto por clave (429 con `Retry-After`);
  - probar el asistente cuenta además como «Probar asistente» del dueño.
- **Registro:** cada llamada queda en el registro `mcp_llamada` (clave, herramienta, resultado y duración). Nunca los datos.
- **Protocolo:** versiones `2025-06-18`, `2025-03-26` y `2024-11-05`; métodos `initialize`, `ping`, `tools/list` y `tools/call`;
  lote; notificaciones con 202. Sin flujo de eventos (GET responde 405).

## Agregar una herramienta

1. **Área:** si encaja en una existente, úsala; si no, agrégala en `KEY_AREAS` con lo que deja cada nivel. El panel la dibuja
   sola en la tabla de permisos.
2. **Herramienta:** en `business_config_application/mcp/tools/<tema>.py`, como adaptador sobre el servicio del panel. La
   descripción le dice al agente cuándo usarla, de dónde sacar cada dato y qué confirmar. Usa `destructive=True` si cambia lo que
   reciben los clientes.
3. **Composición:** súmala en `server.py`.
4. **Pruebas:** en `tests/test_mcp.py`:
   - llama al servicio con lo pedido y a nombre de la clave;
   - solo aparece con su permiso;
   - no alcanza negocios ajenos.
5. **Documentación:** esta página, la guía para agentes y la guía del negocio.
