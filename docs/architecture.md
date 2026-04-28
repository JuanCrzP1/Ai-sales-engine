# Arquitectura Del Sistema

## Propósito De Este Documento

Este documento describe la arquitectura activa del sistema según el código actual del repositorio. No documenta módulos eliminados ni capas teóricas no presentes en el runtime.

El foco está en responder tres preguntas:

1. Por dónde entra un mensaje y cómo sale una respuesta.
2. Qué rol cumple cada capa del runtime actual.
3. Cómo el contexto del tenant modifica el comportamiento final.

## Flujo Completo Del Sistema

Hay dos entradas activas:

- webhook real de WhatsApp Meta
- endpoint de simulación para pruebas, validación y revisión del flujo comercial

### Flujo Productivo Real

```text
WhatsApp Cloud API
-> project/app/main.py
-> project/app/api/routes.py
-> project/app/api/controllers/whatsapp_webhook.py
-> project/app/services/tenant_channel_resolver.py
-> project/app/connectors/router.py
-> project/app/connectors/whatsapp/meta/parser.py
-> project/app/application/runtime/tenant_runtime_loader.py
-> project/app/application/runtime/runtime_yaml_builder.py
-> project/app/infrastructure/config/config_service.py
-> project/app/services/ai_service.py
-> project/app/application/ai_pipeline.py
-> project/app/application/pipeline/saas_guard.py
-> project/app/application/pipeline/conversation_flow.py
-> project/app/application/pipeline/sales_flow.py
-> project/app/application/pipeline/ai_execution.py
-> project/app/application/pipeline/response_router.py
-> project/app/services/ai/ai_orchestrator.py
-> project/app/infrastructure/ai/prompting/builder/prompt_builder.py
-> project/app/domain/ai/prompt_context.py
-> project/app/services/ai_runtime/runtime_llm/client.py
-> project/app/services/ai/structured_output.py
-> project/app/application/pipeline/response_postprocessor.py
-> project/app/application/response_guard.py
-> project/app/connectors/whatsapp/transport_runtime.py
-> project/app/connectors/whatsapp/transport/sender.py
-> project/app/connectors/whatsapp/meta/sender.py
-> respuesta al canal
```

### Flujo De Simulación

```text
Cliente HTTP
-> project/app/main.py
-> project/app/api/routes.py
-> project/app/api/controllers/simulation.py
-> project/app/api/dependencies.py
-> project/app/services/ai_service.py
-> mismo pipeline AI-first del runtime
-> respuesta JSON
```

La diferencia es operativa:

- `whatsapp_webhook.py` recibe un evento real y envía respuesta al canal.
- `simulation.py` usa el mismo motor de respuesta, pero devuelve JSON sin enviar mensaje por connector.

## Componentes Activos

## FastAPI Y Capa HTTP

- `project/app/main.py`: inicia FastAPI, prepara logger, valida entorno y monta las rutas.
- `project/app/api/routes.py`: registra controladores HTTP.
- `project/app/api/controllers/whatsapp_webhook.py`: entrada real de WhatsApp Meta.
- `project/app/api/controllers/simulation.py`: entrada controlada para simulación y validación.
- `project/app/api/dependencies.py`: resuelve el tenant para endpoints públicos y autenticados.

La capa HTTP no decide la respuesta. Su trabajo es recibir, validar, resolver tenant y delegar al runtime.

## Orquestación Del Runtime

- `project/app/services/ai_service.py`: fachada de alto nivel para generar respuesta comercial.
- `project/app/application/ai_pipeline.py`: coordinador central del pipeline.

`AIService` no contiene el negocio completo. Su responsabilidad es delegar al pipeline, consolidar metadata, aplicar guardas de salida y exponer una interfaz simple al resto del sistema.

## Pipeline Activo

El pipeline actual no está separado en archivos llamados `decision_engine` o `narrative_builder`. Esas responsabilidades existen, pero están distribuidas en componentes activos.

### Intent

No existe un archivo activo llamado `intent.py` para la decisión final del runtime. La interpretación actual se apoya en:

- el modelo LLM
- `project/app/services/ai/structured_output.py`
- `project/app/application/pipeline/response_router.py`

`structured_output.py` normaliza la salida del modelo y expone `intent`, `stage`, `next_step` y metadata útil para el resto del flujo.

### Decision Engine

No hay un módulo activo con ese nombre. La decisión efectiva se reparte entre:

- `project/app/application/pipeline/saas_guard.py`
- `project/app/application/pipeline/conversation_flow.py`
- `project/app/application/pipeline/sales_flow.py`
- `project/app/application/pipeline/response_router.py`

Qué hace cada uno:

- `saas_guard.py`: decide si el tenant puede responder o debe bloquearse por estado SaaS.
- `conversation_flow.py`: decide early responses, continuidad, memoria y contexto del turno.
- `sales_flow.py`: decide qué contexto comercial, pricing, features e inventario deben inyectarse al runtime.
- `response_router.py`: decide si la salida proviene de IA o fallback por excepción, y conserva metadata operativa.

### Narrative Builder

Tampoco existe como archivo aislado. La construcción narrativa del turno actual se distribuye así:

- `project/app/infrastructure/ai/prompting/builder/prompt_builder.py`
- `project/app/domain/ai/prompt_context.py`
- `project/app/services/ai/ai_orchestrator.py`

En la práctica:

- `prompt_context.py` resume memoria y contexto reciente.
- `prompt_builder.py` construye el prompt final con bloques de identidad, grounding, pricing, comportamiento comercial y reglas de foco.
- `ai_orchestrator.py` entrega ese prompt al modelo y parsea la salida estructurada.

### AI

La integración activa con OpenRouter vive en:

- `project/app/services/ai_runtime/runtime_llm/client.py`

Ese archivo:

- construye el cliente HTTP real
- prepara payloads hacia `/chat/completions`
- registra trazas de request y response
- reporta `tokens_usage`

### Salida

La salida se consolida en varias capas:

- `project/app/services/ai/structured_output.py`: parsea contenido y metadata
- `project/app/application/pipeline/response_postprocessor.py`: aplica reglas de postproceso del texto
- `project/app/application/response_guard.py`: valida salida contra el YAML activo
- `project/app/connectors/whatsapp/meta/sender.py`: envía al canal real

## ai_orchestrator.py

### Archivo Activo

- `project/app/services/ai/ai_orchestrator.py`

### Qué Recibe

El método principal `generate_business_reply()` recibe:

- `service`: la implementación runtime del LLM
- `tenant`: tenant actual
- `bot_config`: configuración opcional del runtime/modelo
- `user_message`: mensaje actual del usuario
- `conversation_history`: historial inmediato del turno
- `faq_results`: resultados FAQ ya resueltos
- `yaml_config`: runtime YAML efectivo del tenant

### Qué Hace

Su rol exacto es:

1. pedir al runtime que construya el prompt
2. llamar al modelo con ese prompt y el mensaje actual
3. parsear la respuesta estructurada
4. devolver texto final y metadata sin reescribir el contenido comercial

No decide negocio. No clasifica manualmente. No fuerza respuestas.

### Qué Retorna

Retorna una tupla:

```text
(response_text, ai_used, metadata)
```

Donde:

- `response_text`: texto principal de respuesta
- `ai_used`: bool indicando si la respuesta provino de IA
- `metadata`: intent, stage, next_step y demás datos extraídos del structured output

## Construcción Del Prompt

### Entradas Reales Del Prompt

La construcción activa del prompt toma insumos de:

- `yaml_config` del tenant
- memoria conversacional resumida
- `conversation_history`
- `faq_results`
- contexto comercial consolidado en `sales_flow.py`
- reglas activas del builder

### Cadena Activa

```text
tenant_runtime_loader.py
-> runtime_yaml_builder.py
-> sales_flow.py
-> services/ai_runtime/runtime_llm/prompting.py
-> infrastructure/ai/prompting/builder/prompt_builder.py
-> domain/ai/prompt_context.py
```

### Qué Controla El Prompt

El prompt final controla, como mínimo:

- identidad conversacional
- grounding por negocio
- uso de pricing real
- foco del turno actual
- comportamiento comercial esperado
- límites de veracidad
- contexto reciente del cliente

`prompt_builder.py` no crea reglas de venta por hardcode. Estructura y prioriza el contexto que el modelo debe usar.

## Multi-Tenant

## Resolución Del Tenant

Hay dos mecanismos principales activos:

### Webhook real

En `project/app/api/controllers/whatsapp_webhook.py`:

- se extrae `phone_number_id`
- se consulta `project/app/services/tenant_channel_resolver.py`
- se construye un `Tenant` válido para el runtime

### Simulación y endpoints públicos

En `project/app/api/dependencies.py`:

- se lee `X-Tenant-Slug`
- se normaliza el slug
- se resuelve el tenant vía `DBRepository`

## Carga De Configuración YAML

El runtime del tenant se arma en:

- `project/app/application/runtime/tenant_runtime_loader.py`
- `project/app/application/runtime/runtime_yaml_builder.py`
- `project/app/infrastructure/config/config_service.py`

Las secciones activas que se cargan y validan son:

- `sales`
- `business`
- `pricing`
- `inventory`
- `config`

Además se derivan bloques como:

- `capabilities`
- `post_payment`
- `channel`

## Cómo Afecta El Tenant La Respuesta

El tenant cambia directamente:

- qué vende el negocio
- cómo se explica el valor
- qué precio existe y cómo se cobra
- qué capacidades o canales están disponibles
- qué memoria reciente debe influir en la respuesta
- si el tenant puede o no responder por estado SaaS

La respuesta final no es genérica. Se construye sobre el runtime YAML efectivo del tenant activo.

## Observaciones Técnicas Relevantes

- El sistema activo está simplificado hacia Meta WhatsApp como conector productivo real.
- No hay `decision_engine.py` ni `narrative_builder.py` como archivos activos. Sus responsabilidades están distribuidas.
- El runtime es AI-first: el backend organiza contexto, acceso y validación, pero la interpretación del turno y la redacción dependen del modelo.
- La simulación es parte importante de la arquitectura porque permite probar el mismo motor sin enviar mensajes reales al canal.