# Arquitectura del panel (`apps/admin-web`)

Estado: base refactorizada, **sin conexión al motor ni a ningún servidor**. Todo se guarda en el
navegador mediante implementaciones locales de contratos asíncronos.

## Capas

| Carpeta | Responsabilidad | Puede importar |
|---|---|---|
| `lib/` | Utilidades puras genéricas (texto, formato, ids) | — |
| `domain/` | Modelo, reglas y validaciones puras (sin React ni navegador) | `lib` |
| `repositories/` | Contratos asíncronos de persistencia y autenticación, y su error tipado | `domain`, `lib` |
| `infrastructure/` | Implementaciones concretas: `browser/` (localStorage) y `local/` (repositorio de configuración y acceso abierto) | `repositories`, `domain`, `lib` |
| `adapters/` | Traducción provisional al formato del motor y chequeo de su contrato mínimo | `domain`, `lib` |
| `state/` | Proveedores y hooks de React: sesión, configuración, estados de carga y guardado, operaciones | `repositories`, `domain`, `lib` |
| `components/ui/` | Interfaz genérica; **no conoce el dominio** (tipos propios, compatibles estructuralmente) | `lib` |
| `components/brand/` | Logotipo | — |
| `components/config/` | Piezas visuales ligadas al modelo de configuración | `ui`, `domain`, `lib`, `navigation` |
| `navigation/` | Rutas y definición del recorrido (sin componentes) | `domain`, `lib` |
| `layout/` | Estructura del panel: barra lateral, barra superior, menú de usuario, paginador, pantallas de carga y error, protección ante errores de renderizado (`ErrorBoundary`) | `ui`, `brand`, `config-ui`, `state`, `navigation`, `domain`, `lib` |
| `features/<x>/` | Pantallas, formularios y hooks de cada funcionalidad. **Sin imports entre funcionalidades** | `ui`, `brand`, `config-ui`, `layout`, `state`, `navigation`, `domain`, `lib` |
| `app/` | Composición: elige implementaciones (`compositionRoot.ts`), rutas, guardas de sesión y espacio de trabajo por cuenta | todo |
| `test/` | Utilidades de prueba, servicios falsos, datos ficticios y la prueba de arquitectura | todo |

Las reglas se verifican automáticamente en `src/test/architecture.test.ts` (capas permitidas,
imports entre funcionalidades y dependencias circulares) a partir de los imports reales. Para que
esa prueba vea siempre los archivos actuales, `vite.config.ts` desactiva la caché persistente de
módulos de Vitest (`fsModuleCache: false`); con ella activa, la lista de archivos quedaba congelada
y una violación nueva pasaba inadvertida (comprobado con archivos de prueba temporales).

## Principios

- **Un solo punto de elección de implementaciones:** `app/compositionRoot.ts`. Las pantallas y el
  estado solo conocen contratos (`repositories/`).
- **Contratos asíncronos.** `ConfigRepository` y `AuthService` devuelven promesas y rechazan con
  errores tipados (`PersistenceError`, `AuthError`), para poder sustituir el navegador por una API
  sin reescribir pantallas ni reglas.
- **Nada se da por guardado sin confirmación.** El estado de guardado (`idle`, `saving`, `saved`,
  `error`) solo pasa a `saved` cuando el repositorio resolvió; un fallo se muestra con opción de reintentar.
- **No se sobrescriben datos ilegibles.** Si lo guardado está dañado, se informa y el usuario decide;
  nunca se reemplaza en silencio por una configuración vacía.
- **Operaciones con nombre.** Las pantallas usan las acciones del contexto (`useConfigActions()` o
  `useConfig().actions`); las transformaciones son funciones puras en `domain/config/operations.ts`.
  Ya no existe un reducer con acciones expuestas a la interfaz.
- **Carga y errores explícitos.** Sesión y configuración tienen estados de carga y error con
  pantallas propias (`layout/StatusScreen.tsx`); un fallo de renderizado muestra `ErrorBoundary`
  (global y por sección, que se reinicia al cambiar de ruta).

## Registro de decisiones

### D1 — Eliminar la autenticación local con contraseña (`localAuthService`, `passwordHasher`)

- **Contexto:** verificaban contraseñas en el navegador (PBKDF2 con Web Crypto). Desde que se adoptó
  el acceso abierto, ninguna ruta de la aplicación los usaba: solo su propia prueba, los servicios
  falsos de prueba y dos comentarios.
- **Problema:** comprobar contraseñas en el cliente no es una autenticación segura (quien accede al
  navegador accede a los datos) y mantenerlo sugiere una protección que no existe.
- **Comprobación previa:** búsqueda de referencias en código, pruebas y documentación. Sus claves de
  almacenamiento (`accounts.v1`, `session.v1`) ya no las lee ninguna parte de la aplicación, de modo
  que eliminar el código no vuelve inaccesible ningún dato en uso.
- **Decisión:** eliminarlos. El contrato `AuthService` conserva la capacidad `verifiesCredentials` y
  la contraseña opcional para la futura autenticación real en servidor. Las pruebas usan un servicio
  falso en memoria que sí verifica credenciales, para cubrir ese camino de la interfaz.

### D2 — El acceso abierto se identifica en la interfaz

Con `verifiesCredentials = false` la interfaz no pide contraseña y muestra permanentemente que el
acceso es local y no está verificado. No se presenta como autenticación real.

### D3 — Adaptador al motor provisional

`adapters/` traduce la configuración al formato que hoy leen los YAML del motor, pero **el contrato
no está aprobado**: se revisará tras la corrección de los YAML. El adaptador no se usa desde la
interfaz. `translateToEngine` rechaza configuraciones con errores, verifica el contrato mínimo
conocido y devuelve avisos por cada dato descartado, fusionado o que el motor actual no consume.

### D4 — Limpieza explícita al cambiar el tipo de una cuenta de transferencia

Al cambiar el tipo (por ejemplo, de Nequi a cuenta bancaria) se borran los datos propios del tipo
anterior (`changeTransferMethodType`). Solo ocurre por esa acción explícita: los datos ya guardados
no se modifican al cargarlos.

## Pendiente para la siguiente fase (no implementado)

- Contrato definitivo entre el panel y el motor, tras revisar y corregir los YAML y comprobar qué
  campos usa realmente el motor.
- Conexión mediante API e integración con el backend.
- Persistencia real por negocio (implementación remota de `ConfigRepository`).
- Autenticación real en servidor (implementación de `AuthService` con `verifiesCredentials = true`).
- Publicar o aplicar configuraciones en el motor.
- Cambios en el motor para consumir los campos que hoy ignora (ver avisos del adaptador y
  `domain/config/engineUsage.ts`).

## Limitaciones conocidas (aceptadas en esta fase)

- La sesión no se sincroniza entre pestañas del mismo navegador.
- Cada cambio guarda la configuración completa; con una API conviene agrupar guardados.
- El acceso abierto no protege datos: cualquiera con acceso al navegador puede verlos o borrarlos.
- La foto de perfil se guarda como data URL en el navegador; con servidor debería ir a un almacén
  de archivos.
