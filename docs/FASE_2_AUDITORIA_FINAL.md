# Fase 2: Auditoría Final

> **Documento histórico (6 de noviembre de 2026).** Audita el panel cuando solo funcionaba en este equipo y los negocios todavía
> se importaban de sus YAML. Desde entonces el panel corre en la nube con cuentas, los YAML se retiraron (11 de noviembre de 2026)
> junto con `migrate_tenants_to_contract.py` y su `migration-report.md`, y los negocios de ejemplo son JSON. Estado actual:
> `docs/plan-v1.md`.

Fecha: 2026-11-06. Estado auditado: rama `main`, commit base `4b64485`, con todo el trabajo de la fase sin confirmar. Este documento no contiene datos de pago, claves ni secretos.

## Resumen Ejecutivo

BusinessConfig v1 y el dashboard funcionan localmente en Windows, con persistencia real en SQLite, y están preparados para macOS. Todas las pruebas ejecutables pasan sin fallos: 1117 de Python en tres configuraciones, 180 de Vitest, 23 de integración y los recorridos en navegador. Los 9 negocios compilan y los 46 datos de pago siguen cifrados y se descifran con la clave actual.

**No hubo ninguna ejecución en un Mac real**, porque no hay uno disponible en este equipo. La compatibilidad con macOS está implementada y tiene evidencia indirecta, pero no se puede marcar como verificada. Por eso el dictamen es **FASE 2 NO COMPLETADA**, con ese único bloqueo. Se levanta con la comprobación de «Bloqueo Y Cómo Levantarlo».

Dos computadores **no** comparten datos. Cada uno tiene su propio archivo SQLite, y la información centralizada corresponde a la Fase 3.

## Arquitectura Final Implementada

```text
Navegador -> Vite (127.0.0.1:5180, proxy /api) -> API FastAPI (127.0.0.1:8010) -> BusinessConfigService
          -> repositorio y almacén de datos de pago -> SQLite (project/data/business_config.sqlite3)
```

| Capa | Ubicación | Responsabilidad |
|---|---|---|
| Dominio | `project/app/domain/business_config/` | Contrato, validación, compilación, diagnósticos, máscaras |
| Aplicación | `project/app/business_config_application/` | Casos de uso y puertos, sin detalles de base de datos |
| Persistencia | `project/app/infrastructure/business_config/` | Repositorio, tablas, almacén cifrado, clave de cifrado |
| API | `project/app/admin_api/` | HTTP local, sin documentación pública ni CORS |
| Arranque | `scripts/run_admin_api.py` | Composición y puerto. Host fijo a `127.0.0.1` |
| Secretos | `scripts/local_secrets.py`, `secrets.local.env` | Llevar los secretos de un equipo a otro, sin mostrarlos |
| Panel | `apps/admin-web/` | React con tipos generados desde el contrato; no guarda datos en el navegador |

Las reglas entre capas las vigilan `tests/test_business_config_architecture.py` y `apps/admin-web/src/test/architecture.test.ts`.

**Preparación para la Fase 3.** La aplicación solo conoce puertos, y la persistencia toma su URL de `BUSINESS_CONFIG_DATABASE_URL`. La migración `project/db/migrations/0001_business_config_store.sql` está preparada, y el panel habla solo con la API. Ver «Limitaciones Que Corresponden A La Fase 3».

## Estado De BusinessConfig v1

- Contrato estricto (`extra="forbid"`), con esquema `project/config/contracts/v1/business-config.schema.json` y tipos `apps/admin-web/src/contracts/businessConfig.v1.ts`, ambos generados. Los generadores con `--check` no encuentran diferencias, incluidos los 18 documentos de los negocios.
- Los datos de pago no van en el documento: solo referencias `secret_store:` a valores cifrados con Fernet. Versión y datos se guardan en una misma transacción.
- Las versiones son inmutables. Guardar crea una versión; publicar exige que compile; restaurar crea un borrador.
- El motor **no** usa BusinessConfig todavía: sigue con sus YAML hasta la Fase 4, y lo publicado no llega a los clientes.

