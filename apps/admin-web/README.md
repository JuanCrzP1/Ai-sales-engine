# Panel de administración (`apps/admin-web`)

Interfaz web para administrar varios negocios sin editar YAML ni código: identidad, productos y servicios, precios y
promociones, personalidad e instrucciones del asistente, preguntas frecuentes, políticas y medios de pago.

El panel edita **BusinessConfig v1** a través de una **API local** (`project/app/admin_api`) y todo se guarda en una base
**SQLite** en este equipo. No guarda nada en el navegador.

> **Solo funciona en este equipo.** La API no tiene inicio de sesión y por eso escucha únicamente en `127.0.0.1`. La
> autenticación y la autorización multiusuario deben incorporarse antes de desplegarla en la nube.
>
> **Todavía no llega a los clientes.** El motor comercial sigue leyendo sus YAML. Publicar aquí deja una versión oficial
> del negocio, pero el asistente en funcionamiento no la usa hasta que se integre (Fase 4).

## Ejecutar

Los únicos lanzadores del sistema son `run_local.bat` (Windows) y `run_local.sh` (Linux y macOS). Encienden el motor con el
`.env`, ngrok, Telegram y la API de este panel; cuando esa API responde, arrancan la interfaz y se abre
<http://127.0.0.1:5180>. Si la API no responde, la interfaz no se abre y el motor sigue arrancando.
La interfaz usa el 5180, y no el 5173 que Vite toma por defecto, para convivir con otros proyectos de Vite en el mismo equipo.

Requisitos: el entorno de Python del proyecto en `.venv`, Node 24 LTS (`.nvmrc`; también sirven 22.22+ y 26+, ver `engines` en `package.json`), y lo que ya necesita el motor (`ngrok` y `.env`).
`run_local.sh` además se detiene al empezar si PostgreSQL no está disponible.

Para detener todo: `bash run_local_stop.sh`, desde Git Bash en Windows.

Esos lanzadores abren también el túnel de `ngrok` y Telegram. Para administrar los negocios sin encender el motor ni exponer nada,
basta con la API y la interfaz, cada una en su consola, desde la raíz del repositorio y con `.venv` activo:

```bash
python scripts/run_admin_api.py          # API en 127.0.0.1:8010. También crea las tablas y la clave si faltan
npm --prefix apps/admin-web run panel    # interfaz en http://127.0.0.1:5180
```

Son las mismas órdenes en Windows y macOS. No uses `run dev -- --port ...` desde PowerShell: su `npm.ps1` pierde el `--`, Vite toma el puerto por carpeta raíz y arranca sin configuración, sin proxy y sin el panel. Para usar los mismos datos en los dos equipos: `docs/operations.md`, «Trabajar Desde Windows Y macOS».

Se detienen igual, con `bash run_local_stop.sh`, que reconoce la interfaz por el `--port 5180` del script `panel`. La interfaz llega a la API por el proxy
de Vite (`/api`), en el mismo origen: no hay CORS y el navegador no habla con nadie más.

**Clave de cifrado.** Cifra los datos de pago. La primera vez se crea sola en `.ai-sales-engine/business_config_secrets.key`,
dentro de la carpeta del usuario y fuera del repositorio, y después se reutiliza siempre. Guarda una copia: sin ella esos datos
no se pueden leer. `BUSINESS_CONFIG_SECRETS_KEY` tiene prioridad si está definida. Si la clave falta y la base ya tiene datos
cifrados, la API no arranca y lo explica, en vez de crear otra que los dejaría ilegibles. Cómo respaldarla y recuperarla:
[docs/operations.md](../../docs/operations.md).

La base se crea sola en `project/data/business_config.sqlite3` (ignorada por git). Otro archivo:
`BUSINESS_CONFIG_DATABASE_URL`. Otro puerto para la API: `ADMIN_API_PORT` (8010 por defecto).

## Qué se puede hacer

| Sección | Qué administra | Sección del contrato |
|---|---|---|
| Tus negocios | Crear, abrir, eliminar (hay que escribir el identificador) e importar los YAML existentes | negocios del almacén |
| Mi negocio | Nombre comercial, marca, a qué se dedica, descripción, propuesta de valor, ubicación, cobertura, modalidades, horarios, cliente ideal, forma de venta | `identity`, `offer.model` |
| Productos y servicios | Planes o catálogo, categorías, descripciones, características, precios por moneda, disponibilidad, variantes y existencias, entrega y agenda | `offer`, `inventory`, `fulfillment` |
| Pagos y cierre | Enlace y cuentas, promociones, condiciones, políticas, financiación, formas de cierre, datos que se piden y acciones | `payments`, `terms`, `capabilities` |
| Cómo atiende | Personalidad, tono, estilo, instrucciones comerciales, recomendaciones, preguntas frecuentes, estrategia avanzada | `response_style`, `sales`, `knowledge`, `features` |
| Mensajes y canales | Bienvenida, mensajes de pago, otros mensajes, canales y restricciones | `messages`, `capabilities` |
| Revisión y publicación | Lo que falta, avisos del servidor, resumen, publicar, volver a la versión anterior, historial y restaurar | versiones del almacén |

