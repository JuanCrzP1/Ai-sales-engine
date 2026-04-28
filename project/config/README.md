# Guía De Configuración YAML

Este directorio concentra la configuración funcional del sistema de ventas AI-first. La lógica por negocio vive en cada tenant; la base global solo define estructura compartida, sistema y recursos comunes.

## Principio De Operación

Mismo motor.
Misma arquitectura.
Distinto comportamiento según el tenant activo.

La adaptación no se resuelve con ramas de código. Se resuelve con configuración.

## Estructura Canónica

- `core/`: `intents.yaml`, `nlu.yaml`, `flows.yaml`, `intent_levels.yaml`
- `tenants/<tenant_slug>/`: `business.yaml`, `config.yaml`, `inventory.yaml`, `pricing.yaml`, `sales.yaml`
- `channels/channels.yaml`: configuración por canal
- `assets/media.yaml`: media reutilizable
- `system/`: `bot_config.yaml`, `settings.yaml`, `conversation_stage.yaml`, `secrets.yaml`

## Configuración Por Tenant

Cada tenant controla su comportamiento desde cinco archivos:

- `business.yaml`: contexto del negocio
- `config.yaml`: parámetros generales del sistema
- `inventory.yaml`: oferta o servicios disponibles
- `pricing.yaml`: estructura de precios
- `sales.yaml`: lógica comercial y enfoque de ventas

## Regla Operativa

- la lógica comercial específica vive en `tenants/<tenant_slug>/`
- la base global no debe contener datos reales de un negocio concreto
- la segmentación comercial y de pricing sale de `pricing.yaml`
- el motor conversacional debe operar con continuidad aunque cambie el sector del tenant

## Qué Editar Según El Cambio

- identidad comercial: `tenants/<tenant_slug>/business.yaml`
- parámetros operativos del tenant: `tenants/<tenant_slug>/config.yaml`
- catálogo, servicios u oferta: `tenants/<tenant_slug>/inventory.yaml`
- precios y condiciones: `tenants/<tenant_slug>/pricing.yaml`
- enfoque comercial, objeciones y cierre: `tenants/<tenant_slug>/sales.yaml`
- configuración global de runtime: `system/bot_config.yaml` y `system/settings.yaml`
- intenciones y flujos compartidos: `core/intents.yaml` y `core/flows.yaml`

## Reglas De Mantenimiento

- no duplicar datos comerciales entre global y tenant
- no escribir copy final de negocio en archivos globales
- si cambian precios, actualizar `pricing.yaml`
- si cambian canales o assets, editar `channels/channels.yaml` o `assets/media.yaml`

## Estado Del Runtime

Actualmente el runtime consume:

- configuración global desde `system/`
- intenciones, NLU y flujos desde `core/`
- contexto de negocio, configuración, inventario, pricing y ventas desde `tenants/<tenant_slug>/`
- media desde `assets/`
- configuración por canal desde `channels/channels.yaml`

La prioridad es mantener una sola fuente de verdad por tenant.