## Funcionalidades Del Dashboard Verificadas

Comprobadas en Microsoft Edge real contra la API y SQLite reales: 126 comprobaciones con datos ficticios y 46 sobre una copia de la base real.

| Funcionalidad | Resultado |
|---|---|
| Crear y consultar negocios | Funciona. También rechaza identificadores repetidos y datos incompletos |
| Editar y guardar | Funciona. El guardado se confirma solo cuando el servidor acepta |
| Recuperar tras reiniciar | Funciona, con un navegador limpio |
| Productos y servicios | Crear, editar, pausar, activar y eliminar |
| Categorías, precios y promociones | Crear, renombrar sin afectar productos, quitar las que no se usan y editar precios |
| Personalidad e instrucciones | Se guardan y se recuperan |
| Preguntas frecuentes | Crear, editar y eliminar |
| Políticas y métodos de pago | Políticas, enlace, cuentas, activar, desactivar, reemplazar y quitar |
| Validación antes de guardar | Producto, promoción, celular y enlace inválidos no se guardan. El servidor también rechaza lo que no pase por el panel |
| Versiones e historial | Funciona. Un guardado desde una pestaña vieja se rechaza con 409 |
| Publicar, volver atrás y restaurar | Funciona, con sus datos de pago originales |
| Aislamiento entre negocios | Un documento ajeno se rechaza, y cambiar un negocio no altera a los otros |
| Almacenamiento en el navegador | `localStorage` y `sessionStorage` vacíos. El código del panel no los usa |

## Persistencia Y Recuperación

- **Reinicio con datos ficticios:** se apagaron API y panel y se abrieron de nuevo con un navegador limpio. Configuración e historial quedaron idénticos, leídos también directamente del archivo SQLite.
- **Sobre una copia de la base real, con la clave real:** se editó, se reemplazó un dato por uno ficticio, se publicó, se reinició y se restauró. Un CRUD completo con un negocio ficticio terminó con integridad `ok`, 0 claves foráneas rotas y 0 filas huérfanas.
- **Sobre la base real, solo lectura:** dos arranques con la parada oficial entre ellos. Contrato, negocios, configuración e historial son iguales antes y después, y el archivo queda **idéntico byte a byte**.
- **Integridad de cada negocio:** guardar un cambio en los negocios reales de la copia solo alteró lo editado; el resto de cada documento quedó igual.

## Compatibilidad Windows Y macOS

| Punto | Resultado | Cómo se comprobó |
|---|---|---|
| Ejecución en Windows | **Comprobada** | Todas las suites, y un equipo nuevo simulado: otra carpeta, otro perfil de usuario y dependencias desde cero (31/31) |
| **Ejecución en un Mac real** | **No ejecutada** | No hay Mac disponible. Es el bloqueo de este dictamen |
| Ejecución en Linux | No ejecutada | La confirmará el CI tras el push. No es requisito de esta fase |
| Rutas | Sin dependencias de Windows | `Path.home()` y rutas relativas al repositorio; 0 referencias a rutas de Windows en el código de BusinessConfig; la base no guarda rutas |
| Dependencias de Python | Disponibles | Descarga simulada para Apple Silicon, Python 3.13 y 3.11: 40 paquetes, 8 nativos para Mac, con las versiones exactas |
| Dependencias del panel | Disponibles | `npm ci --os=darwin --cpu=arm64` correcto, con sus binarios para `darwin-arm64` |
| Variables de entorno | Documentadas | `docs/operations.md`; `secrets.local.env.example` no tiene valores |
| Arranque y parada | Lógica comprobada | Orden del panel en PowerShell, cmd y Git Bash (14/14). `run_local.sh` y la rama de macOS de `run_local_stop.sh`, simuladas sin encender el motor (13/13) |
| Scripts | Compatibles | Sin construcciones de bash 4 ni herramientas exclusivas de GNU; `shellcheck` sin avisos; finales de línea LF |
| SQLite | Portable | Mismo archivo en ambos sistemas; una sola copia, sin archivos auxiliares con el sistema apagado |
| Secretos | Portables | `secrets.local.env` no depende de la carpeta del usuario. En Windows, la clave se lee de ese archivo y descifra 46 de 46 en un perfil sin clave |

