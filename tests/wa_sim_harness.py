"""Arnés de los recorridos con el WhatsApp simulado (`apps/wa-sim`): levanta el simulador y el motor como servidores de verdad (en
hilos de este proceso, en puertos libres de localhost), un teléfono de prueba para hacer de cliente y un modelo de IA con respuestas
fijas, para que todo lo demás corra con su código real.

- El simulador es un uazapi falso: el panel y el motor le hablan con su cliente real de uazapi y él les avisa como uazapi.
- El «modelo» (`ScriptedModel`) reemplaza solo la llamada a OpenRouter: el prompt, la memoria, la entrega de los datos de pago, el
  paso a una persona y los guardas del motor son los reales.
- Nada sale de este equipo: sin WhatsApp, sin OpenRouter, sin correos.
"""
from __future__ import annotations

import json
import re
import socket
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "apps" / "wa-sim"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from wa_sim.config import SimConfig  # noqa: E402
from wa_sim.server import SimulatorApp, create_simulator  # noqa: E402


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class ServerThread:
    """Un servidor ASGI de verdad en un hilo, solo en 127.0.0.1."""

    def __init__(self, app, port: int) -> None:
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="off"))
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self) -> "ServerThread":
        self._thread.start()
        deadline = time.monotonic() + 10
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("el servidor de prueba no arrancó")
            time.sleep(0.02)
        return self

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)


def start_simulator(*, receipt_seconds: float = 0.2) -> tuple[SimulatorApp, ServerThread]:
    simulator = create_simulator(SimConfig(receipt_seconds=receipt_seconds), persist=False)
    return simulator, ServerThread(simulator.app, free_port()).start()


def wait_for(check: Callable[[], object], *, timeout: float = 10.0, what: str = "algo") -> object:
    """Espera hasta que `check` devuelva algo verdadero; si no, falla diciendo qué no pasó."""
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result:
            return result
        if time.monotonic() > deadline:
            raise AssertionError(f"No pasó a tiempo: {what}")
        time.sleep(0.05)


class Phone:
    """El teléfono de prueba, hablando con el simulador como la página del navegador."""

    def __init__(self, base_url: str) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=30.0)

    def state(self) -> dict:
        return self._http.get("/_sim/state").json()

    def instance(self) -> dict | None:
        instances = self.state()["instances"]
        return instances[0] if instances else None

    def scan(self, token: str, phone: str = "573110000000") -> dict:
        response = self._http.post(f"/_sim/instances/{token}/scan", json={"phone": phone, "profile_name": "Negocio de prueba"})
        response.raise_for_status()
        return response.json()

    def add_client(self, phone: str, name: str) -> None:
        self._http.post("/_sim/clients", json={"phone": phone, "name": name}).raise_for_status()

    def write(self, token: str, phone: str, text: str = "", **file) -> dict:
        response = self._http.post(f"/_sim/chats/{token}/{phone}/write", json={"text": text, **file})
        response.raise_for_status()
        return response.json()

    def chat(self, token: str, phone: str) -> list[dict]:
        return self._http.get(f"/_sim/chats/{token}/{phone}").json()["messages"]

    def from_business(self, token: str, phone: str) -> list[dict]:
        return [message for message in self.chat(token, phone) if message["author"] == "business"]

    def open(self, token: str, phone: str) -> list[str]:
        return self._http.post(f"/_sim/chats/{token}/{phone}/open").json()["read"]

    def wait_reply(self, token: str, phone: str, after: int, *, what: str, timeout: float = 15.0) -> dict:
        """El siguiente mensaje del negocio después de los `after` que ya había."""
        found = wait_for(lambda: self.from_business(token, phone)[after:], timeout=timeout, what=what)
        return found[0]  # type: ignore[index]

    def close(self) -> None:
        self._http.close()


@dataclass
class ScriptedModel:
    """El modelo de IA con respuestas fijas: la primera regla cuyo patrón aparece en el mensaje del cliente decide la respuesta (en el
    formato estructurado que pide el motor). Anota cada mensaje que «leyó» y el prompt que recibió."""

    rules: list[tuple[str, dict]] = field(default_factory=list)
    default: dict = field(default_factory=lambda: {"response": "Claro, te ayudo con eso.", "intent": "info", "metadata": {}})
    seen: list[str] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)

    def generate(self, prompt: str, *, user_message: str, bot_config=None, history=None) -> str:
        self.seen.append(user_message)
        self.prompts.append(prompt)
        lowered = user_message.lower()
        reply = next((reply for pattern, reply in self.rules if re.search(pattern, lowered)), self.default)
        return json.dumps(reply, ensure_ascii=False)


@dataclass
class Report:
    """El informe en español de un recorrido: cada paso con lo que se comprobó, o por qué falló."""

    title: str
    steps: list[tuple[str, bool, str]] = field(default_factory=list)

    def step(self, name: str, check: Callable[[], str]) -> None:
        try:
            detail = check() or ""
        except Exception as error:  # noqa: BLE001 - el informe dice qué falló y la prueba falla igual
            self.steps.append((name, False, str(error)))
            raise
        self.steps.append((name, True, detail))

    def markdown(self) -> str:
        lines = [f"## {self.title}", ""]
        for name, ok, detail in self.steps:
            lines.append(f"- {'✅' if ok else '❌'} **{name}**" + (f": {detail}" if detail else ""))
        return "\n".join(lines) + "\n"
