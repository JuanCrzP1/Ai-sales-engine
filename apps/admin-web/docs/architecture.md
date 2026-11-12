# Arquitectura del panel (`apps/admin-web`)

Estado: conectado a BusinessConfig v1 a través de la API local, con persistencia real en SQLite. Funciona solo en este equipo y
el motor comercial todavía no consume lo que aquí se publica.

```text
Navegador                    Este equipo (127.0.0.1)
┌──────────────────┐  /api   ┌──────────────┐    ┌──────────────────────┐    ┌────────────────────┐
│ Panel (React)    │ ──────▶ │ Proxy de Vite│ ─▶ │ API local (FastAPI)  │ ─▶ │ BusinessConfigSer- │
│ edita el         │         │ :5180        │    │ project/app/admin_api│    │ vice: contrato,    │
│ documento del    │ ◀────── │              │ ◀─ │ :8010                │ ◀─ │ versiones, cifrado │
│ contrato         │         └──────────────┘    └──────────────────────┘    └─────────┬──────────┘
└──────────────────┘                                                                   ▼
                                                                                   SQLite local
```

## Responsabilidades

| Parte | Responsabilidad |
|---|---|
| Panel | Interfaz, formularios, validación anticipada, navegación y comunicación con la API. No guarda nada |
| API del panel | Recibe las solicitudes, llama a los servicios, traduce sus errores y confirma el resultado. Solo usa la capa de aplicación (`BusinessConfigService` y los demás servicios), que es quien valida con el contrato: ni base de datos ni motor. La importación de ejemplos se le entrega desde fuera (`create_app(examples=...)`), solo en este equipo |
| BusinessConfig v1 | Contrato central: modelos, esquema, validaciones, compilador. El panel recibe de aquí los tipos generados y el esquema |
| Persistencia | Versiones inmutables y datos de pago cifrados: Neon en la nube, SQLite en este equipo |

## Capas

| Carpeta | Responsabilidad | Puede importar |
|---|---|---|
| `lib/` | Utilidades puras genéricas (texto, formato, ids) | — |
| `contracts/` | Tipos generados desde el contrato | — |
| `domain/` | Operaciones, validación anticipada y lectura del esquema, puras (sin React ni navegador) | `contracts`, `lib` |
| `repositories/` | Contratos asíncronos de persistencia y autenticación, y su error tipado | `domain`, `lib` |
| `infrastructure/` | Implementaciones: `api/` (cliente de la API local) y `local/` (acceso sin autenticación) | `repositories`, `domain`, `lib` |
| `state/` | Proveedores y hooks: sesión, negocios, configuración, guardado | `repositories`, `domain`, `lib` |
| `components/ui/` | Interfaz genérica; **no conoce el dominio** | `lib` |
| `components/brand/` | Logotipo | — |
| `components/config/` | Piezas ligadas al documento, incluido el campo generado desde el esquema (`ContractField`) | `ui`, `domain`, `lib`, `navigation` |
| `navigation/` | Rutas del espacio de trabajo y del recorrido | `domain`, `lib` |
| `layout/` | Estructura del panel, estado del guardado, protección de cambios, formularios generados, carga y error | `ui`, `brand`, `config-ui`, `state`, `navigation`, `domain`, `lib` |
| `features/<x>/` | Pantallas y formularios de cada sección. **Sin imports entre funcionalidades** | `ui`, `brand`, `config-ui`, `layout`, `state`, `navigation`, `domain`, `lib` |
| `app/` | Composición: implementaciones (`compositionRoot.ts`), rutas y espacio de trabajo por negocio | todo |
| `test/` | Backend en memoria, datos ficticios, prueba de arquitectura e integración | todo |

`src/test/architecture.test.ts` verifica estas reglas a partir de los imports reales, y además que ningún archivo use el
almacenamiento del navegador, que solo `infrastructure/api/httpClient.ts` hable con el servidor y que la página no cargue nada de
otros servidores. Para que vea siempre los archivos actuales, `vite.config.ts` desactiva la caché persistente de módulos de
Vitest (`fsModuleCache: false`).