**Sincronización:** no existe. Cada equipo tiene su archivo SQLite y la última copia reemplaza a la otra. Edita en un solo equipo a la vez.

## Estado De Seguridad Y Cifrado

**Prueba de sockets.** El control positivo dio (1, 4) por un error de la propia prueba: su servidor hacía `listen(1)` sin `accept()`, la primera conexión llenaba la cola y las demás se rechazaban. No era el firewall. Se demostró cambiando el orden de las interfaces: siempre pasaba solo la primera. Corregido, el resultado es:

| Control | IPv4 | IPv6 |
|---|---|---|
| Servidor abierto a todas las interfaces (debe responder en todas) | (4, 4) | (7, 7) |
| Servidor solo en loopback (debe responder solo por loopback) | (0, 4) | (1, 7), `::1` |
| **API y dashboard reales** (no deben responder) | (0, 4) | (0, 7) |

La prueba quedó en el repositorio, sin depender del sistema operativo: `tests/test_local_network_binding.py`.

- **Loopback:** la tabla de sockets de Windows muestra `127.0.0.1` y nada más en los puertos 8010 y 5173 (el panel pasó después al 5180, con la misma dirección). `netstat` no sirve en este equipo: muestra unos 10 de 50 sockets. Estas pruebas se hacen desde el propio equipo; la comprobación desde otro está en «Bloqueo Y Cómo Levantarlo».
- **Host y Origin ajenos:** rechazados por la API y a través del proxy del panel. La API no publica documentación y sus respuestas no se guardan en caché.
- **Aislamiento multiempresa:** 9 pruebas específicas, más los recorridos sobre la copia real. Ninguno de los 9 negocios cambia cuando se opera sobre otro.
- **Cifrado:** los 46 datos están cifrados con Fernet en la base real, y ningún valor aparece en claro en el archivo.
- **Descifrado:** 46 de 46 con la clave actual, tanto con `cryptography` 46 como con la 50 de `requirements.txt`.
- **Enmascaramiento:** ningún dato de pago completo en respuestas, en las 63 pantallas reales, en la consola del navegador ni en los registros.
- **Clave:** no se generó otra ni se sobrescribió; el archivo original es idéntico al inicial. `secrets.local.env` la contiene exacta, legible solo por el usuario, e ignorada por git. Ninguno de los archivos que subiría git contiene la clave ni los secretos del `.env`.
- **Respaldo de la clave:** **aplazado por decisión del propietario**. Hoy solo existe en este equipo. Si se pierde, los datos cifrados no se recuperan; se pueden reconstruir desde los YAML únicamente mientras nadie edite pagos en el panel. Copiar `secrets.local.env` al Mac crea la primera copia externa.

## Revisión Del Repositorio

**Comprobado:**

| Hallazgo | Medición |
|---|---|
| Visibilidad | Público, accesible sin credenciales, sin bifurcaciones |
| Valores de pago en lo publicado | 10 valores distintos en 20 de 452 archivos de `origin/main`: 9 YAML, 5 del laboratorio, 3 pruebas y 3 más (`apps/admin-web/src/domain/config/operations.test.ts`, `apps/admin-web/src/features/payments/TransferMethodsForm.tsx`, `scripts/reset_conversation_state.py`). También están en el historial |
| Lo que subiría `git add -A` | 26 de 571 archivos con alguno de esos valores. Los añadidos son pruebas que repiten un mismo valor con forma de ejemplo, y uno de `legacy/` |
| Credenciales | `.env` nunca se versionó. Sin patrones de credenciales en lo publicado. `project/config/system/secrets.yaml` está publicado solo con campos vacíos o de ejemplo |
| Cinco archivos del laboratorio | `baseline_metrics.json`, `baseline_prompt.txt`, `candidate_metrics.json`, `candidate_prompt.txt` y `phase1_human_tuning_metrics.json`: con datos de pago, sin cambios desde mayo y no modificados |
| `apps/admin-web/legacy/` | 17 archivos sin seguimiento, del panel anterior. Nada los importa ni los compila. 6 usan `localStorage` y 1 contiene un valor de pago. `git add -A` los subiría |