Los campos del contrato sin pantalla propia se generan desde el esquema que publica la API, en las secciones plegables.

### Cómo se comporta

- **Guardar es explícito.** Cada guardado crea una versión inmutable y exige un documento válido, así que no hay guardado
  automático. «Guardado» solo aparece cuando el servidor aceptó el documento. Salir con cambios sin guardar pregunta qué hacer.
- **Un negocio nuevo no queda guardado hasta que cumple el contrato**: datos del negocio y al menos un producto o servicio
  disponible. El negocio sí queda registrado desde que se crea.
- **El servidor es la autoridad.** El panel avisa mientras se escribe, pero al guardar decide el contrato, y sus errores se
  muestran en el mismo campo.
- **Lo abierto no se pierde al cambiar de sección.** Un plan o producto a medio escribir sigue en su formulario al volver. Para
  guardar hay que aplicarlo a la lista o cancelarlo: el panel lo explica en vez de dejarlo fuera en silencio.
- **Datos de pago: se reconocen, no se leen.** El servidor los cifra y nunca devuelve un valor completo, solo su estado y una
  parte para reconocerlo (`••••4567`, o el servidor de un enlace). «Métodos configurados» muestra cada método, su banco, tipo de
  cuenta y etiqueta, y si está activo. Editar lo descriptivo no toca el dato cifrado, desactivar un método lo conserva y
  reemplazar es explícito: con el campo vacío se conserva el dato guardado. Cada valor nuevo recibe una referencia propia, de
  modo que editar un borrador no altera lo publicado y cada versión conserva los suyos.
- **Si el negocio cambió en otra pestaña**, guardar se rechaza en vez de pisar esos cambios.

## Qué no hace todavía

- Inicio de sesión y usuarios: fase de nube. Las pantallas de cuenta siguen conectadas al contrato `AuthService`, pero con el
  acceso local no se muestran.
- Hacer llegar lo publicado a los clientes: Fase 4.
- Conectar canales: marcar WhatsApp o Telegram solo indica por dónde atiende el negocio.
- Teléfono y correo de contacto del negocio: BusinessConfig v1 no tiene esos campos; la información de contacto que contempla
  es ubicación, horarios y canales.

## Pruebas

```bash
npm run typecheck         # TypeScript estricto
npm test                  # interfaz, reglas y arquitectura, con un backend en memoria
npm run test:integration  # interfaz real + API real + BusinessConfig + SQLite temporal
npm run build             # typecheck y build de producción
pytest tests/test_admin_api.py   # API, desde la raíz del repositorio
```

`npm run test:integration` usa el Python de `.venv` (u otro con `ADMIN_API_PYTHON`), una base temporal y una clave generada en
cada ejecución. Reinicia la API de verdad y no usa `.env`, ni la base definitiva, ni servicios externos, ni modelos de IA.

## Estructura

Capas, reglas de dependencia (verificadas por `src/test/architecture.test.ts`) y decisiones:
[docs/architecture.md](docs/architecture.md). Contrato: [docs/business-config.md](../../docs/business-config.md).

| Carpeta | Responsabilidad |
|---|---|
| `src/app/` | Composición: elección de implementaciones (`compositionRoot.ts`), rutas y espacio de trabajo de cada negocio |
| `src/features/<x>/` | Pantallas y formularios de cada sección |
| `src/layout/` | Estructura del panel, estado del guardado, formularios generados, pantallas de carga y error |
| `src/components/` | Interfaz genérica (`ui/`), logotipo (`brand/`) y piezas ligadas a la configuración (`config/`) |
| `src/contracts/` | Tipos generados desde el contrato: no se editan a mano |
| `src/domain/` | Operaciones sobre el documento, validación anticipada y lectura del esquema: puro, sin React |
| `src/repositories/` | Contratos de persistencia y autenticación |
| `src/infrastructure/` | Implementaciones: cliente de la API (`api/`) y acceso local sin autenticación (`local/`) |
| `src/state/` | Proveedores y hooks de sesión, negocios y configuración |
| `src/test/` | Backend en memoria, documentos ficticios, prueba de arquitectura y pruebas de integración (`integration/`) |
| `legacy/` | Código anterior, sin uso y fuera de la compilación ([legacy/README.md](legacy/README.md)) |
