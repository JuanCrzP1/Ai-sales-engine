<p align="center">
  <img src="assets/logo.jpg" alt="AI Sales Engine" width="320"/>
</p>

<h1 align="center">AI Sales Engine</h1>

<p align="center">
  Asistente de ventas con IA para WhatsApp, como servicio: cada negocio crea su cuenta, configura su asistente y lo conecta.
</p>

---

## Qué es

Una plataforma SaaS en la que cada negocio:

1. crea su cuenta y su negocio en el panel;
2. describe lo que vende (oferta, precios, pagos, políticas, cómo vende) y lo publica;
3. pega su propia clave de IA (OpenRouter);
4. conecta WhatsApp escaneando un código QR;
5. atiende desde el panel: conversaciones en vivo, clientes, ventas y reportes.

El asistente responde con lo que el negocio publicó, guía al cliente hacia la compra y pasa la conversación a una persona cuando
el cliente la pide, reclama o reporta un pago.

## Cómo vamos (11 de noviembre de 2026)

**Funciona en la nube (Vercel + Neon):**

- Cuentas con Neon Auth; cada usuario solo ve sus negocios.
- Configuración del negocio con contrato versionado: borrador, publicar, volver a una versión anterior.
- Clave de IA por negocio, cifrada (la plataforma no tiene clave propia), con el modelo y el consumo de cada negocio.
- «Probar asistente» con la IA real.
- WhatsApp por código QR (uazapi): el negocio solo toca «Conectar WhatsApp».
- Conversaciones en vivo: escribiendo, chulos de enviado y leído, no leídos, responder desde el panel, pausar la IA, fotos y notas
  de voz que la IA entiende, y paso a una persona con aviso al equipo.
- Clientes con su etapa, ventas (registrar y anular, pagos por verificar) y reportes (embudo, actividad por día, costo de la IA).
- Las migraciones de la base se aplican solas en cada despliegue.

**Lo que sigue:** el plan completo y su avance están en [docs/plan-v1.md](docs/plan-v1.md). Falta, entre otras cosas, el
horario del equipo y el aviso por correo al pasar a una persona, Telegram por negocio, la API oficial de Meta, retirar lo que
queda del sistema anterior (modelos con ids enteros y sus tablas) y la operación para lanzar (monitoreo, copias, correo, términos).

## Estructura del repositorio

| Carpeta | Qué hay |
|---|---|
| `project/app/` | El motor (FastAPI): webhooks de los canales, el pipeline de la IA y la API del panel |
| `project/app/domain/business_config/`, `business_config_application/`, `infrastructure/business_config/`, `admin_api/` | El contrato del negocio, sus casos de uso, el almacén (PostgreSQL o SQLite) y la API del panel |
| `project/db/migrations/` | Migraciones del almacén (se aplican solas en la nube) |
| `project/config/system/` | Ajustes de la plataforma (no de un negocio) |
| `project/config/tenants/<negocio>/` | Los 9 negocios de ejemplo, en JSON: siembran este equipo, la rama de pruebas y las pruebas |
| `project/config/contracts/v1/` | El esquema del contrato y un documento de ejemplo |
| `apps/admin-web/` | El panel (React + Vite) |
| `tests/` | Suite del motor y del almacén; `tests/golden/` guarda lo que el motor recibía de los YAML, congelado |
| `experiments/` | Laboratorio de regresión (sin costo) y de calidad (con la IA real) |
| `scripts/` | API local del panel, preparación de la base en la nube, generadores del contrato |

## Ejecutar en este equipo

```bash
./run_local.sh        # macOS y Linux
run_local.bat         # Windows
```

Arranca el motor (puerto 8082, con el `.env`), el túnel de ngrok, la API del panel (`127.0.0.1:8010`) y el panel en
<http://localhost:5180>. `./run_local_stop.sh` lo detiene todo. En el panel local, «Importar negocios de ejemplo» trae los 9
negocios de ejemplo. Guía completa: [docs/quickstart.md](docs/quickstart.md).

## Pruebas

```bash
pytest                                             # motor y almacén (sin IA real ni base del .env)
npm --prefix apps/admin-web run typecheck
npm --prefix apps/admin-web test                   # panel
npm --prefix apps/admin-web run test:integration   # panel contra la API real y un SQLite temporal
```

Antes de tocar el motor: laboratorio de regresión contra el commit anterior (no gasta nada) y, si cambia el prompt, el
laboratorio de calidad. Ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentación

- [Inicio rápido](docs/quickstart.md)
- [Plan de la versión 1 y avance](docs/plan-v1.md)
- [Arquitectura del motor](docs/architecture.md)
- [Negocios: aislamiento y ejemplos](docs/tenants.md)
- [Contrato de configuración (BusinessConfig)](docs/business-config.md)
- [Operación: variables, nube, canales y depuración](docs/operations.md)
- [Panel de administración](apps/admin-web/README.md)
- [Producto](docs/product.md)
- Históricos: [Auditoría de la Fase 2](docs/FASE_2_AUDITORIA_FINAL.md), [Congelamiento del núcleo](docs/core-freeze.md)