**Necesita confirmación del propietario** (no se tocó nada):

1. Si los 10 valores son reales. Por su forma, unos 4 o 5 parecen de ejemplo, lo que no prueba nada.
2. Si el repositorio sigue público.
3. Si se sanean los archivos publicados y se reescribe el historial. Reescribirlo afecta a 13 commits, incluido `4b64485`. Los YAML no se pueden retirar antes de la Fase 4.
4. Si `legacy/` se elimina o se conserva. Mientras tanto, para no subirlo: `git add -A -- . ":!apps/admin-web/legacy"`.

## Resultado De Cada Suite De Pruebas

Sin modelo de IA, sin mensajes reales y sin el motor encendido. La red se bloqueó durante pytest, salvo este mismo equipo: 0 intentos de salida.

| # | Suite | Aprobadas | Fallidas | Omitidas |
|---|---|---:|---:|---:|
| 1 | Contrato BusinessConfig v1 | 291 | 0 | 0 |
| 2 | Validación: backend / panel | 221 / 29 | 0 | 0 |
| 3 | Backend y API | 221 | 0 | 0 |
| 4 | Dashboard: Vitest / integración / Edge ficticio / Edge sobre copia real / orden en 3 consolas | 180 / 23 / 126 / 46 / 14 | 0 | 0 |
| 5 | Persistencia SQLite | 126 | 0 | 0 |
| 6 | Aislamiento multiempresa | 9 | 0 | 0 |
| 7 | Cifrado y protección de datos | 108 | 0 | 1 |
| 8 | Historial, publicación y restauración | 28 | 0 | 0 |
| 9 | Compatibilidad: secretos y red / equipo nuevo / lanzadores simulados | 36 / 31 / 13 | 0 | 1 |
| 9 | **Compatibilidad: ejecución real en macOS** | **No ejecutada** | | |
| 10 | Reinicio y recuperación: pruebas / base real | 8 / 47 | 0 | 0 |
| 11 | Motor sin cambios: pruebas / réplica | 178 / prompts 9 de 9, respuestas 10 de 10 | 0 | 0 |
| 12 | YAML intactos | 45 de 45 | 0 | 0 |

Las suites comparten pruebas: el total es el de la suite completa.

| Suite completa de Python | Aprobadas | Fallidas | Omitidas | Pendientes de Fase 4 |
|---|---:|---:|---:|---:|
| `.venv`, Python 3.13, `cryptography` 46 | 1117 | 0 | 55 | 63 |
| Python 3.13, versiones exactas de `requirements-dev.txt` | 1117 | 0 | 55 | 63 |
| Python 3.11, versiones exactas de `requirements-dev.txt` | 1117 | 0 | 55 | 63 |

- **Omitidas:** 54 necesitan la clave del modelo y no corren para no gastar API; 1 comprueba permisos de macOS y Linux, y en esos sistemas la de Windows es la que se omite.
- **Pendientes:** las 63 están marcadas `xfail` en `test_business_config_engine_pending.py` y describen la integración de la Fase 4. Ninguna empezó a pasar.
- **Otras comprobaciones:** TypeScript sin errores, build correcto, respaldo y recuperación con clave ficticia 19/19.
- **Motor (11):** la réplica contra `6815ec5` da webhook y health iguales. La única diferencia es `POST /api/v1/simulate`, retirada por una orden de seguridad anterior.
- **YAML (12):** los 45 de negocios son idénticos a `HEAD`. Dos YAML de sistema, `bot_config.yaml` y `settings.yaml`, difieren en una línea cada uno: `enable_simulation_endpoint` pasó a `false` en esa misma orden anterior.
- **Reproducción:** lo de Python y Vitest se repite con las órdenes de `docs/operations.md` y `apps/admin-web/README.md`. Los recorridos en navegador y las pruebas sobre datos reales se ejecutaron con scripts temporales, que no forman parte del repositorio.

