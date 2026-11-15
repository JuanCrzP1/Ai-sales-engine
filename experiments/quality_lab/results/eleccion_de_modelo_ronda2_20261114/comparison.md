# Elegir el modelo del asesor

Mismo código, mismas conversaciones y mismo juez; solo cambia el modelo. Regla de decisión fijada antes de ver resultados (`compare_models.py`): fuera con cualquier falla crítica o si el 5 % más lento pasa de 8 s; de los que quedan, más conversaciones sin fallas, y con 1 o menos de diferencia, el más barato.

| Modelo | Conversaciones sin fallas | Fallas críticas | Fallas de calidad | Respuesta (mediana · 5 % más lento) | USD por 1.000 mensajes | Veredicto |
|---|---|---|---|---|---|---|
| `openai/gpt-4o-mini` | 106 de 114 | sin respuesta de la ia 3 | no pide lo ya dado 4, explica cuando no entienden 4, nota fiel 1, no repite la respuesta 2, fuera de formato 3 | 3.28 s · 4.9 s | 0.37 | fuera: sin respuesta de la ia (3) |
| `google/gemini-2.5-flash` | 101 de 114 | pasa al equipo cuando debe 4, sin respuesta de la ia 1 | no pide lo ya dado 5, explica cuando no entienden 1, nota fiel 1, fuera de formato 9, no repite la respuesta 5, sigue las reglas para pasar 3 | 2.04 s · 3.2 s | 0.88 | fuera: pasa al equipo cuando debe (4), sin respuesta de la ia (1) |
| `openai/gpt-6-luna` | 98 de 114 | no dice nada falso del pago 2, sin respuesta de la ia 2 | responde lo que preguntan 2, no pide lo ya dado 5, explica cuando no entienden 3, no repite la respuesta 5 | 3.21 s · 5.5 s | 0.2 | fuera: no dice nada falso del pago (2), sin respuesta de la ia (2) |

**Veredicto:** ningún modelo califica.

Corridas: `modelo_r2_gpt6luna_20261114`, `modelo_r2_gpt6luna_reglas_20261114`, `modelo_r2_gpt4omini_20261114`, `modelo_r2_gpt4omini_reglas_20261114`, `modelo_r2_gemini25flash_20261114`, `modelo_r2_gemini25flash_reglas_20261114`.