## Principios

- **Un solo punto de elección de implementaciones:** `app/compositionRoot.ts`. Pantallas y estado solo conocen contratos.
- **El estado es el documento del contrato.** Ver D5.
- **El servidor es la autoridad.** `domain/validation/rules.ts` solo ayuda mientras se escribe, con mensajes para el negocio. Al
  guardar valida el contrato y sus errores vuelven con la ruta del campo, que es la misma que usa el formulario.
- **Nada se da por guardado sin confirmación.** `saved` solo se alcanza cuando la API aceptó el documento.
- **Carga y errores explícitos.** Un fallo de carga nunca se presenta como un negocio vacío. Un fallo de renderizado muestra
  `ErrorBoundary`, global y por sección.

## Registro de decisiones

### D1 — Sin autenticación local con contraseña

Comprobar contraseñas en el navegador no es una autenticación segura. El contrato `AuthService` conserva `verifiesCredentials` para
la autenticación real, y las pantallas de cuenta y las guardas se mantienen conectadas a él. Las pruebas usan un servicio en memoria
que sí verifica credenciales, para cubrir ese camino.

### D2 — Acceso local sin autenticación

`createLocalOperatorAuthService()` da una sesión fija, sin guardar nada, con `verifiesCredentials = false`: el panel no muestra
pantallas de cuenta ni menú de usuario y avisa de que solo funciona en este equipo. La autenticación definitiva llega con la fase de
nube, como otra implementación del mismo contrato elegida en `compositionRoot.ts`.

### D3 — Se retira el adaptador al motor

El panel tenía un modelo propio (`AssistantConfig`) y lo traducía hacia el contrato en un solo sentido. Se perdía todo lo que el modelo
no tenía, como los campos avanzados de los nueve negocios, y no se podía cargar un documento guardado. El adaptador pasó a `legacy/`.

### D4 — Limpieza explícita al cambiar el tipo de una cuenta

Al cambiar el tipo (por ejemplo, de Nequi a cuenta bancaria) se descartan los datos del tipo anterior, salvo la etiqueta y el estado de
la cuenta. Solo por esa acción explícita.

### D5 — El panel edita el documento del contrato

`BusinessDocument` son los tipos generados del contrato. Lo que no tiene pantalla se conserva al guardar, y una ruta de error del
servidor (`offer.plans.0.prices.0.monthly`) coincide con la del campo. Las pruebas de integración abren y guardan los nueve negocios
reales desde el panel y comprueban que no se pierde nada.

### D6 — Guardado explícito

Cada guardado crea una versión inmutable y exige un documento válido; el guardado automático crearía versiones por cada tecla y
fallaría mientras un negocio está a medias. Lo no guardado está protegido al salir del negocio (`useBlocker`) y al cerrar la pestaña
(`beforeunload`).

### D7 — Datos de pago: se reconocen sin exponerlos

El documento lleva referencias `secret_store:...`; los valores nuevos viajan aparte (`payment_values`, por referencia), una sola vez.
El servidor los cifra y responde con referencias nuevas. El panel nunca recibe un valor completo: cada respuesta trae `payment_fields`,
con el estado de cada referencia (`configured`, `missing`, `unreadable`) y una versión enmascarada que calcula el servidor
(`payment_data.mask_payment_value`). Antes el panel no recibía ni eso, y el dueño no podía saber qué método tenía configurado.

Lo descriptivo (tipo, banco, tipo de cuenta, etiqueta, estado) ya está en el documento: no hay un segundo modelo de pagos, y
`domain/config/paymentMethods.ts` solo lo combina con lo enmascarado para mostrarlo. Un dato guardado no se edita, se reemplaza: si el
campo de reemplazo queda vacío, no se envía y se conserva. Su formato se comprueba aquí para avisar mientras se escribe; la autoridad
es el servidor, que aplica las mismas reglas antes de guardar.

