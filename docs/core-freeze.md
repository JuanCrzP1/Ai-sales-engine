# Núcleo Conversacional — Estado Estable (Freeze)

> **Documento histórico (mayo de 2026).** Describe el núcleo cuando los negocios se configuraban con YAML y una plataforma externa
> iba a manejar las cuentas. Hoy el motor solo lee la versión publicada de cada negocio, las cuentas son de Neon Auth, el prompt
> se arma por bloques (`infrastructure/ai/prompting/`) y los YAML de los negocios se retiraron el 11 de noviembre de 2026. Sus
> reglas para tocar el núcleo siguen vigentes: cambios pequeños, con el laboratorio de regresión antes y después. Estado actual:
> `docs/architecture.md` y `docs/plan-v1.md`.

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
ConversationFlow → SalesFlow → AIExecution
```

No toma decisiones comerciales. Solo valida estado y delega.

---

### `AIService` — `project/app/services/ai_service.py`

Adapter liviano que expone `generate_business_reply()` al mundo exterior. Instancia `AIPipeline` e inyecta los repositorios globales. Entrega la respuesta con los espacios en orden (`tidy_spacing()`), sin cambiar ninguna palabra.

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

Dirige el turno del asesor. Cada paso vive en su propio módulo de `application/pipeline/`:

- `turn_context.py`: arma lo que el asesor sabe antes de responder (memoria, resumen, lector de pagos, largo de respuesta).
- `answer_review.py`: pide la respuesta a la IA y, si dice algo que no puede salir así, le pide otra.
- `turn_persistence.py`: guarda en la memoria lo que decidió el asesor.
- `payment_outcome.py`: resuelve el pago avisado, pone los datos reales (`payment_delivery.py`, donde está `ejecutar_pago()`) y
  aplica el largo máximo (`enforce_max_words()`).
- `handoff_brief.py`: escribe la nota para el equipo cuando el chat pasa a una persona.

El formato de la respuesta estructurada (intención, `send_payment`, `payment_status`, `handoff`) está en
`services/ai/output_contract.py` y se interpreta en `services/ai/structured_output.py`.

---

### `PromptBuilderService` — `project/app/infrastructure/ai/prompting/` (bloques en `sections/`, orden en `composer.py`, textos fijos en `instructions.py`)

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

### `response_postprocessor.py` — `project/app/application/pipeline/response_postprocessor.py`

Contiene `enforce_max_words()`: trunca la respuesta a `max_words` (default 80) respetando oraciones completas. Es la última defensa antes de entregar la respuesta al usuario. Y `tidy_spacing()`, que `AIService.generate_business_reply()` aplica a toda respuesta: ordena los espacios y nunca cambia una palabra (`tests/test_reply_spacing.py`). Reemplaza a `response_guard.py`, retirado el 18 de noviembre de 2026: borraba palabras «prohibidas» según el tipo de negocio y estaba apagado desde abril (AI-first).

---

## 4. Componentes congelados

Los siguientes archivos **no deben modificarse** sin completar una auditoría técnica previa y obtener autorización explícita:

| Archivo | Razón del freeze |
|---|---|
| `prompting/` (`instructions.py`, `composer.py`, `sections/`) | Núcleo del sistema AI-first. Cambios aquí modifican el comportamiento de toda la IA para todos los tenants: se comprueban con el laboratorio de regresión (`experiments/pricing_lab/run_regression_experiment.py`). |
| `ai_execution.py` y sus pasos (`turn_context.py`, `answer_review.py`, `turn_persistence.py`, `payment_outcome.py`) | El turno del asesor: qué sabe, qué responde, qué se guarda y qué sale con el pago. Se comprueban con el laboratorio de regresión. |
| `conversation_flow.py` | Estado de la conversación y manejo del mensaje inicial. |
| `memory_repository.py` | Contrato de persistencia. Su modificación afecta todos los flujos de memoria. |
| `ai_pipeline.py` | Secuencia de orquestación principal. |

Los siguientes archivos son **estables pero modificables con auditoría ligera**:

| Archivo | Condición para modificar |
|---|---|
| `ai_service.py` | Solo cambios que no afecten el flujo de respuesta ni la memoria |
| `sales_flow.py` | Solo si se verifica que `_hydrate_runtime_yaml` cubre el mismo rol |
| `response_postprocessor.py` | Solo `enforce_max_words` y `tidy_spacing`; no agregar lógica de negocio ni cambiar palabras de la IA |

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

- Modificar cualquier instrucción del prompt en `prompting/instructions.py` (`GROUNDING`, `COMMERCIAL_BEHAVIOR`, `CHANNEL_FRAME`, etc.) o el orden de los bloques en `prompting/composer.py`
- Cambiar el formato del `history_summary` (afecta continuidad de conversación)
- Modificar el contrato de structured output (campos `intent`, `payment_method`, `payment_status`)
- Tocar `ejecutar_pago()` o `_resolve_post_payment_message()`
- Cambiar la lógica de `conversation_state` (new/active/warm/cold)
- Migrar `MemoryRepository` a PostgreSQL

---

## 7. Suscripciones, planes y límites de uso

No forman parte del motor. La plataforma externa gestiona cuentas, planes, facturación y límites,
y solo envía al motor solicitudes que ya puede atender. `AIPipeline.run()` no consulta suscripciones
ni cuotas: carga la configuración del negocio y ejecuta la atención comercial.

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

### Deuda técnica pendiente

| Item | Impacto | Fase sugerida |
|---|---|---|
| Migrar `MemoryRepository` a PostgreSQL | Alto — prerequisito para escalar multi-tenant en producción | Fase 8 |
| Eliminar `SalesFlow` tras verificar que `_hydrate_runtime_yaml` lo cubre | Bajo | Fase 6C-parte-2 |
| Retirar `intent_detectado` de la capa de memoria si no tiene consumidor futuro | Bajo | Fase 6C-parte-2 |
