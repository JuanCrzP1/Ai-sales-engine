# Elegir el modelo del asesor

Mismo código, mismas conversaciones y mismo juez; solo cambia el modelo. Regla de decisión fijada antes de ver resultados (`compare_models.py`): fuera con cualquier falla crítica o si el 5 % más lento pasa de 8 s; de los que quedan, más conversaciones sin fallas, y con 1 o menos de diferencia, el más barato.

| Modelo | Conversaciones sin fallas | Fallas críticas | Fallas de calidad | Respuesta (mediana · 5 % más lento) | USD por 1.000 mensajes | Veredicto |
|---|---|---|---|---|---|---|
| `openai/gpt-4o-mini` | 10 de 10 | — | — | 3.0 s · 4.5 s | 0.42 | empata en calidad, pero cuesta más |
| `google/gemini-2.5-flash` | 10 de 10 | — | fuera de formato 1 | 1.9 s · 3.2 s | 0.81 | empata en calidad, pero cuesta más |
| `openai/gpt-6-luna` | 10 de 10 | — | — | 3.0 s · 5.7 s | 0.29 | gana |
| `deepseek/deepseek-v4.1-flash` | 8 de 10 | no dice nada falso del pago 1 | nota fiel 2 | 2.5 s · 6.5 s | 0.31 | fuera: no dice nada falso del pago (1) |
| `google/gemini-3.5-flash-lite` | 7 de 10 | sin datos sin pedirlos 1, no repite el bloque 1 | no pide lo ya dado 2, explica cuando no entienden 1 | 2.2 s · 3.8 s | 1.69 | fuera: sin datos sin pedirlos (1), no repite el bloque (1) |
| `anthropic/claude-haiku-5.5` | 7 de 10 | pasa al equipo cuando debe 2 | no pide lo ya dado 1, fuera de formato 22 | 2.5 s · 4.7 s | 0.78 | fuera: pasa al equipo cuando debe (2) |

**Veredicto:** `openai/gpt-6-luna`.

Corridas: `modelo_r1_gpt4omini_20261114`, `modelo_r1_gemini25flash_20261114`, `modelo_r1_gemini35lite_20261114`, `modelo_r1b_haiku55_20261114`, `modelo_r1b_gpt6luna_20261114`, `modelo_r1b_deepseek41_20261114`.