### D8 — Formularios generados desde el esquema

`ContractField` y `ContractSection` construyen los campos avanzados desde `GET /api/contract`, que es el esquema publicado. Un campo
nuevo del contrato queda editable sin duplicar su definición; `contractSchema.ts` solo aporta nombres y ayudas en lenguaje del negocio.
Los datos de pago no pasan por aquí: `payments` tiene su propia pantalla.

Para que nadie se enrede, el formulario se adapta al tipo de campo: un «sí / no / sin indicar» o una lista cerrada de hasta cuatro
opciones se elige con botones (`SegmentedControl`); los pasos de la conversación, lo que no debe hacer y los datos del cierre se eligen
con etiquetas en español (`ChipPicker` y `domain/config/vocabulary.ts`, el mismo vocabulario que el motor le dice a la IA); las horas
usan el reloj del navegador, el tema de una objeción se elige de una lista y cada elemento de una lista lleva un título con sentido
(«Objeciones: el precio»).

### D8b — Configuración por tarjetas

Cada sección del Asistente IA se arma con `SettingsGroup` y `SettingsCard` (`components/ui/SettingsCard.tsx`), con la distribución
de los paneles de configuración profesionales (Stripe, Shopify):
- Cada bloque («Lo esencial», «Entrega y existencias», «Para afinar»…) es una fila con su título y para qué sirve a la izquierda
  (queda a la vista al bajar) y sus tarjetas a la derecha, una debajo de otra y todas del mismo ancho.
- Nunca hay tarjetas de distinta altura lado a lado, así que no quedan huecos: se lee de arriba abajo, como un formulario.
- Una línea separa los bloques. En pantallas angostas el título va arriba.
- Cada tarjeta tiene ícono, color, título y para qué sirve. Las opcionales son filas compactas plegables (elemento `<details>`,
  accesible por teclado).
- El resumen (`features/overview`) muestra cada sección con su estado, sus datos clave y el acceso a probar y publicar; es la
  entrada desde el menú.

### D8c — Plantillas para empezar un negocio

Crear un negocio empieza por elegir cómo: «Empezar de cero» (la primera opción, que no es una plantilla) o una plantilla de
`GET /api/business-templates`. Las plantillas viven en el servidor (`project/config/business-templates/*.json`), validadas contra el
contrato al arrancar la API (`business_config_application/templates.py`, `domain/business_config/templates.py`); el panel solo recibe
título, descripción e ícono, y `POST /api/businesses` con `template` guarda el primer borrador. Al abrirse, el resumen avisa que hay
que cambiar los ejemplos y agregar los medios de pago: nada se publica solo.

### D8d — Canales: WhatsApp por código QR

Canales muestra WhatsApp con su logo y dos formas de conectarlo: código QR (lista) y la API oficial de Meta (próximamente, el mismo
contrato de canal con otro conector). El negocio no configura nada técnico: el servidor de uazapi y su token son de la plataforma y
nunca llegan al panel. Toca «Conectar WhatsApp», la API crea su instancia y devuelve el QR, y la pantalla pregunta el estado cada 3
segundos hasta que lo escaneen; a los dos minutos ofrece generar otro. Si la plataforma no tiene activa la conexión, lo dice sin
detalles técnicos.

`features/channels` usa `useChannels()` (`state/channelsContext.ts`), que cuelga del negocio abierto (`BusinessWorkspace`); el tipo
vive en `domain/channels/types.ts` y el contrato en `repositories/channels.ts`, con su implementación en
`infrastructure/api/apiChannels.ts` (`/api/businesses/{slug}/channels/whatsapp`). En las pruebas, `createMemoryWhatsApp` de
`test/fakes.ts` simula el servidor. Telegram y el chat web aparecen como «Próximamente»; Instagram se retiró.

