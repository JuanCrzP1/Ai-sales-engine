# Lógica SaaS

## Propósito De Este Documento

Este documento describe la lógica SaaS existente y la dirección operativa prevista para control de tenants, suscripciones y uso. Está basado en el runtime actual del repositorio.

No documenta una plataforma de billing completa. Documenta lo que ya existe, lo que ya condiciona el flujo y lo que claramente está preparado para endurecerse después.

## Qué Es Un Tenant

En este sistema, un tenant es una cuenta lógica de negocio que opera sobre la misma plataforma compartida.

Cada tenant tiene, al menos:

- identidad propia (`slug`, `id`, estado)
- configuración comercial propia
- pricing propio
- capacidades y restricciones propias
- memoria conversacional aislada
- posible configuración de conectores y secretos propios

El tenant no es un detalle administrativo. Es la unidad de aislamiento, de configuración y de monetización.

## Dónde Se Resuelve El Tenant

Hay dos caminos activos:

### Webhook Productivo

Archivo principal:

- `project/app/api/controllers/whatsapp_webhook.py`

Proceso:

1. se extrae `phone_number_id` del payload
2. se busca el tenant con `project/app/services/tenant_channel_resolver.py`
3. se construye un objeto `Tenant` válido para el runtime

### Simulación Y Endpoints Públicos

Archivo principal:

- `project/app/api/dependencies.py`

Proceso:

1. el cliente envía `X-Tenant-Slug`
2. el sistema normaliza el slug
3. el tenant se resuelve desde base de datos vía `DBRepository`

## Estado Actual De La Lógica SaaS

El control SaaS activo vive en:

- `project/app/application/pipeline/saas_guard.py`
- `project/app/infrastructure/persistence/subscription_repository.py`
- `project/app/infrastructure/persistence/usage_repository.py`

`saas_guard.py` es el punto donde el pipeline decide si el tenant puede seguir o debe bloquearse.

El flujo actual es:

```text
mensaje entrante
-> tenant resuelto
-> saas_guard.check_access(tenant_key)
-> subscription_repo.is_active(...)
-> usage_repo.can_send(...)
-> si pasa: usage_repo.increment(...)
-> continúa la respuesta
-> si falla: respuesta bloqueada
```

## Estructura Actual En Base De Datos

Los repositorios activos ya reflejan dos conceptos centrales:

### subscriptions

Consultado desde `project/app/infrastructure/persistence/subscription_repository.py`.

Campos que hoy importan en la lógica activa:

- `tenant_id`
- `status`
- `current_period_end`

Qué valida hoy:

- si hay una suscripción activa para el tenant
- si la suscripción sigue vigente por fecha

Comportamiento actual observado:

- si no hay tenant válido, el repositorio no bloquea de forma dura
- si no hay suscripción o fecha, hoy el sistema es permisivo en varios casos

Eso significa que la base SaaS existe, pero todavía está implementada con tolerancia operativa para no cortar el runtime cuando faltan datos SaaS obligatorios.

### usage

Consultado desde `project/app/infrastructure/persistence/usage_repository.py`.

Qué expone hoy:

- `increment(tenant_id)`
- `get_usage(tenant_id)`
- `can_send(tenant_id)`

Comportamiento actual:

- el repositorio ya tiene la interfaz correcta
- hoy el control es permisivo y devuelve `True` en `can_send()`
- la estructura ya prepara el sistema para límites por plan, pero todavía no endurece el bloqueo por consumo

## Validación SaaS: Actual Y Esperada

## Activo / Inactivo

La validación activa ya contempla el estado del tenant vía suscripción.

Camino actual:

```text
saas_guard.py
-> subscription_repository.is_active()
-> si False: bloqueo con reason = subscription_inactive
```

Esto significa que el pipeline ya tiene un punto único para bloquear respuesta por estado SaaS.

## Límites Por Plan

La estructura actual ya contempla la lógica para introducir límites por plan sin reescribir el pipeline.

Camino activo:

```text
saas_guard.py
-> usage_repository.can_send()
-> usage_repository.increment()
```

Hoy `UsageRepository` actúa como placeholder permisivo, pero su posición en el runtime ya es correcta.

Eso habilita evoluciones como:

- límite de mensajes por día
- límite de conversaciones activas
- límite por tenant según plan
- corte por vencimiento de cuota
- upgrade de plan sin cambiar el controlador HTTP

## Flujo Esperado De Bloqueo

El flujo objetivo, ya insinuado por la arquitectura actual, es este:

```text
mensaje
-> resolver tenant
-> validar suscripción
-> validar límite de uso
-> si pasa: responder
-> si no pasa: bloquear con mensaje SaaS controlado
```

El diseño correcto ya existe porque la validación se hace antes de la llamada al modelo, dentro del pipeline.

## Qué Se Monetiza

La monetización natural del sistema es por tenant.

La plataforma está preparada para cobrar por:

- activación o setup
- plan mensual
- volumen de uso
- canales habilitados
- capacidad comercial o automatizaciones adicionales

La clave técnica es que el runtime ya conoce:

- quién es el tenant
- si puede responder
- cuánto puede usar

Eso convierte el control SaaS en parte del flujo de producto, no en un sistema externo pegado después.

## Qué Está Activo Hoy Y Qué No

### Ya Activo

- tenant resolution por webhook o header
- guard centralizado dentro del pipeline
- consulta de estado de suscripción
- punto de control de uso antes de responder

### Parcial O Permisivo

- enforcement duro de límite por plan
- bloqueo agresivo por ausencia de suscripción
- contabilidad real de consumo en `UsageRepository`

### No Documentado Aquí Porque No Está Activo

- pasarelas de cobro
- upgrades automáticos de plan
- facturación externa
- consola administrativa de billing

## Riesgo Operativo Actual

El mayor riesgo actual no es de diseño, sino de endurecimiento pendiente:

- la capa SaaS existe y está bien ubicada
- pero varias validaciones siguen siendo permisivas para no romper el runtime

Esto es positivo para evolución porque permite introducir endurecimiento incremental sin cambiar controladores ni arquitectura general.

## Resumen Ejecutivo

La lógica SaaS del sistema ya está insertada donde debe estar:

- antes de la generación de respuesta
- asociada al tenant
- separada del transporte HTTP
- preparada para monetización real

No es todavía una capa de billing completa, pero sí es una base correcta para escalar la plataforma como SaaS multi-tenant con control de acceso y límites por plan.