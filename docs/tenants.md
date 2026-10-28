# Tenants

## Propósito De Este Documento

Describe cómo el motor identifica y aísla a cada negocio (tenant). Está basado en el runtime actual del repositorio.

## Qué Es Un Tenant

En este sistema, un tenant es una cuenta lógica de negocio que opera sobre la misma plataforma compartida.

Cada tenant tiene, al menos:

- identidad propia (`slug`, `id`, estado)
- configuración comercial propia
- pricing propio
- capacidades y restricciones propias
- memoria conversacional aislada
- posible configuración de conectores y secretos propios

El tenant no es un detalle administrativo. Es la unidad de aislamiento y de configuración.

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

## Suscripciones, Planes Y Límites De Uso

No forman parte del motor. La plataforma externa gestiona cuentas, planes, facturación y límites de uso,
y decide qué solicitudes envía al motor.

El pipeline (`project/app/application/ai_pipeline.py`) no consulta suscripciones ni cuotas: con un tenant
resuelto, carga su configuración comercial y ejecuta la atención conversacional.

Los precios, planes, catálogos y métodos de pago que aparecen en la configuración de cada negocio son
la oferta que ese negocio vende a sus propios clientes, no planes del motor.
