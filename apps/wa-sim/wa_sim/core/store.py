"""Guarda el estado del simulador en `state.json`: sobrevive a reinicios, como una sesión de WhatsApp de verdad."""
from __future__ import annotations

import json
import threading
from pathlib import Path

from wa_sim.core.models import State


class SimulatorStore:
    def __init__(self, data_dir: Path | None) -> None:
        # Sin carpeta (en las pruebas), todo queda en memoria.
        self._path = data_dir / "state.json" if data_dir else None
        self._lock = threading.RLock()
        self._state = self._load()

    def _load(self) -> State:
        if self._path and self._path.is_file():
            try:
                return State.from_dict(json.loads(self._path.read_text(encoding="utf-8")))
            except (ValueError, TypeError):
                return State()
        return State()

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    @property
    def state(self) -> State:
        return self._state

    def save(self) -> None:
        if not self._path:
            return
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self._path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self._state.to_dict(), ensure_ascii=False), encoding="utf-8")
            temporary.replace(self._path)

    def reset(self) -> None:
        with self._lock:
            self._state = State()
            self.save()
