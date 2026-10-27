# Panel de configuración del asistente (`apps/admin-web`)

Interfaz web para que un negocio cree su cuenta y configure su asistente de ventas sin editar YAML.

> **Estado actual: base de frontend, sin conexión.** El panel **no está conectado** al motor
> (`project/`), a ninguna API ni a la base de datos, y **no está listo para producción**. No lee
> ni escribe los YAML de `project/config/`. Las cuentas, la sesión y la configuración se guardan
> en el `localStorage` de cada navegador mediante implementaciones locales de contratos
> asíncronos (ver [docs/architecture.md](docs/architecture.md)).

## Ejecutar

```bash
cd apps/admin-web
npm install
npm run dev        # http://localhost:5173
npm test           # pruebas (Vitest + Testing Library, jsdom), incluida la prueba de arquitectura
npm run typecheck  # TypeScript estricto
npm run build      # typecheck + build de producción en dist/
npm run preview    # sirve dist/ en http://localhost:4173
```

Requiere Node 20 o superior (verificado con Node 22). `run_local.bat` / `run_local.sh` en la raíz
del repositorio también lo inician y abren el navegador.

## Qué funciona hoy

| Funcionalidad | Estado |
|---|---|
| Configuración guiada (negocio, productos, pagos, atención, mensajes, revisión) | Funciona; validación en vivo |
| Guardado | Automático en este navegador. "Guardado" solo aparece cuando el almacenamiento confirma; si falla, se muestra "No se pudo guardar" con opción de reintentar |
| Datos guardados dañados | Se informan y **no se sobrescriben**; el usuario puede reintentar o descartarlos explícitamente |
| Cuentas | **Acceso local sin verificación**: se entra solo con el correo, sin contraseña. La pantalla de entrada lo indica siempre. No es autenticación real |
| Perfil | Nombre y foto (JPG, PNG, WebP o GIF de hasta 5 MB, recortada a 256×256), cierre de sesión, borrado de la configuración |
| Cuentas de transferencia | Al cambiar el tipo se borran los datos del tipo anterior |
| Traducción al motor (`adapters/`) | Implementada y probada, pero **provisional y sin usar**: no se llama desde la interfaz |
| Errores de renderizado | Se muestran en una pantalla de error con opción de reintentar, en vez de dejar la página en blanco |

## Qué todavía no funciona

- No hay servidor: los datos viven solo en el navegador donde se crearon (no se comparten entre
  equipos ni navegadores) y cualquiera con acceso a ese navegador puede verlos o borrarlos.
- No hay autenticación real, recuperación de contraseña ni verificación de correo.
- Nada se publica ni se aplica en el motor; marcar un canal (WhatsApp, Telegram) no lo conecta.
- La sesión no se sincroniza entre pestañas abiertas del mismo navegador.

## Estructura

Ver [docs/architecture.md](docs/architecture.md): capas, reglas de dependencia (verificadas por
`src/test/architecture.test.ts`), decisiones y pendientes.

| Carpeta | Responsabilidad |
|---|---|
| `src/app/` | Composición: elección de implementaciones (`compositionRoot.ts`), rutas y guardas de sesión |
| `src/features/<x>/` | Pantallas y formularios de cada funcionalidad |
| `src/layout/` | Estructura del panel, pantallas de carga y error, protección ante errores |
| `src/components/ui/` | Interfaz genérica, sin dependencias del dominio |
| `src/domain/` | Modelo, reglas, validaciones y operaciones puras |
| `src/repositories/` | Contratos asíncronos de persistencia y autenticación |
| `src/infrastructure/` | Implementaciones locales (localStorage) de esos contratos |
| `src/state/` | Proveedores y hooks de sesión y configuración |
| `src/adapters/` | Traducción provisional al formato actual de los YAML del motor |
| `src/lib/` | Utilidades puras (texto, formato, ids) |
| `src/test/` | Servicios falsos, datos ficticios de prueba y prueba de arquitectura |

## Adaptador al motor (provisional)

`translateToEngine` (`src/adapters/translateToEngine.ts`) traduce `AssistantConfig` al formato de
las cinco secciones que leen hoy los YAML. **El contrato no está aprobado** y se revisará tras
corregir los YAML. Por eso:

- Rechaza configuraciones con errores de validación (salvo `allowInvalid`).
- Comprueba el contrato mínimo que hoy exige el motor (`engineContract.ts`).
- Devuelve avisos (`engineNotices.ts`) por cada dato que no se envía, que se fusiona (categorías
  que se escriben igual sin tildes ni mayúsculas) o que el motor actual recibe pero no usa
  (nombre comercial, descripción, tono, reglas, preguntas y, en catálogo, nombres y precios).

Decisiones actuales de la traducción: los elementos no disponibles no se envían; el bloque de pago
se repite en cada plan (o en `catalog.payment`); `capabilities.channels` replica
`business_channels.allowed`; las ventanas de conversación se omiten; largo de respuesta: corto = 60,
medio = 75, largo = 100 palabras.

## Pendiente (siguiente fase)

Ver la sección "Pendiente" de [docs/architecture.md](docs/architecture.md): contrato definitivo con
el motor tras revisar los YAML, API e integración con el backend, persistencia real por negocio,
autenticación en servidor, publicación de configuraciones y cambios en el motor para usar los
campos que hoy ignora. Al desplegar como SPA (por ejemplo, en Vercel) hará falta una regla de
reescritura hacia `index.html`.
