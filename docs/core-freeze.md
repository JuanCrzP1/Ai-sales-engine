# Núcleo Conversacional — Estado Estable (Freeze)

**Versión:** 6C  
**Fecha:** 9 de mayo de 2026  
**Tests al momento del freeze:** 114 passed, 0 failed  
**Fases previas completadas:** 5A, 5B, 5C, 5D-A, 5D-B, 5D-C, 6A, 6B

---

## 1. Propósito del núcleo conversacional

El núcleo conversacional es el conjunto de componentes que procesan cada mensaje entrante de un usuario, construyen el contexto para la IA, ejecutan la llamada al modelo de lenguaje y persisten el resultado en memoria.

Su única responsabilidad es entregar al LLM el contexto correcto y devolver la respuesta sin modificarla.

No contiene lógica de negocio. No clasifica intenciones. No fuerza comportamientos. La IA decide.

---

## 2. Principios AI-first

Estos principios son no negociables. Cualquier propuesta de cambio que los viole debe rechazarse sin necesidad de análisis adicional.

**NO está permitido en el núcleo:**
- Clasificar intent con heurísticas de palabras clave
- Modificar la respuesta de la IA antes de entregarla al usuario (excepto `enforce_max_words` y `validate_response_against_yaml`, que son defensas de seguridad, no lógica comercial)
- Usar `if/else` condicionados por intent para alterar flujo de ventas
- Hardcodear comportamiento de ningún tenant
- Agregar texto de respuesta manualmente al output de la IA

**SÍ está permitido en el núcleo:**
- Pasar contexto al prompt (datos de YAML, memoria, historial)
- Estructurar el output del LLM (structured output)
- Persistir metadata de la conversación en memoria
- Aplicar defensas de seguridad post-LLM (longitud, coherencia comercial)

---

## 3. Componentes del núcleo y sus responsabilidades

### `AIPipeline` — `project/app/application/ai_pipeline.py`

Orquestador principal. Recibe el mensaje del usuario y coordina la secuencia:

```
SaaSGuard → ConversationFlow → SalesFlow → AIExecution
```

No toma decisiones comerciales. Solo valida estado y delega.

---

### `AIService` — `project/app/services/ai_service.py`

Adapter liviano que expone `generate_business_reply()` al mundo exterior. Instancia `AIPipeline` e inyecta los repositorios globales. Aplica `validate_response_against_yaml()` y `_extract_price_anchor()` sobre el resultado final.

---

### `ConversationFlow` — `project/app/application/pipeline/conversation_flow.py`

Gestiona el estado temporal de la conversación antes de llamar a la IA:
- Detecta si corresponde enviar el mensaje inicial del tenant (configurable por YAML)
- Calcula el estado de la conversación (`new`, `active`, `warm`, `cold`) por tiempo de inactividad
- Inyecta historial estructurado en `runtime_yaml`
- Persiste el mensaje del usuario en memoria

---

### `SalesFlow` — `project/app/application/pipeline/sales_flow.py`

Precarga las secciones YAML del tenant (`sales`, `business`, `pricing`, `features`, `inventory`) en `runtime_yaml` antes de que el prompt builder las necesite. Actúa como hidratación defensiva antes de `PromptBuilderService._hydrate_runtime_yaml()`.

---

### `AIExecution` — `project/app/application/pipeline/ai_execution.py`

Construye el contexto de memoria, ejecuta el prompt builder, llama al LLM vía `_generate_with_frame()`, interpreta el structured output, ejecuta la lógica de pago si corresponde, y persiste la respuesta y metadata en memoria.

Contiene:
- `FRAME_BLOCK`: segundo wrapper de prompt que inyecta el contrato de metadata JSON (intent, payment_method, payment_status). No debe eliminarse sin auditar el contrato de structured output.
- `ejecutar_pago()`: lógica de ejecución de pago real (link, nequi, daviplata, bank, breb)
- `enforce_max_words()`: defensa de longitud post-LLM

---

### `PromptBuilderService` — `project/app/infrastructure/ai/prompting/builder/prompt_builder.py`

Construye el prompt del sistema que recibe el LLM. Ensambla bloques de contexto a partir del `runtime_yaml`. Es la capa más crítica del sistema AI-first: todo cambio aquí afecta directamente el comportamiento del modelo.

Estructura del prompt generado:

```
CONTEXTO DEL NEGOCIO
REGLAS OPERATIVAS
CAPACIDADES DEL NEGOCIO
COMPORTAMIENTO COMERCIAL
PRICING
```

Cada bloque tiene gates de activación (estado de conversación, datos en memoria). Los cambios en este archivo requieren auditoría y suite de tests.

---

### `MemoryDomainService` — `project/app/domain/conversation/memory.py`

Facade del dominio de memoria. Expone la API de lectura/escritura de estado conversacional: last_intent, last_pain, payment_method, payment_status, history, conversation_state, etc.

---

### `MemoryRepository` — `project/app/infrastructure/persistence/memory_repository.py`

Implementación en RAM de `MemoryDomainService`. Almacena 14 dicts keyed por `(tenant_slug, user_id)`. Retiene hasta 20 mensajes por usuario. No es persistente entre reinicios del servidor.

`SQLMemoryRepository` es el placeholder vacío para la migración futura a PostgreSQL.

---

### `response_guard.py` — `project/app/application/response_guard.py`

