from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OperationalState:
    """Minimal carrier for the active operational process in a conversation turn."""

    active_process: str = ""   # payment | demo | onboarding | activation | handoff
    active_option: str = ""    # nequi | daviplata | link | transferencia | bank | breb
    pending_action: str = ""   # confirm_method | report_payment | continue_demo | ...
    expires_at: datetime | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        if not self.active_process:
            return False
        if self.expires_at is None:
            return True
        effective_now = now or datetime.now(timezone.utc)
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return effective_now < exp

    def to_dict(self) -> dict:
        return {
            "active_process": self.active_process,
            "active_option": self.active_option,
            "pending_action": self.pending_action,
            "expires_at": self.expires_at.isoformat() if self.expires_at else "",
        }

    @staticmethod
    def from_dict(data: dict) -> "OperationalState":
        if not isinstance(data, dict):
            return OperationalState()
        expires_at: datetime | None = None
        raw_exp = data.get("expires_at") or ""
        if raw_exp:
            try:
                expires_at = datetime.fromisoformat(str(raw_exp))
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                expires_at = None
        return OperationalState(
            active_process=str(data.get("active_process") or "").strip().lower(),
            active_option=str(data.get("active_option") or "").strip().lower(),
            pending_action=str(data.get("pending_action") or "").strip().lower(),
            expires_at=expires_at,
        )