### D8d2 — Sin barra superior

Como en Slack o Linear, la cuenta (foto, nombre, correo; «Mi perfil» y «Cerrar sesión») va abajo en la barra lateral y la campana
de avisos junto a la marca; sus menús se abren al lado de la barra (`position: fixed`, porque la barra recorta lo que se sale). El
estado de guardado solo aparece en las páginas del Asistente IA, que es donde se guarda. Conversaciones ocupa exactamente la
pantalla (`100dvh`, sin desplazamiento de la página). El título va en la cabecera de la lista de chats y solo se desplazan la
lista y los mensajes.

### D8e — Conversaciones en vivo

La bandeja se actualiza sola, como Auream: la lista se refresca cada 5 segundos y el chat abierto pide solo lo que cambió
(`GET /conversations/{id}/live?since=<cursor>`, con la hora del servidor como marca). Pregunta cada 1,5 segundos si hubo movimiento
en el último minuto y cada 4 en calma, y nada con la pestaña oculta. La lógica pura (unir por id, el intervalo) está en
`domain/inbox/live.ts`; el ciclo, en `state/useConversations.ts`.

En el chat se ven:
- las fotos, los audios (con su transcripción) y los documentos, que se descargan con la sesión del usuario (`useMediaUrl`);
- los chulos de lo que salió y el «escribiendo…» del asistente;
- por qué el chat pasó a una persona.

El equipo responde desde la caja de abajo. El mensaje aparece enseguida («enviando»), sale por el canal del cliente y la IA se pausa
en ese chat. Si no sale, se avisa y el texto vuelve a la caja. «Pausar IA / Reanudar IA» decide quién atiende. Las conversaciones de
prueba no tienen caja de respuesta.

### D8f — Clientes, ventas y reportes

`features/commerce` reúne las tres pantallas y el formulario «Registrar venta» que comparten. Se apoyan en
`state/commerceContext` y en `repositories/commerce.ts`, con su implementación en `infrastructure/api/apiCommerce.ts`
(`/api/businesses/{slug}/customers`, `/sales` y `/reports`).

- **Clientes:** cada contacto de un canal real con su etapa: nuevo → interesado → listo para comprar → pagó (por verificar) →
  cliente. Se filtra por etapa con las tarjetas de arriba y se busca por nombre o teléfono. Cada fila lleva a su chat y permite
  registrar una venta.
- **Ventas:**
  - las métricas de 30 días;
  - los pagos por verificar, con «Confirmar y registrar venta»;
  - el historial, donde anular deja la venta marcada.
- **Reportes:**
  - el periodo (7, 30 o 90 días) y sus métricas comparadas con el periodo anterior;
  - las conversaciones y las ventas por día;
  - el embudo;
  - quién respondió (la IA o el equipo) y el costo de la IA;
  - por qué los chats pasaron a una persona.

Los gráficos (`components/ui/Charts.tsx`) usan un color por serie, globo al pasar el mouse y una tabla oculta para lectores de
pantalla. Los dos colores de «Quién respondió» están validados para daltonismo.

### D8g — El celular como una aplicación

En pantallas de hasta 900 px, `layout/AppShell.tsx` muestra una barra superior con ☰ (izquierda), la sección abierta y su negocio
(`navigation/navItems.ts`, `titleForPath`) y la campana (derecha). El menú lateral pasa a ser un panel que se desliza: fondo oscuro,
bloquea la página de atrás, el foco entra al abrir y vuelve al ☰ al cerrar, y se cierra con la X, Escape, tocando afuera,
deslizándolo o al elegir una opción. `lib/useMediaQuery.ts` decide si la pantalla es de celular: la campana se monta una sola vez
(arriba en el celular, en el menú en pantalla grande), porque cada una consulta sus avisos. Ninguna pantalla se sale del ancho del
celular (se comprobaron las 15 a 390 px).

### D8h — Eliminar chats

