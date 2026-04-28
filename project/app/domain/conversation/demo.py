##### 🚨 DO NOT PATCH BEHAVIOR #####
# Este sistema es AI-FIRST.
# IMPORTANTE: SOLO DEBE FUNCIONAR PARA EL TENANT "asesor_ai_prod".
# 
# ❌ NO:
# - modificar respuestas manualmente
# - agregar lógica condicional de venta
# - parchear outputs
#
# ✅ SI:
# - mejorar contexto
# - mejorar instrucciones a la IA
#
# Si un test falla:
# -> corregir contexto o prompt
# -> NO tocar respuesta final
################################

##### DEMO MODE CONTRACT #####
# Si demo está activa:
# - NO salir del modo
# - NO volver a discovery
# - NO hacer preguntas genéricas
#
# Cada respuesta:
# -> debe continuar experiencia
# -> debe parecer negocio real
################################

from __future__ import annotations

from typing import Protocol


##### 🔒 CRITICAL BEHAVIOR BLOCK #####
# NO MODIFICAR SIN VALIDACIÓN COMPLETA
# Romper esto afecta ventas directamente
####################################
DEMO_BEHAVIOR_BLOCK = """##### 🚨 DEMO HARD LOCK #####

Si demo está activa:

- actúa como negocio real
- mantén continuidad comercial
- respeta la memoria previa
- SOLO actúa como negocio
- NO puedes cambiar el tono
- NO puedes salir del personaje
- TODAS las respuestas deben mantener el mismo formato

RESPUESTA SIEMPRE debe empezar EXACTO así:

"perfecto, mira, esto sería respondiendo a tu cliente:"

Si no empieza así:
→ estás fuera de demo

NO hay excepciones.

❌ PROHIBIDO:
- saludar como bot
- cambiar el mensaje del cliente
- inventar texto antes del formato
- mencionar planes, precios o productos específicos

La respuesta al cliente debe ser genérica y natural.
NO inventes detalles comerciales del negocio.

SIEMPRE debes continuar directamente así:

"perfecto, mira, esto sería respondiendo a tu cliente: ..."

################################"""


DEMO_CLOSURE_TEXT = (
    "Ya viste cómo respondería en tu negocio.\n\n"
    "Ahora piensa en todos los mensajes que te llegan y el tiempo que se te va respondiendo uno por uno… ahí es donde se te están yendo ventas.\n\n"
    "Si quieres lo dejamos funcionando contigo y ves cómo empieza a responder por ti desde hoy."
)


class DemoRepositoryPort(Protocol):
    def activate(self, *, tenant_slug: str, user_id: str) -> None:
        ...

    def consume(self, *, tenant_slug: str, user_id: str) -> bool:
        ...

    def clear(self, *, tenant_slug: str, user_id: str) -> None:
        ...


class DemoDomainService:
    ACTIVATION_SIGNALS = (
        "quiero una prueba",
        "quiero prueba",
        "quiero demo",
        "hagamos una prueba",
        "haz una prueba",
        "quiero ver una prueba",
    )

    DEMO_RESPONSE = (
        "Perfecto, activamos demo en vivo para tu negocio.\n\n"
        "Escribeme como si fueras un cliente real y te respondo en modo venta.\n\n"
        "Desde aqui seguimos en demo sin salir del flujo comercial."
    )

    def __init__(self, repository: DemoRepositoryPort) -> None:
        self._repository = repository

    @staticmethod
    def is_enabled(tenant) -> bool:
        # CRITICAL RULE: demo mode is only available for asesor_ai_prod.
        # Other tenants must remain in normal AI-first flow and never auto-activate demo.
        return str(getattr(tenant, "slug", "")).strip().lower() == "asesor_ai_prod"

    def should_activate(self, tenant, user_message: str) -> bool:
        if not self.is_enabled(tenant):
            return False
        text = " ".join(str(user_message or "").strip().lower().split())
        if not text:
            return False
        return any(signal in text for signal in self.ACTIVATION_SIGNALS)

    def activate(self, tenant_slug: str, user_id: str) -> None:
        self._repository.activate(tenant_slug=tenant_slug, user_id=user_id)

    def consume(self, tenant_slug: str, user_id: str) -> bool:
        return self._repository.consume(tenant_slug=tenant_slug, user_id=user_id)

    def clear(self, tenant_slug: str, user_id: str) -> None:
        self._repository.clear(tenant_slug=tenant_slug, user_id=user_id)

    @classmethod
    def handle(cls) -> str:
        return cls.DEMO_RESPONSE
