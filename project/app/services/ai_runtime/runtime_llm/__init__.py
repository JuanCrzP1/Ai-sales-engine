##### 🚨 AI-FIRST ARCHITECTURE RULE #####
# Este sistema es AI-first.
#
# ❌ PROHIBIDO:
# - NO inferir intent fuera de structured_output.py
# - NO usar heurísticas ("quiero", "comprar", etc.)
# - NO crear lógica comercial en código
# - NO forzar respuestas
# - NO agregar reglas de cierre
#
# ✅ PERMITIDO:
# - pasar contexto
# - estructurar datos
# - delegar completamente en la IA
#
# 💣 SI VIOLAS ESTO:
# rompes consistencia, ventas y multi-tenant
#########################################
from .client import AIService as Client
from .prompting import RuntimeLLMImplementation


class RuntimeLLM(RuntimeLLMImplementation):
	"""Facade del runtime LLM con componentes separados."""


class AIService(RuntimeLLM):
	"""Alias de compatibilidad para el runtime."""

	pass


__all__ = ["Client", "RuntimeLLMImplementation", "RuntimeLLM", "AIService"]