`layout/DeleteChatDialog.tsx` confirma antes de eliminar y dice qué se borra (mensajes, archivos, avisos y lo que el asistente
recuerda del cliente) y qué no (las ventas). Lo usan Conversaciones y Clientes, porque un cliente es su chat. Si el servidor no
puede borrarlo, lo dice y el chat sigue ahí. Los chats de «Probar asistente» se borran de una vez desde la lista, con confirmación
en dos pasos.

### D8i — Diálogos por encima de todo

`components/ui/Dialog.tsx` se dibuja al final de la página (un portal de React): así cubre también el menú lateral, que tiene su
propia capa para que el menú de la cuenta y los avisos se abran por encima del contenido.

### D8j — Atención humana y notificaciones del dispositivo

Lo que dice el asistente (fuera del horario, al retomar) está en Mensajes y sí se publica; la atención humana, en Configuración (D8k),
y se aplica al instante.
- `repositories/attention.ts` define dos contratos: `Attention` (los ajustes de un negocio, `createAttention(slug)`) y `DevicePush` (las
  notificaciones de la persona en este navegador, una sola instancia de la aplicación).
- `infrastructure/browser/browserPush.ts` junta las API del navegador (Service Worker, Push, Notification) con la del panel. El
  permiso se pide primero, mientras dura el toque en el botón (Safari lo exige). En iPhone y iPad sin instalar el panel devuelve
  `install`, y la pantalla explica cómo instalarlo.
- `public/sw.js` muestra la notificación y, al tocarla, abre ese chat en una ventana del panel (solo rutas del propio panel). No guarda
  nada en caché. `vercel.json` lo sirve sin caché para que los cambios lleguen enseguida.
- La campana ofrece «Activar notificaciones» mientras no estén activadas ni bloqueadas, y distingue los avisos `ai_resumed` (la IA
  retomó un chat). El aviso del chat abierto dice si la IA está pausada (y desde cuándo espera el cliente), si la retomó o si el chat
  llegó fuera del horario.

### D8k — Configuración (del negocio) y Mi cuenta (de la persona)

Como en Shopify, Intercom o HubSpot, se separan dos cosas que antes se mezclaban (Mi perfil vivía dentro de la Configuración del
negocio y «Configuración» aparecía dos veces):
- **Configuración** es del negocio abierto y va sola, fija abajo en el menú de la izquierda (`.nav__bottom`). Su menú propio
  (`SETTINGS_GROUPS`): Asistente (Inteligencia artificial, Atención humana, Respuestas rápidas) y Facturación (Pagos y suscripciones).
- **Mi cuenta** es de la persona, igual en todos sus negocios, y se abre desde el menú de la foto (que ya no tiene «Configuración»):
  Mi perfil, Seguridad y Notificaciones (`ACCOUNT_GROUPS`, rutas `/cuenta/…`). Seguridad cambia la contraseña con la actual y, por
  defecto, cierra las demás sesiones; también cierra todas las demás sesiones aparte (`AuthService.changePassword` y
  `signOutOtherDevices`, sobre `change-password` y `revoke-other-sessions` de Neon Auth). Las notificaciones del dispositivo pasaron
  de Atención humana a Mi cuenta, porque son de cada persona y de cada dispositivo; Atención humana enlaza allá. Con el acceso local
  (sin cuentas) Mi cuenta solo muestra Notificaciones.
- Las dos usan el mismo diseño con menú propio (`layout/SettingsLayout.tsx`: `SettingsLayout` y `AccountLayout`). `/configuracion/perfil`
  redirige a `/cuenta/perfil`.

En Configuración, Lo que todavía no existe se ve con «Pronto» y su página dice qué traerá, para saber hacia dónde va la plataforma. En
el celular el menú es una fila de pestañas que se desliza. Todas las rutas viven bajo `/configuracion/…`; las anteriores (`/ia`,
`/atencion-humana`) redirigen. `isAssistantPath` ignora las rutas de Configuración, así una sección no se confunde con una pestaña del
asistente de nombre parecido. Fuera de un negocio (antes de crear el primero), Mi cuenta es una sola
página (`/perfil`) con todo.