Validador post-LLM de coherencia comercial. Detecta si la respuesta menciona planes inexistentes en el YAML o términos de modelo de negocio incorrecto (e.g., términos de catálogo en respuesta de SaaS). Se aplica en `AIService.generate_business_reply()`.

---

### `response_postprocessor.py` — `project/app/application/pipeline/response_postprocessor.py`

Contiene `enforce_max_words()`: trunca la respuesta a `max_words` (default 80) respetando oraciones completas. Es la última defensa antes de entregar la respuesta al usuario.

---

## 4. Componentes congelados

Los siguientes archivos **no deben modificarse** sin completar una auditoría técnica previa y obtener autorización explícita:

| Archivo | Razón del freeze |
|---|---|
| `prompt_builder.py` | Núcleo del sistema AI-first. Cambios aquí modifican el comportamiento de toda la IA para todos los tenants. |
| `ai_execution.py` | Orquestación de la llamada al LLM y contrato de structured output (FRAME_BLOCK). |
| `conversation_flow.py` | Estado de la conversación y manejo del mensaje inicial. |
| `memory_repository.py` | Contrato de persistencia. Su modificación afecta todos los flujos de memoria. |
| `ai_pipeline.py` | Secuencia de orquestación principal. |

Los siguientes archivos son **estables pero modificables con auditoría ligera**:

| Archivo | Condición para modificar |
|---|---|
| `ai_service.py` | Solo cambios que no afecten el flujo de respuesta ni la memoria |
| `sales_flow.py` | Solo si se verifica que `_hydrate_runtime_yaml` cubre el mismo rol |
| `response_guard.py` | Modificaciones requieren actualizar `test_response_guard.py` |
| `response_postprocessor.py` | Solo `enforce_max_words`; no agregar lógica de negocio |

---

## 5. Reglas para modificar el núcleo

Antes de cualquier cambio en archivos congelados:

1. **Auditoría de impacto**: documentar qué bloques del prompt cambian y en qué estados de conversación.
2. **Tests previos**: ejecutar la suite determinística y confirmar 114 passed.
3. **Scope controlado**: cada cambio debe tener un objetivo único y verificable.
4. **Tests posteriores**: la suite debe seguir verde después del cambio.
5. **Sin "ya aproveché"**: no agregar cambios adicionales al scope de una fase.

---

## 6. Cambios que requieren auditoría completa (nueva fase)

Los siguientes tipos de cambio son de alto riesgo y requieren una fase numerada con informe previo:

- Modificar cualquier bloque del prompt en `prompt_builder.py` (`GROUNDING_BLOCK`, `COMMERCIAL_BEHAVIOR_BLOCK`, `FRAME_BLOCK`, etc.)
- Cambiar el formato del `history_summary` (afecta continuidad de conversación)
- Modificar el contrato de structured output (campos `intent`, `payment_method`, `payment_status`)
- Tocar `ejecutar_pago()` o `_resolve_post_payment_message()`
- Cambiar la lógica de `conversation_state` (new/active/warm/cold)
- Migrar `MemoryRepository` a PostgreSQL
- Conectar `response_guard.py` al pipeline de producción (hoy se llama desde `AIService` pero no desde `AIPipeline`)

---

## 7. Relación con la capa SaaS (subscriptions, usage, billing)

El núcleo conversacional está desacoplado del billing. La integración ocurre en un único punto de entrada:

```
AIPipeline.run()
  └── SaaSGuard.check_access(tenant_key)
        ├── SubscriptionRepository — valida que el tenant tenga suscripción activa
        └── UsageRepository — valida que no haya superado su cuota de mensajes
```

Si `SaaSGuard` bloquea la solicitud, el núcleo conversacional **no se ejecuta**. La respuesta de bloqueo es devuelta directamente sin llamar a la IA.

Para pasar a billing y monetización real, el prerequisito técnico es:
1. Implementar `SQLMemoryRepository` con persistencia real en PostgreSQL
2. Conectar `SubscriptionRepository` y `UsageRepository` a la base de datos
3. Verificar que `SaaSGuard` refleje el estado real de cada tenant

El núcleo conversacional no necesita cambiar para soportar billing.

---

## 8. Estado del sistema al momento del freeze

```
Tests:          114 passed, 0 failed
Fases completadas: 5A, 5B, 5C, 5D-A, 5D-B, 5D-C, 6A, 6B, 6C
Memoria:        In-RAM (MemoryRepository) — no persistente entre reinicios
Tenants activos: multi-tenant via YAML (config/tenants/<slug>/)
Canales activos: WhatsApp, Web, Telegram
LLM:            OpenRouter (configurable por tenant)
```

### Deuda técnica pendiente (no bloquea billing)

| Item | Impacto | Fase sugerida |
|---|---|---|
| Migrar `MemoryRepository` a PostgreSQL | Alto — prerequisito para escalar multi-tenant en producción | Fase 8 |
| Eliminar `SalesFlow` tras verificar que `_hydrate_runtime_yaml` lo cubre | Bajo | Fase 6C-parte-2 |
| Retirar `intent_detectado` de la capa de memoria si no tiene consumidor futuro | Bajo | Fase 6C-parte-2 |
| Conectar `response_guard.py` al pipeline de `AIPipeline` en lugar de solo `AIService` | Medio | Fase 7 |
