# Documentación

Cada documento tiene un lector. Empieza por el tuyo.

## Si tienes un negocio

| Documento | Qué encuentras |
|---|---|
| [Guía del negocio](guia-del-negocio.md) | Crear la cuenta, enseñarle al asistente, conectar WhatsApp, atender, vender y ver los reportes |
| [Producto](product.md) | Qué problema resuelve y cómo vende el asistente |

## Si vas a desarrollar

| Documento | Qué encuentras |
|---|---|
| [Inicio rápido](quickstart.md) | Instalar, arrancar todo en tu equipo y correr las pruebas |
| [Cómo contribuir](../CONTRIBUTING.md) | Reglas, pruebas, laboratorio de regresión y mensajes de commit |
| [API del asistente](api.md) | Para conectar el asistente a cualquier plataforma: autenticación, mensajes, respuestas, errores y guías por plataforma |
| [Arquitectura del motor](architecture.md) | Por dónde entra un mensaje, cómo se arma la respuesta y cómo se borra un chat |
| [Negocios](tenants.md) | Cómo se aísla cada negocio, qué tablas lo forman y los negocios de ejemplo |
| [Contrato de configuración](business-config.md) | BusinessConfig v1: el documento de cada negocio, sus versiones, datos de pago y la API del panel |
| [Trazabilidad del contrato](business-config-traceability.md) | Adónde fue cada campo de la configuración antigua (generado) |
| [Panel](../apps/admin-web/README.md) · [su arquitectura](../apps/admin-web/docs/architecture.md) | Cómo está hecho el panel y sus decisiones |

## Si vas a operar la plataforma

| Documento | Qué encuentras |
|---|---|
| [Desplegar](despliegue.md) | Qué necesita el proyecto para funcionar en Vercel o en otro lugar: piezas, servicios y cada variable con dónde va |
| [Operación](operations.md) | Vercel y Neon, WhatsApp por QR, atención humana, secretos entre equipos y cómo depurar |
| [Plan de la versión 1](plan-v1.md) | Auditoría, fases y el avance de cada una |
| [Cambios](../CHANGELOG.md) | Qué cambió y cuándo |

## Históricos

Describen el sistema en un momento pasado; se conservan como registro.

- [Auditoría de la Fase 2 (noviembre de 2026)](FASE_2_AUDITORIA_FINAL.md)
- [Congelamiento del núcleo (mayo de 2026)](core-freeze.md)

## Cómo se escribe esta documentación

- En español, para quien la va a leer: la del negocio sin términos técnicos; la técnica, con rutas a los archivos.
- Cada afirmación se puede comprobar en el código o en una prueba. Si algo cambia, el documento cambia en el mismo commit.
- Las capturas de `images/` son del panel con los negocios de ejemplo (datos ficticios).