En Inteligencia artificial cada parte se guarda por separado: el proveedor (OpenRouter; los demás, «Pronto»), la clave y el modelo.
La clave guardada se ve oculta (`sk-or-v1-••••…` y sus últimos caracteres) y nunca se vuelve a mostrar completa: el servidor solo la
guarda cifrada y no la devuelve, como OpenAI, Stripe u OpenRouter. «Cambiar clave» abre el campo para pegar otra, con el ojo para ver
lo que se pegó antes de guardar. El modelo se elige en una lista desplegable con buscador (`ModelPicker`: botón con `aria-haspopup`,
buscador como `combobox` y opciones como `listbox`), que se maneja con flechas, Enter y Escape.

### D8l — Integraciones

Sección propia del menú (entre Canales y Configuración), porque se muestra y se vende: «conéctalo con lo que ya usas». Canales queda
para donde escriben los clientes; Integraciones, para otras herramientas.
- `repositories/integrations.ts` (`createIntegrations(slug)`): resumen, claves (crear, listar, revocar) y la prueba de la API.
- El resumen es un catálogo (`domain/integrations/catalog.ts`, puro): categorías en pestañas (la elegida queda en `?categoria=`),
  buscador sin tildes y grupos Activas / Disponibles / Próximamente. Solo es «Disponible» lo que funciona hoy. Cada tarjeta lleva el
  logo del servicio sobre una ficha neutra (`components/brand/IntegrationMark.tsx`, logos de Simple Icons, CC0), igual que en
  Configuración → Inteligencia artificial. OpenRouter aparece activa cuando el negocio tiene su clave de IA.
- Tres pantallas: el catálogo, la API (estado de conexión, cómo
  funciona, datos de conexión, guías por plataforma en pestañas —`PlatformGuides.tsx` con `components/ui/Tabs.tsx`—, qué se envía
  y qué se recibe, y la prueba) y la tabla de claves. Solo la guía de Leona dice «Probado»: se probó con un flujo real; otras
  plataformas tendrán su pestaña cuando se prueben.
- **Agentes de IA (MCP)** (`AgentsPage.tsx`, `integraciones/agentes`):
  - la dirección del servidor y lo que se pega en cada agente (`mcpSnippets`); con «Claude y ChatGPT», cómo conectarlos sin clave;
  - la pantalla `/oauth/authorize` (`OAuthConsentPage.tsx`, contrato `AgentAuthorization`, de la cuenta y no de un negocio): quién pide acceso, negocios y permisos, autorizar o cancelar;
  - las claves de agente;
  - «Claude web y ChatGPT», marcado Próximamente (OAuth).
- **Claves:** son de la cuenta y tienen permisos por área (`PermissionMatrix.tsx`). Las áreas y lo que deja cada nivel vienen del
  motor (`overview.areas`), así que un área nueva se dibuja sola.
- **Crear una clave** (`CreateKeyDialog`, según `purpose`):
  - para conversar con el asistente basta el nombre;
  - para agentes se elige a qué negocios entra (este, todos o algunos, con `useMyBusinesses`), qué puede y cuándo vence.
- **Tabla de claves** (`KeysTable.tsx`, compartida): qué puede cada clave, a qué negocios entra, el último uso, el vencimiento y
  revocar.
- Una clave completa se ve una sola vez, en `NewSecretDialog`, con su botón de copiar (`components/ui/CopyButton.tsx`). Después
  solo su comienzo.
- Los chats del canal `api` se reconocen en la bandeja (ícono y nombre «API»). No se responden desde aquí, porque se atienden en
  la plataforma conectada, pero sí se pausa y se reanuda la IA.

### D8m — Guardado no es publicado

