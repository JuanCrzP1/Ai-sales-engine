"""La API y la interfaz del panel solo escuchan en este equipo, comprobado contra sus servidores reales, por IPv4 e IPv6.

Se intenta conectar desde este equipo a cada una de sus direcciones. Un servidor de control abierto a todas las interfaces demuestra
que el método detecta una exposición: si el control no responde, un rechazo no probaría nada.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

ROOT_DIR = Path(__file__).resolve().parents[1]
RUN_SCRIPT = ROOT_DIR / "scripts" / "run_admin_api.py"
WEB_DIR = ROOT_DIR / "apps" / "admin-web"
VITE = WEB_DIR / "node_modules" / "vite" / "bin" / "vite.js"


def _own_addresses(family: socket.AddressFamily) -> list[str]:
    """Las direcciones de este equipo, sin las locales."""
    try:
        found = {info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, family)}
    except OSError:
        found = set()
    if family == socket.AF_INET:
        with socket.socket(family, socket.SOCK_DGRAM) as probe:
            try:
                probe.connect(("192.0.2.1", 9))  # UDP no envía nada: solo pregunta por qué interfaz saldría.
                found.add(probe.getsockname()[0])
            except OSError:
                pass
    return sorted(address for address in found if not address.startswith("127.") and address not in ("0.0.0.0", "::1"))


def _ipv6_available() -> bool:
    if not socket.has_ipv6:
        return False
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as probe:
            probe.bind(("::1", 0))
        return True
    except OSError:
        return False


def _connects(address: str, port: int, family: socket.AddressFamily) -> bool:
    with socket.socket(family, socket.SOCK_STREAM) as probe:
        # En Windows, un puerto cerrado tarda unos 2 s en rechazar la conexión.
        probe.settimeout(3)
        try:
            probe.connect((address, port))
            return True
        except OSError:
            return False


def _responding(addresses: list[str], port: int, family: socket.AddressFamily = socket.AF_INET) -> list[str]:
    if not addresses:
        return []
    with ThreadPoolExecutor(max_workers=len(addresses)) as pool:
        answers = list(pool.map(lambda address: _connects(address, port, family), addresses))
    return [address for address, answered in zip(addresses, answers) if answered]


class _Control:
    """Servidor de control: acepta y cierra cada conexión. Si no las aceptara, se llenaría su cola y rechazaría las siguientes."""

    def __init__(self, host: str, family: socket.AddressFamily = socket.AF_INET) -> None:
        self.host, self.family = host, family

    def __enter__(self) -> "_Control":
        self.sock = socket.socket(self.family, socket.SOCK_STREAM)
        if self.family == socket.AF_INET6:
            self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        self.sock.bind((self.host, 0))
        self.sock.listen(32)
        self.sock.settimeout(0.1)
        self.port = self.sock.getsockname()[1]
        self.finished = threading.Event()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        return self

    def _serve(self) -> None:
        while not self.finished.is_set():
            try:
                connection, _address = self.sock.accept()
                connection.close()
            except OSError:
                continue

    def __exit__(self, *_details) -> None:
        self.finished.set()
        self.thread.join(timeout=2)
        self.sock.close()


@pytest.fixture
def own_ipv4() -> list[str]:
    addresses = _own_addresses(socket.AF_INET)
    if not addresses:
        pytest.skip("este equipo no tiene direcciones IPv4 fuera de loopback")
    return addresses


@pytest.fixture
def ipv6_targets() -> list[str]:
    if not _ipv6_available():
        pytest.skip("este equipo no tiene IPv6")
    return ["::1", *_own_addresses(socket.AF_INET6)]


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _wait_until_open(process: subprocess.Popen, port: int, seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"el servidor terminó antes de abrir el puerto, con código {process.returncode}")
        if _connects("127.0.0.1", port, socket.AF_INET):
            return
        time.sleep(0.2)
    raise AssertionError("el servidor no abrió el puerto a tiempo")


def _assert_only_on_loopback(port: int, ipv4: list[str]) -> None:
    assert _responding(["127.0.0.1"], port) == ["127.0.0.1"]
    assert _responding(ipv4, port) == []
    if _ipv6_available():
        assert _responding(["::1", *_own_addresses(socket.AF_INET6)], port, socket.AF_INET6) == []


def test_a_server_open_to_every_interface_answers_on_all_of_them(own_ipv4):
    with _Control("0.0.0.0") as control:
        assert _responding(own_ipv4, control.port) == own_ipv4


def test_the_order_of_the_interfaces_does_not_change_the_result(own_ipv4):
    with _Control("0.0.0.0") as control:
        assert _responding(list(reversed(own_ipv4)), control.port) == list(reversed(own_ipv4))
        assert _responding(own_ipv4, control.port) == own_ipv4


def test_a_server_open_to_every_ipv6_interface_answers_on_all_of_them(ipv6_targets):
    with _Control("::", socket.AF_INET6) as control:
        assert _responding(ipv6_targets, control.port, socket.AF_INET6) == ipv6_targets


def test_a_server_on_loopback_does_not_answer_on_the_other_interfaces(own_ipv4):
    with _Control("127.0.0.1") as control:
        assert _responding(["127.0.0.1"], control.port) == ["127.0.0.1"]
        assert _responding(own_ipv4, control.port) == []


def test_a_server_on_ipv6_loopback_does_not_answer_on_the_other_ipv6_interfaces(ipv6_targets):
    with _Control("::1", socket.AF_INET6) as control:
        assert _responding(ipv6_targets, control.port, socket.AF_INET6) == ["::1"]


def test_the_real_api_only_listens_on_loopback(tmp_path, own_ipv4):
    port = _free_port()
    env = {
        **os.environ,
        "BUSINESS_CONFIG_SECRETS_KEY": Fernet.generate_key().decode(),
        "BUSINESS_CONFIG_DATABASE_URL": f"sqlite:///{(tmp_path / 'red.sqlite3').as_posix()}",
        "ADMIN_API_PORT": str(port),
    }
    server = subprocess.Popen([sys.executable, str(RUN_SCRIPT)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    try:
        _wait_until_open(server, port)
        _assert_only_on_loopback(port, own_ipv4)
    finally:
        server.terminate()
        server.wait(timeout=20)


@pytest.mark.skipif(not VITE.is_file() or shutil.which("node") is None, reason="sin las dependencias del panel: se instalan con 'npm ci' en apps/admin-web")
def test_the_real_dashboard_only_listens_on_loopback(own_ipv4):
    port = _free_port()
    env = {**os.environ, "BROWSER": "none"}
    server = subprocess.Popen(["node", str(VITE), "--port", str(port), "--strictPort"], cwd=WEB_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    try:
        _wait_until_open(server, port)
        _assert_only_on_loopback(port, own_ipv4)
    finally:
        server.terminate()
        server.wait(timeout=20)
