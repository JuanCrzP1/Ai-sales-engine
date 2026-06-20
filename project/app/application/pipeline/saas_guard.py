from __future__ import annotations

PLAN_LIMITS: dict[str, int | None] = {
    "starter": 2000,
    "pro": 10000,
    "enterprise": None,  # unlimited
}


class SaaSGuard:
    def __init__(self, *, subscription_repo, usage_repo) -> None:
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo

    def check_access(self, tenant_key: str) -> tuple[bool, str | dict | None]:
        if not self.subscription_repo.is_active(tenant_key):
            return False, "subscription_inactive"

        plan_code = self.subscription_repo.get_plan_code(tenant_key)
        limit = PLAN_LIMITS.get(plan_code) if plan_code in PLAN_LIMITS else None

        if not self.usage_repo.can_send(tenant_key, max_messages=limit):
            return False, {
                "source": "saas_guard_limit_reached",
                "plan_code": plan_code,
                "limit": limit,
            }

        # NOTA: el incremento de uso NO ocurre aquí. check_access SOLO verifica acceso.
        # El consumo de cuota se registra con record_usage() únicamente cuando el flujo
        # produjo una respuesta válida (ver AIPipeline.run).
        return True, None

    def record_usage(self, tenant_key: str) -> None:
        """Registra el consumo de un mensaje para el tenant.

        Se invoca SOLO tras generar una respuesta válida al usuario, de modo que
        fallos de IA/proveedor o excepciones del pipeline no descuenten cuota.
        """
        self.usage_repo.increment(tenant_key)