El dueño no sabía que tenía que publicar: el asistente seguía con la versión 1 mientras editaba la 4. Ahora siempre se ve:
- `ConfigProvider` carga el documento publicado (`GET /versions/{n}`, una sola vez por versión; si es la que se edita, no lo pide) y
  calcula `publication`: `never`, `pending`, `published` o `checking`. Compara **contenido** (`domain/config/publishChanges.ts`), no
  números de versión: guardar sin cambiar nada no deja nada pendiente. Si no puede leer lo publicado, cae al número de versión.
- Arriba del editor (`layout/SaveStatus.tsx`): «Guardado · hh:mm · Cambios sin publicar» en ámbar con «Revisar y publicar», o
  «Publicado · es lo que responde a tus clientes». En el menú, un punto ámbar en «Asistente IA». El Inicio y «Probar» usan el mismo
  estado.
- Los avisos en vivo que también da el servidor (`domain/validation/liveAdvisories.ts`) tienen el mismo campo y el mismo texto en los
  dos lados (casos compartidos en `project/config/contracts/v1/advisory-cases.json`, prueba `advisoryParity.test.ts`). «Publicar» no
  repite los diagnósticos que la pantalla ya muestra en vivo (`serverOnlyDiagnostics`).
- En Revisión (`features/review/PublishChanges.tsx`): «Lo que cambia al publicar», por sección, con cómo estaba y cómo queda. Los
  campos se nombran con el contrato (`schemaFieldNamer`) y los elementos de una lista por su título. Los datos de pago cambian de
  referencia cuando cambia su valor: se informan como «actualizado (protegido)», nunca su valor.

### D9 — API separada del motor y limitada a este equipo

`app.main` publica rutas del motor y en Docker escucha en `0.0.0.0`. La API del panel es otra aplicación, con el host fijo a `127.0.0.1`
sin opción para cambiarlo, documentación desactivada y un middleware que rechaza clientes, `Host` (DNS rebinding) y `Origin` ajenos. Sin
CORS: el panel llega por el proxy de Vite, en el mismo origen. El cliente HTTP escapa el identificador, y la API lo valida y comprueba
que el documento sea de ese negocio.

### D10 — Sin recursos de otros servidores

El panel cargaba la fuente Inter de Google Fonts. Se retiró para no avisar a un tercero cada vez que se abre y para funcionar sin
internet: usa Inter si está instalada y, si no, la fuente del sistema.

### D11 — El borrador de un plan o producto vive en el estado de la configuración

Antes vivía en la pantalla, así que se perdía al cambiar de sección y «Guardar cambios» lo dejaba fuera sin avisar. Ahora lo conserva
`ConfigProvider`: sigue ahí al volver, cuenta como cambio sin guardar en cuanto se escribe algo, y guardar se detiene y lo explica
hasta que se aplique o se cancele. No se guarda en el navegador: un cierre de la pestaña lo protege el mismo aviso de los demás cambios.

## Pendiente

- ~~Autenticación y autorización multiusuario~~: hecho (Neon Auth y `business_members`).
- ~~API y persistencia en la nube~~: hecho (la API del panel bajo `/panel` del motor, en Neon).
- ~~Integrar el motor con lo publicado y retirar los YAML~~: hecho (el motor solo lee lo publicado; los YAML se borraron el 11 de
  noviembre de 2026).
- ~~Ejecutar las pruebas del panel en el CI~~: el trabajo `panel` de `.github/workflows/ci.yml` corre tipos, pruebas e integración.
- Telegram, la API oficial de Meta y el chat web en Canales (Fase 5 de `docs/plan-v1.md`).

## Limitaciones conocidas

- Abrir el mismo negocio en dos pestañas es seguro, pero la segunda en guardar debe recargar: no se combinan los cambios.
- La foto de perfil y el menú de la cuenta solo existen con cuentas (en la nube); el panel local no tiene cuentas.
