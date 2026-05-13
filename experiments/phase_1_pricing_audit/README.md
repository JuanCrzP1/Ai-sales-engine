# Phase 1 — Pricing & Commercial Scope Audit

## Propósito

Este laboratorio existe para **medir antes de modificar**.

Ningún cambio en producción será aprobado hasta que los scripts aquí demuestren objetivamente:

1. El prompt permanece igual o más corto.
2. La IA comunica mejor qué incluye y qué no incluye.
3. El precio se presenta como inversión (framing).
4. La respuesta mantiene naturalidad humana.
5. La capacidad de venta mejora o, al menos, no se degrada.

---

## Principio arquitectónico

> Primero se mide. Luego se experimenta. Solo después se integra.

---

## Estructura

```
experiments/phase_1_pricing_audit/
├── README.md                     ← Este archivo
├── generate_prompt_snapshot.py   ← Genera el prompt real del tenant y lo guarda
├── compare_prompt_length.py      ← Compara métricas entre versiones del prompt
├── run_golden_conversations.py   ← Ejecuta una conversación humana real de 10 turnos
├── clear_test_memory.py          ← Limpia la memoria conversacional del tenant
└── results/
    ├── baseline_prompt.txt       ← Prompt baseline generado
    ├── baseline_metrics.json     ← Métricas del prompt baseline
  ├── baseline_conversations.md ← Respuestas ordenadas de la conversación completa
  └── evolution_log.md          ← Historial acumulativo de cada corrida
```

---

## Scripts de uso

### 1. Generar snapshot del prompt baseline

```bash
python experiments/phase_1_pricing_audit/generate_prompt_snapshot.py
```

Genera el prompt real de `asesor_ai_prod` y guarda:
- `results/baseline_prompt.txt`
- `results/baseline_metrics.json`

### 2. Comparar longitud del prompt entre versiones

```bash
python experiments/phase_1_pricing_audit/compare_prompt_length.py
```

Compara `results/baseline_prompt.txt` con otro archivo de prompt.
Útil para validar que una modificación no infla el contexto.

### 3. Ejecutar conversaciones doradas

```bash
python experiments/phase_1_pricing_audit/run_golden_conversations.py
python experiments/phase_1_pricing_audit/run_golden_conversations.py --label candidate_v1 --tenant tienda_de_ropa
```

Ejecuta una conversación humana secuencial de 10 turnos con el mismo `user_id`,
manteniendo memoria acumulativa entre turnos y sin modificar el pipeline de producción.

Parámetro opcional:
- `--tenant <tenant_slug>`: permite evaluar cualquier tenant configurado. Default: `asesor_ai_prod`.

Guarda respuestas en `results/baseline_conversations.md` o en el archivo indicado por `--output`.

### 4. Limpiar memoria conversacional

```bash
python experiments/phase_1_pricing_audit/clear_test_memory.py
```

Elimina la memoria RAM del tenant `asesor_ai_prod` para evitar contaminación entre corridas.

---

## Conversación Humana Base

La evaluación principal del laboratorio ya no usa preguntas aisladas. Usa esta secuencia completa:

| # | Pregunta | Evalúa |
|---|----------|--------|
| 1 | Hola, ¿cómo estás? | Inicio humano y naturalidad |
| 2 | Me puedes dar más información. | Apertura comercial |
| 3 | ¿Qué venden exactamente? | Claridad de oferta |
| 4 | ¿Cómo funciona eso? | Explicación del servicio |
| 5 | ¿Eso me sirve para una tienda de ropa? | Adaptación al contexto |
| 6 | ¿Qué incluye? | Claridad de la oferta |
| 7 | ¿Qué no incluye? | Transparencia comercial |
| 8 | ¿Y qué precio tiene? | Presentación del precio |
| 9 | Está como costoso. | Manejo de objeción |
| 10 | Bueno, quiero empezar. | Cierre comercial |

Todos los turnos se ejecutan con el mismo `user_id`, de modo que la memoria se acumula de forma natural.

---

## Métricas registradas

```json
{
  "chars": 0,
  "lines": 0,
  "estimated_tokens": 0,
  "has_includes": false,
  "has_not_included": false,
  "has_price_framing": false,
  "has_roi_hints": false,
  "pricing_block_chars": 0,
  "pricing_block_lines": 0
}
```

## Evolution Log

Cada ejecución de `run_golden_conversations.py` agrega una nueva entrada a:

- `results/evolution_log.md`

El archivo es acumulativo y registra:

- fecha y hora UTC;
- label (`baseline`, `candidate_v1`, etc.);
- tenant evaluado;
- archivo generado;
- métricas principales del prompt si existe `baseline_metrics.json`;
- campo manual `Observaciones: pendiente de revision`.

Esto permite demostrar con historial si una iteración acerca o aleja al sistema del vendedor objetivo.

## Flujo recomendado

1. `python experiments/phase_1_pricing_audit/clear_test_memory.py`
2. `python experiments/phase_1_pricing_audit/generate_prompt_snapshot.py`
3. `python experiments/phase_1_pricing_audit/run_golden_conversations.py --label baseline`
4. `python experiments/phase_1_pricing_audit/compare_prompt_length.py`

---

## Regla de oro para aprobación

Un candidato de `build_pricing_context()` se aprueba si y solo si:

- `chars` del prompt candidato ≤ `chars` del baseline + 50 (tolerancia mínima).
- `has_includes = true`.
- `has_not_included = true`.
- Las conversaciones doradas 4, 5, 6, 7 mejoran o igualan al baseline.
- No se degrada la naturalidad ni el CTA final.