**Defectos encontrados y corregidos durante el cierre:**

| Defecto | Corrección |
|---|---|
| Los lanzadores de Unix no tenían permiso de ejecución en git: `./run_local.sh` habría fallado en macOS | Permiso añadido en el índice, sin commit, y prueba que lo vigila |
| En PowerShell, `npm.ps1` perdía el `--` de `run dev -- --port 5173`: Vite arrancaba sin configuración, sin proxy y sin panel | Script `panel`, sin `--`, que funciona en todas las consolas |
| El control positivo de red daba (1, 4) | Corregida la prueba, no el producto |
| La guía de macOS usaba `python`, que allí puede no existir, e indicaba mal la versión de Node | Corregida |
| `secrets_key.py` importaba `dotenv`, contra la regla de esa capa (introducido durante este mismo cierre) | La API lee solo la línea de la clave |

## Estado De Los Nueve Negocios

Leído por la API real sobre una copia de la base, con la clave de `secrets.local.env`:

| Negocio | Modalidad | Ofertas | Categorías | Promociones | Preguntas frecuentes | Métodos de pago | Datos descifrados | Versiones | Publicada | Compila | Avisos |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `agencia_viajes` | catálogo | 3 | 2 | 0 | 0 | 4 | 4 de 4 | 1 | 1 | Sí | 2 |
| `asesor_ai_prod` | planes | 1 | 0 | 0 | 0 | 5 | 5 de 5 | 1 | 1 | Sí | 2 |
| `clinic` | planes | 1 | 0 | 0 | 0 | 5 | 5 de 5 | 1 | 1 | Sí | 1 |
| `demo` | planes | 2 | 0 | 0 | 0 | 10 | 10 de 10 | 1 | 1 | Sí | 2 |
| `ecommerce` | planes | 1 | 0 | 0 | 0 | 5 | 5 de 5 | 1 | 1 | Sí | 1 |
| `escuela_conduccion` | catálogo | 6 | 3 | 0 | 0 | 4 | 4 de 4 | 1 | 1 | Sí | 2 |
| `restaurant` | catálogo | 4 | 2 | 0 | 0 | 4 | 4 de 4 | 1 | 1 | Sí | 1 |
| `saas` | planes | 1 | 0 | 0 | 0 | 5 | 5 de 5 | 1 | 1 | Sí | 0 |
| `tienda_ropa` | catálogo | 2 | 2 | 0 | 0 | 4 | 4 de 4 | 1 | 1 | Sí | 3 |

**Total:** 9 de 9 compilan y 46 de 46 datos se descifran. La base real tiene integridad `ok` y 0 claves foráneas rotas.

Los 14 avisos no impiden compilar. Son incoherencias de los datos comerciales originales, que esta fase no modifica: cierre por enlace sin enlace (4), agenda sin horarios (3), recomendación de una oferta no disponible (3), entrega sin modalidad (2), sin canales de atención (1) y catálogo que contradice la oferta (1). Se ven en la revisión de cada negocio y puedes corregirlos desde el panel. Detalle: `project/config/contracts/v1/migration-report.md`.

## Archivos Creados Y Modificados Durante Esta Intervención

**En esta orden:**

| Archivo | Cambio |
|---|---|
| `docs/FASE_2_AUDITORIA_FINAL.md` | Nuevo: este documento |
| `apps/admin-web/package.json` | Script `panel` |
| `apps/admin-web/README.md` | Orden del panel y versión de Node |
| `docs/operations.md` | Orden del panel, `python3` y paquete de git |
| `README.md` | Enlace a esta auditoría |
| `tests/test_admin_api.py` | Pruebas del permiso de ejecución y de la orden del panel |
| `run_local.sh`, `run_local_stop.sh` | Solo el permiso de ejecución, preparado en el índice de git. Su contenido no cambió |

**En la orden anterior, del mismo cierre:**

