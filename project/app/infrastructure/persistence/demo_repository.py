from __future__ import annotations


class DemoRepository:
    """In-memory repository; interface lista para persistencia SQL."""

    _demo_mode_by_user: dict[tuple[str, str], bool] = {}

    @staticmethod
    def _key(*, tenant_slug: str, user_id: str) -> tuple[str, str] | None:
        normalized_slug = str(tenant_slug or "").strip().lower()
        normalized_user = str(user_id or "").strip().lower()
        if not normalized_slug or not normalized_user:
            return None
        return normalized_slug, normalized_user

    def activate(self, *, tenant_slug: str, user_id: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if key:
            self._demo_mode_by_user[key] = True

    def consume(self, *, tenant_slug: str, user_id: str) -> bool:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if not key or not self._demo_mode_by_user.get(key):
            return False
        self._demo_mode_by_user[key] = False
        return True

    def clear(self, *, tenant_slug: str, user_id: str) -> None:
        key = self._key(tenant_slug=tenant_slug, user_id=user_id)
        if key:
            self._demo_mode_by_user.pop(key, None)
