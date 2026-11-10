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
| API local | Recibe las solicitudes, llama al servicio, traduce sus errores y confirma el resultado. Solo usa `BusinessConfigService`, que es quien valida con el contrato: ni base de datos, ni YAML, ni motor (salvo la importación, que lee los YAML) |
| BusinessConfig v1 | Contrato central: modelos, esquema, validaciones, compilador. El panel recibe de aquí los tipos generados y el esquema |
| Persistencia | Versiones inmutables y datos de pago cifrados en SQLite |

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

Cada sección del Asistente IA se arma con `SettingsGroup` y `SettingsCard` (`components/ui/SettingsCard.tsx`): un bloque «Lo esencial» y
otro de opciones para afinar, en una cuadrícula de dos columnas que pasa a una en el celular. Cada tarjeta tiene ícono, color, título y
para qué sirve; las avanzadas son plegables (elemento `<details>`, accesible por teclado) y al abrirlas ocupan todo el ancho. `Card` con
`icon` se dibuja igual, así los formularios existentes no cambian de estructura. El resumen (`features/overview`) muestra cada sección
con su estado, sus datos clave y el acceso a probar y publicar; es la entrada desde el menú.

### D8c — Plantillas para empezar un negocio

Crear un negocio empieza por elegir cómo: «Empezar de cero» (la primera opción, que no es una plantilla) o una plantilla de
`GET /api/business-templates`. Las plantillas viven en el servidor (`project/config/business-templates/*.json`), validadas contra el
contrato al arrancar la API (`business_config_application/templates.py`, `domain/business_config/templates.py`); el panel solo recibe
título, descripción e ícono, y `POST /api/businesses` con `template` guarda el primer borrador. Al abrirse, el resumen avisa que hay
que cambiar los ejemplos y agregar los medios de pago: nada se publica solo.

### D8d — Canales: WhatsApp por código QR

Canales muestra WhatsApp con su logo y dos formas de conectarlo: código QR (lista) y la API oficial de Meta (próximamente, el mismo
contrato de canal con otro conector). El negocio pega la dirección de su servidor de uazapi y un token: el de su instancia o el de
administrador del servidor, con el que la API crea la instancia del negocio. El token se guarda cifrado y nunca vuelve al panel (solo
sus últimos caracteres). Al guardar se pide el QR y la pantalla pregunta el estado cada 3 segundos hasta que lo escaneen; a los dos
minutos ofrece generar otro.

`features/channels` usa `useChannels()` (`state/channelsContext.ts`), que cuelga del negocio abierto (`BusinessWorkspace`); el tipo
vive en `domain/channels/types.ts` y el contrato en `repositories/channels.ts`, con su implementación en
`infrastructure/api/apiChannels.ts` (`/api/businesses/{slug}/channels/whatsapp`). En las pruebas, `createMemoryWhatsApp` de
`test/fakes.ts` simula el servidor. Telegram y el chat web aparecen como «Próximamente»; Instagram se retiró.

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

- Autenticación y autorización multiusuario (Fase 3), antes de cualquier despliegue en la nube.
- API y persistencia en la nube (Fase 3): otra implementación de los mismos contratos.
- Integrar el motor con lo publicado y retirar los YAML (Fase 4). Hasta entonces, algunos avisos describen lo que el motor hará al
  conectarse.
- Ejecutar las pruebas del panel en el CI, que hoy no las incluye.

## Limitaciones conocidas

- Abrir el mismo negocio en dos pestañas es seguro, pero la segunda en guardar debe recargar: no se combinan los cambios.
- La foto de perfil solo existe en el camino de autenticación real, que hoy no se usa.
