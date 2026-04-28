from __future__ import annotations


class SaaSGuard:
    def __init__(self, *, subscription_repo, usage_repo) -> None:
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo

    def check_access(self, tenant_key: str) -> tuple[bool, str | None]:
        if not self.subscription_repo.is_active(tenant_key):
            return False, "subscription_inactive"
        if not self.usage_repo.can_send(tenant_key):
            return False, "usage_limit"
        self.usage_repo.increment(tenant_key)
        return True, None