- **Nuevos:** `scripts/local_secrets.py`, `secrets.local.env.example`, `tests/test_local_secrets.py`, `tests/test_local_network_binding.py`.
- **Modificados:** `.gitignore`, `.dockerignore`, `README.md`, `apps/admin-web/README.md`, `docs/operations.md`, `project/.env.example`, `project/app/infrastructure/business_config/secrets_key.py`, `pytest.ini`, `scripts/run_admin_api.py`, `tests/conftest.py`.
- **Ignorado por git:** `secrets.local.env`, con valores reales.

**No se modificó en este cierre:** motor, lógica de ventas, prompts, conversaciones, YAML, contenido de los lanzadores, base real, clave y resultados históricos del laboratorio.

**Estado de git:** rama `main`, sin commits ni push. Todo el trabajo de las Fases 1 y 2 sigue sin confirmar: 122 archivos modificados, 15 eliminados y 120 sin seguimiento. Solo el permiso de ejecución de dos archivos está preparado para commit.

## Riesgos Conocidos

| Riesgo | Estado |
|---|---|
| Repositorio público con valores de pago | Sin resolver; depende del propietario. Terminar el panel no lo soluciona |
| Clave sin respaldo externo | Aplazado por el propietario |
| `secrets.local.env` con secretos en claro | Ignorado por git y legible solo por el usuario. Debe tratarse como una contraseña |
| Dos copias de la base editadas a la vez | No hay sincronización: la última copia reemplaza a la otra |
| API local sin autenticación | Deliberado hasta la fase de nube. Cualquier programa que corra en el equipo puede usarla |
| Firewall del equipo Windows | Permite entrada a `python.exe` y `node.exe` en redes públicas: lo que protege al panel es escuchar solo en loopback. Otros programas del equipo sí escuchan en todas las interfaces |
| `.env` en Windows | Con permisos más abiertos que `secrets.local.env`. No se modificó |
| Motor | Hasta la Fase 4, los datos de pago siguen en YAML, prompts y `conversation_trace`, y `sender.py` y `whatsapp_webhook.py` imprimen tokens. `run_local.*` publica el motor por ngrok |
| CI | El job `integration` consume API en cada push si existe el secreto `OPENROUTER_API_KEY` en GitHub. El CI no ejecuta las pruebas del panel |
| `.venv` de Windows | 3 paquetes con versiones distintas de `requirements.txt`. La suite pasa con ambas |

## Limitaciones Que Corresponden A La Fase 3

- **Datos compartidos:** no existen. Hacen falta una base central y que los dos equipos la usen.
- **PostgreSQL:** `scripts/run_admin_api.py` rechaza a propósito cualquier base que no sea SQLite. La migración `0001_business_config_store.sql` **no se ha ejecutado en ninguna base**, y las pruebas no cubren particularidades de PostgreSQL.
- **Autenticación:** el panel no tiene. Debe existir antes de exponer la API fuera de loopback.
- **Publicaciones simultáneas:** en PostgreSQL, dos a la vez las detiene el índice único con un error 500, sin dañar datos; conviene responder 409.
- **Clave de cifrado en la nube:** debe ser la misma, y hay que definir dónde se guarda.
- **Neon y Vercel:** no iniciados, por orden.

## Instrucciones Para Instalar Y Ejecutar En Windows

**En este equipo ya está todo instalado.** Abre PowerShell, una consola para cada orden:

```powershell
cd C:\dev\ai-sales-engine
.\.venv\Scripts\Activate.ps1
python scripts/local_secrets.py check
python scripts/run_admin_api.py
```

```powershell
cd C:\dev\ai-sales-engine
npm --prefix apps/admin-web run panel
```

Abre <http://127.0.0.1:5180>. Para detener: `Ctrl+C` en cada consola, o `bash run_local_stop.sh` desde Git Bash.

**En otro equipo con Windows**, con Python 3.13, Node 20.19 o 22.12 en adelante y Git:

```powershell
git clone https://github.com/JuanCrzP1/Ai-sales-engine.git C:\dev\ai-sales-engine
cd C:\dev\ai-sales-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r project/requirements.txt
npm --prefix apps/admin-web ci
New-Item -ItemType Directory -Force project\data | Out-Null
```

