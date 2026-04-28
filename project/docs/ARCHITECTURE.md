# 🧠 ARCHITECTURE.md

## Sistema SaaS AI-First de Ventas Conversacionales

---

# 🎯 PROPÓSITO

Este sistema NO es una automatización rígida.

👉 Es un **vendedor SaaS conversacional** que:

- entiende clientes
- guía decisiones
- empuja acción
- cierra ventas

---

# 🧱 PRINCIPIO FUNDAMENTAL

## 🚨 AI-FIRST

La IA es la única responsable de:

- interpretar intención
- construir discurso
- ejecutar la venta

El código:

- ❌ NO decide
- ❌ NO vende
- ❌ NO corrige

👉 SOLO orquesta

---

# 🔁 FLUJO DEL SISTEMA

usuario → ai_execution → prompt_builder → IA → structured_output → respuesta

## Detalle del flujo

1. Usuario envía mensaje
2. Se construye contexto (YAML + historial + metadata)
3. Se genera prompt
4. IA produce respuesta
5. structured_output interpreta intent
6. Se retorna respuesta SIN modificar

⚠️ IMPORTANTE:

- El sistema NO reescribe la respuesta
- El sistema NO corrige la IA
- El sistema NO aplica lógica comercial

---

# 🧠 JERARQUÍA DE DECISIÓN DE LA IA

La IA debe priorizar en este orden:

1. Estado conversacional (historial, contexto activo, modo operativo)
2. Intent detectado (structured_output)
3. Contexto del negocio (YAML)
4. Estilo de comunicación (humano, natural)

⚠️ Si esta jerarquía se rompe:

- la IA responde incoherente
- pierde contexto
- baja conversión
- deja de vender

---

# 🧩 MULTI-TENANT

Cada cliente es independiente.

Configuración por tenant:

- business.yaml
- config.yaml
- inventory.yaml
- pricing.yaml
- sales.yaml

👉 TODO el comportamiento sale de YAML

❌ PROHIBIDO:

- hardcodear reglas por negocio
- mezclar comportamientos entre tenants

---

# 🧠 INTENT (FUENTE ÚNICA)

El intent SOLO se define en:

`structured_output.py`

❌ NADIE MÁS puede:

- inferir intent
- modificar intent
- reinterpretarlo

👉 Romper esta regla rompe todo el sistema.

---

# ⚙️ RESPONSABILIDAD POR CAPA

## prompt_builder

✔ inyecta YAML  
✔ organiza contexto  
✔ respeta jerarquía  

❌ NO decide  
❌ NO vende  
❌ NO aplica reglas  

---

## ai_execution

✔ conecta componentes  
✔ ejecuta pipeline  

❌ NO modifica respuesta  
❌ NO aplica lógica comercial  
❌ NO altera intent  

---

## structured_output

✔ define intent  
✔ parsea salida  

👉 Es la única fuente de verdad del intent.

---

## sales_context_block

✔ entrega datos estructurados  

❌ NO lógica  
❌ NO heurísticas  
❌ NO decisiones  

---

## strategies (cta, objection, etc)

✔ passthrough  

❌ NO decisiones  
❌ NO reglas comerciales  
❌ NO usar intent  

---

# 🚫 ANTI-PATTERNS (PROHIBIDO)

Nunca hacer:

- if intent == "buy"
- detectar "quiero", "comprar"
- concatenar respuestas
- forzar cierre
- reescribir salida de la IA

👉 Rompe AI-first

---

# 🚫 QUÉ ROMPE AI-FIRST

- ajustar intent en código
- lógica comercial en Python
- heurísticas por texto
- modificar respuestas
- cierre manual

---

# ⚠️ ERRORES COMUNES

- duplicar lógica de intent
- fallback de cierre en código
- heurísticas por palabras
- mezclar tenants
- parchear respuestas

👉 Si ves esto:

DETENTE

---

# 🧪 FILOSOFÍA DE TESTS

Los tests NO validan código.

👉 Validan ventas reales

## Tipos

### Globales

- presión
- naturalidad
- cierre
- continuidad

### Por tenant

- demo
- inventario
- logística
- servicios

---


# 💣 REGLA DE ORO

SI UN TEST FALLA  
→ EL SISTEMA ESTÁ MAL  
→ NO EL TEST  

---

# 🔥 OBJETIVO FINAL

- sonar humano
- entender contexto
- mantener continuidad
- empujar acción
- cerrar ventas

---
# 🔐 REGLAS DE DESARROLLO

Antes de tocar el sistema:

- Si un test falla → NO tocar el test
- NO parchear respuestas
- NO agregar lógica comercial en código
- NO usar heurísticas por palabras

Si no sabes cómo resolver algo:

👉 DETENTE  
👉 pide auditoría  
👉 NO improvises  

---

# 🚨 PROHIBICIÓN ABSOLUTA

Este sistema se rompe si:

- agregas lógica fuera de la IA
- duplicas decisiones
- modificas el intent
- fuerzas comportamiento desde código

---

# 🧠 PRINCIPIO DE MANTENIMIENTO

```text
MENOS CÓDIGO = MEJOR IA
MÁS CONTROL = PEOR CONVERSIÓN

---

# 💣 PRINCIPIO FINAL

Este sistema no falla por código…

👉 falla cuando rompen las reglas

---

# 💥 FRASE FINAL

No estamos escribiendo código.

👉 estamos construyendo un sistema que genera dinero