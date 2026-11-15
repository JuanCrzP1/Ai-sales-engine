# Elegir el modelo del asesor

Mismo código, mismas conversaciones y mismo juez; solo cambia el modelo. Regla de decisión fijada antes de ver resultados (`compare_models.py`): fuera con cualquier falla crítica o si el 5 % más lento pasa de 8 s; de los que quedan, más conversaciones sin fallas, y con 1 o menos de diferencia, el más barato.

| Modelo | Conversaciones sin fallas | Fallas críticas | Fallas de calidad | Respuesta (mediana · 5 % más lento) | USD por 1.000 mensajes | Veredicto |
|---|---|---|---|---|---|---|
| `openai/gpt-4o-mini` | 10 de 10 | — | — | 3.0 s · 4.5 s | 0.42 | gana |
| `google/gemini-2.5-flash` | 10 de 10 | — | fuera de formato 1 | 1.9 s · 3.2 s | 0.81 | empata en calidad, pero cuesta más |
| `openai/gpt-6-luna` | 9 de 10 | sin respuesta de la ia 12 | no repite la respuesta 1 | 7.5 s · 13.2 s | 0.43 | fuera: sin respuesta de la ia (12) |
| `google/gemini-3.5-flash-lite` | 7 de 10 | sin datos sin pedirlos 1, no repite el bloque 1 | no pide lo ya dado 2, explica cuando no entienden 1 | 2.2 s · 3.8 s | 1.69 | fuera: sin datos sin pedirlos (1), no repite el bloque (1) |
| `deepseek/deepseek-v4.1-flash` | 5 de 10 | datos cuando los necesita 2, nota para el equipo 3, no dice nada falso del pago 1, sin respuesta de la ia 18 | no repite la respuesta 3, no pide lo ya dado 1 | 4.2 s · 9.4 s | 0.67 | fuera: datos cuando los necesita (2), nota para el equipo (3), no dice nada falso del pago (1), sin respuesta de la ia (18) |
| `anthropic/claude-haiku-5.5` | 3 de 10 | datos cuando los necesita 2, no repite el bloque 1, pasa al equipo cuando debe 1, nota para el equipo 1, sin respuesta de la ia 25 | no repite la respuesta 7, no pide lo ya dado 1 | 3.9 s · 5.9 s | 0.9 | fuera: datos cuando los necesita (2), no repite el bloque (1), pasa al equipo cuando debe (1), nota para el equipo (1), sin respuesta de la ia (25) |

**Veredicto:** `openai/gpt-4o-mini`.

Corridas: `modelo_r1_gpt4omini_20261114`, `modelo_r1_haiku55_20261114`, `modelo_r1_gpt6luna_20261114`, `modelo_r1_gemini35lite_20261114`, `modelo_r1_deepseek41_20261114`, `modelo_r1_gemini25flash_20261114`.