Copia `secrets.local.env` a la raíz y `business_config.sqlite3` a `project\data\`, y sigue con `install`, `check` y las órdenes de arriba.

`run_local.bat` enciende también el motor, ngrok y Telegram, y puede consumir API. Para administrar los negocios no hace falta.

## Instrucciones Para Instalar Y Ejecutar En macOS

Estas órdenes **no se han ejecutado en un Mac**. Son la comprobación que falta. Requieren el trabajo ya subido con `git push`; `docs/operations.md` explica cómo hacerlo con un paquete de git, sin publicarlo. Con [Homebrew](https://brew.sh) instalado:

```bash
brew install python@3.13 node git
git clone https://github.com/JuanCrzP1/Ai-sales-engine.git ~/dev/ai-sales-engine
cd ~/dev/ai-sales-engine
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
npm --prefix apps/admin-web ci
mkdir -p project/data
```

En el Mac, activa Ajustes del Sistema > General > Compartir > Inicio de sesión remoto. Con los dos equipos en la misma red y el sistema apagado, ejecuta en Windows, desde la raíz del repositorio, cambiando `usuario` y el nombre del Mac:

```powershell
scp secrets.local.env usuario@nombre-del-mac.local:~/dev/ai-sales-engine/
scp project/data/business_config.sqlite3 usuario@nombre-del-mac.local:~/dev/ai-sales-engine/project/data/
```

Después, en el Mac:

```bash
python scripts/local_secrets.py install
python scripts/local_secrets.py check
python scripts/run_admin_api.py
```

Y en otra terminal, desde la misma carpeta:

```bash
npm --prefix apps/admin-web run panel
```

Abre <http://127.0.0.1:5180>. Para detener: `Ctrl+C` en cada terminal, o `bash run_local_stop.sh`. Apaga el Inicio de sesión remoto al terminar. La guía completa, incluidos el cambio de equipo y la recuperación, está en `docs/operations.md`, «Trabajar Desde Windows Y macOS».

`./run_local.sh` enciende también el motor, ngrok y Telegram. Además necesita `brew install ngrok`, su token y un PostgreSQL local, porque `DATABASE_URL` apunta al propio equipo, y los datos de ese PostgreSQL no se copian.

## Resultado Final De La Auditoría

| Criterio | Estado |
|---|---|
| BusinessConfig v1 | Implementado y verificado |
| Dashboard y sus 13 funcionalidades | Implementado y verificado en Windows |
| Los nueve negocios | Íntegros: 9 de 9 compilan |
| Persistencia real y recuperación tras reiniciar | Verificada, sin `localStorage` |
| Seguridad: loopback, aislamiento, cifrado, máscaras | Verificada en Windows, IPv4 e IPv6 |
| Motor y YAML de negocios | Sin cambios, verificado |
| Arquitectura preparada para la Fase 3 | Documentada; nada de la nube implementado |
| Uso en Windows | Verificado |
| **Uso en macOS** | **Implementado, no verificado en un Mac real** |

### Bloqueo Y Cómo Levantarlo

**Único bloqueo: falta una ejecución real en macOS.** Solo se puede hacer en tu MacBook. Sigue «Instrucciones Para Instalar Y Ejecutar En macOS» y comprueba:

1. `python scripts/local_secrets.py check` termina sin error e indica `9 negocios` y `46 de 46`.
2. El panel abre, muestra los 9 negocios, y un cambio guardado sigue ahí tras reiniciar la API y la interfaz.
3. Estas pruebas no consumen API y deben terminar con `0 failed`:

   ```bash
   pip install -r project/requirements-dev.txt
   python -m pytest
   ```

4. Con el panel encendido en Windows, estas dos órdenes en el Mac deben **fallar**, usando la dirección IP del PC:

   ```bash
   nc -vz -G 3 <IP-del-PC> 8010
   nc -vz -G 3 <IP-del-PC> 5180
   ```

Si los cuatro puntos se cumplen, no queda nada pendiente de esta fase y el dictamen pasa a FASE 2 COMPLETADA. Si alguno falla, es un defecto de esta fase y se corrige aquí.

Lo demás (decisiones sobre el repositorio, `legacy/` y el respaldo de la clave) está documentado y no impide este criterio.

**FASE 2 NO COMPLETADA:** el único bloqueo real es que la compatibilidad con macOS, requisito obligatorio de esta fase, está implementada pero no se ha ejecutado en un Mac. No hay ningún fallo de pruebas ni defecto conocido abierto.

## Anexo: Verificación En macOS (2026-11-09)

Primera ejecución en un Mac real (macOS 26, Apple Silicon), sobre `469c6e9` más las correcciones de este anexo. Sin modelo de IA,
sin la base real y sin la clave real.

| Comprobación del bloqueo | Resultado |
|---|---|
| 3. `python -m pytest` termina con `0 failed` | **Cumplida** tras corregir un defecto de la prueba de red (abajo): 1181 aprobadas, 0 fallidas, 55 omitidas, 63 pendientes de Fase 4. Con Python 3.14, el único instalado; el CI cubre 3.11 y 3.13 |
| Panel: TypeScript, Vitest, integración contra la API real | **Cumplida**: sin errores, 180/180 y 23/23 |
| 1. `local_secrets.py check` con 9 negocios y 46 de 46 | **Cumplida** el mismo día, con `secrets.local.env` y la base copiados desde Windows: 9 negocios, 46 de 46 |
| 2. Panel con los 9 negocios y cambio que sobrevive al reinicio | **Cumplida** (2026-11-10): `./run_local.sh` abre el panel en `127.0.0.1:5180` con los 9 negocios publicados. Un cambio guardado desde el panel en Demo (versión 2, en borrador) sigue ahí después de reiniciar la API y la interfaz. Se hizo sobre una copia de la base, para no dejar versiones de prueba en el historial real, que no se puede borrar; la base real no cambió |
| 4. `nc` desde el Mac contra el panel encendido en Windows | **Pendiente**: necesita los dos equipos en la misma red |

**Defectos encontrados en macOS y corregidos:**

| Defecto | Corrección |
|---|---|
| La prueba de red daba un falso fallo: macOS no incluye la interfaz en el texto de las direcciones IPv6 de enlace local (`fe80::`), y Python ignora el `%interfaz` del texto al conectar. Además, las comprobaciones de «solo en loopback» pasaban sin probar de verdad esas direcciones | La prueba conserva el `scope_id` y conecta con él |
| `node_modules` copiado desde Windows no arranca Vite en macOS | Documentado: se instala en cada equipo con `npm ci` |
| El README pedía Node 20.19 o 22.12, pero Vitest 5 y jsdom 30 exigen 22.22+, 24.15+ o 26+ | Node 24 LTS fijado en `apps/admin-web/.nvmrc` y `engines` |
| El panel usaba el 5173, el puerto que Vite toma por defecto: no abría si otro proyecto de Vite del mismo equipo ya lo ocupaba, y `run_local_stop.sh` cerraba cualquier programa que escuchara en sus puertos | Panel en el 5180, igual en la API, Vite y los lanzadores (lo vigila una prueba). La parada solo detiene procesos de este repositorio |

**Riesgos de la tabla anterior que cambian:**

- *Repositorio público con valores de pago:* los valores de pago de los YAML versionados son ficticios (`1234567890`,
  `usuario@correo.com`, enlaces de `checkout.aisalesengine.com`). Los reales solo están en `secrets.local.env` y en la base cifrada.
- *El CI no ejecuta las pruebas del panel:* resuelto, el job `panel` corre tipos, Vitest, integración y build.
- *El motor no podía leer lo publicado en el panel:* con `BUSINESS_CONFIG_STORE=database` abría la base del motor (`DATABASE_URL`) en
  vez de la del panel, y la prueba que lo cubría sustituía la conexión. Resuelto con `runtime_access.py`: ver
  `docs/business-config.md`, «Conexión Con El Motor».
