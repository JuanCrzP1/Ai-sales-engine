"""API local del panel: conecta `apps/admin-web` con BusinessConfig v1 y su persistencia.

Usa el servicio y el almacén reales sobre un archivo SQLite temporal, con una clave de cifrado generada para cada prueba.
Los datos de pago son ficticios. No hay modelo de IA ni salida a la red. Las aserciones sobre datos de pago comparan con
marcas ficticias o conteos: si una falla, el informe no debe mostrar valores reales.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import ADMIN_WEB_PORT, PANEL_ORIGINS, create_app
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.errors import SecretResolutionError
from app.domain.business_config.payment_data import payment_values
from app.infrastructure.business_config.database import (
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.secrets_key import KEY_FILE, ensure_secrets_key
from app.infrastructure.business_config.tables import business_config_secrets, business_configs

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "project" / "config" / "contracts" / "v1" / "business-config.schema.json"
RUN_SCRIPT = ROOT_DIR / "scripts" / "run_admin_api.py"

BASE_URL = "http://127.0.0.1:8010"
LOCAL_CLIENT = ("127.0.0.1", 50000)
LINK = "https://pagos-ficticios.example/MARCA_LINK_DE_PAGO"
NUMBER = "3000000999"
ACCOUNT = "9000000001234"
LINK_REF = "secret_store:principal.link"
NUMBER_REF = "secret_store:principal.nequi.number"
ACCOUNT_REF = "secret_store:principal.bank.account"
ALL_VALUES = {LINK_REF: LINK, NUMBER_REF: NUMBER, ACCOUNT_REF: ACCOUNT}


def plans_document(slug: str, *, name: str = "Negocio ficticio", with_payments: bool = True) -> dict:
    """Documento válido de un negocio que vende planes, como lo envía el panel."""
    profile = {
        "id": "principal",
        "link": {"secret_ref": LINK_REF},
        "transfer_enabled": True,
        "transfer_methods": [
            {"type": "nequi", "number": {"secret_ref": NUMBER_REF}},
            {"type": "bank", "bank": "Banco Ficticio", "account_type": "ahorros", "account_number": {"secret_ref": ACCOUNT_REF}},
        ],
    }
    return {
        "schema_version": "1.0",
        "tenant_slug": slug,
        "identity": {
            "name": name,
            "industry": "servicios de prueba",
            "description": "Un negocio ficticio para las pruebas.",
            "value_proposition": "Resultados ficticios en poco tiempo.",
        },
        "offer": {
            "model": "plans",
            "plans": [
                {
                    "id": "basico",
                    "name": "Plan básico",
                    "prices": [{"currency": "COP", "monthly": 100000}],
                    "includes": ["Soporte"],
                    "payment_profile": "principal" if with_payments else None,
                }
            ],
        },
        "terms": {},
        "payments": [profile] if with_payments else [],
        "sales": {},
        "capabilities": {
            "service_channels": ["whatsapp"],
            "actions_support": ["responder_dudas"],
            "closing_methods": {"payment_link": with_payments, "human_handoff": False, "data_collection": True},
            "data_collection": {"enabled": True, "fields": ["nombre"]},
        },
        "messages": {"welcome": {"enabled": False, "text": ""}},
        "response_style": {"length": "short"},
        "knowledge": {"faqs": []},
        "inventory": {"items": []},
    }


def catalog_document(slug: str) -> dict:
    document = plans_document(slug, with_payments=False)
    document["offer"] = {
        "model": "catalog",
        "catalog": {
            "categories": [{"id": "bebidas", "name": "Bebidas"}],
            "items": [{"id": "cafe", "name": "Café", "category": "bebidas", "prices": [{"currency": "COP", "amount": 5000}], "features": ["Tamaño 12 oz"]}],
        },
    }
    return document


class Local:
    """Una instancia de la API sobre la base temporal; `restart` simula reiniciar el backend."""

    def __init__(self, path: Path) -> None:
        self.url = f"sqlite:///{path.as_posix()}"
        self.path = path
        self.key = Fernet.generate_key().decode()
        self.start()

    def start(self) -> None:
        self.engine = create_business_config_engine(self.url)
        create_local_schema(self.engine)
        self.app = create_app(build_business_config_service(self.engine, secrets_key=self.key))
        self.client = TestClient(self.app, base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False)

    def restart(self) -> None:
        self.engine.dispose()
        self.start()

    @property
    def service(self) -> BusinessConfigService:
        return build_business_config_service(self.engine, secrets_key=self.key)


@pytest.fixture
def api(tmp_path):
    local = Local(tmp_path / "panel.sqlite3")
    yield local
    local.engine.dispose()


def _create(api: Local, slug: str = "cafe_aroma", name: str = "Café Aroma"):
    response = api.client.post("/api/businesses", json={"slug": slug, "name": name})
    assert response.status_code == 201
    return response


def _save(api: Local, slug: str, document: dict, *, values: dict | None = None, base: int | None = None):
    return api.client.put(f"/api/businesses/{slug}/config", json={"document": document, "payment_values": values or {}, "base_version": base})


def _create_with_document(api: Local, slug: str = "cafe_aroma", *, values: dict | None = ALL_VALUES) -> dict:
    _create(api, slug)
    response = _save(api, slug, plans_document(slug), values=values)
    assert response.status_code == 200, response.text
    return response.json()


def _load(api: Local, slug: str = "cafe_aroma") -> dict:
    response = api.client.get(f"/api/businesses/{slug}/config")
    assert response.status_code == 200
    return response.json()


def _edit(api: Local, change, slug: str = "cafe_aroma", *, values: dict | None = None):
    """Carga lo guardado, aplica el cambio y lo guarda: lo mismo que hace el panel."""
    stored = _load(api, slug)
    document = copy.deepcopy(stored["document"])
    change(document)
    return _save(api, slug, document, values=values, base=stored["latest_version"])


# 1 y 2. Crear un negocio y recuperarlo.


def test_create_list_and_recover_a_business(api):
    created = _create(api).json()
    assert created == {"slug": "cafe_aroma", "name": "Café Aroma", "latest_version": None, "draft_version": None, "published_version": None}
    assert [item["slug"] for item in api.client.get("/api/businesses").json()] == ["cafe_aroma"]
    recovered = _load(api)
    assert recovered["document"] is None
    assert recovered["version"] is None


@pytest.mark.parametrize(
    ("slug", "name", "path"),
    [
        pytest.param("Con Mayusculas", "Nombre", "slug", id="identificador_con_mayusculas_y_espacios"),
        pytest.param("../otro", "Nombre", "slug", id="identificador_con_ruta"),
        pytest.param("", "Nombre", "slug", id="identificador_vacio"),
        pytest.param("negocio", "   ", "name", id="nombre_vacio"),
    ],
)
def test_a_business_with_invalid_data_is_not_created(api, slug, name, path):
    response = api.client.post("/api/businesses", json={"slug": slug, "name": name})
    assert response.status_code == 422
    assert response.json()["issues"][0]["path"] == path
    assert api.client.get("/api/businesses").json() == []


def test_identifiers_cannot_be_duplicated(api):
    _create(api)
    response = api.client.post("/api/businesses", json={"slug": "cafe_aroma", "name": "Otro"})
    assert response.status_code == 409
    assert response.json()["code"] == "duplicate"
    assert len(api.client.get("/api/businesses").json()) == 1


def test_unknown_businesses_are_reported(api):
    assert api.client.get("/api/businesses/no_existe/config").status_code == 404
    assert _save(api, "no_existe", plans_document("no_existe")).status_code == 404


class _Unreachable:
    """Cualquier acceso falla: demuestra que la petición no llegó a la persistencia."""

    def __getattr__(self, name):
        raise AssertionError("un identificador inválido llegó al almacén")


@pytest.mark.parametrize("slug", ["..%2F..%2Fetc", "con%20espacio", "MAYUSCULAS"])
def test_routes_with_invalid_identifiers_do_not_reach_the_store(api, slug, monkeypatch):
    monkeypatch.setattr(api.app.state.service, "_storage", _Unreachable())
    monkeypatch.setattr(api.app.state.service, "_secrets", _Unreachable())
    assert api.client.get(f"/api/businesses/{slug}/config").status_code == 404
    assert api.client.get(f"/api/businesses/{slug}/versions").status_code == 404
    assert api.client.post(f"/api/businesses/{slug}/rollback").status_code == 404
    assert api.client.delete(f"/api/businesses/{slug}", params={"confirm": slug}).status_code == 404


# 3 a 6. Editar, guardar, reiniciar y comprobar que persiste.


def test_saving_creates_a_version_and_the_changes_survive_a_restart(api):
    saved = _create_with_document(api)
    assert saved["version"]["version"] == 1
    assert saved["version"]["status"] == "draft"

    response = _edit(api, lambda document: document["identity"].update(name="Nombre editado"))
    assert response.status_code == 200
    assert response.json()["version"]["version"] == 2

    api.restart()

    recovered = _load(api)
    assert recovered["document"]["identity"]["name"] == "Nombre editado"
    assert recovered["version"]["version"] == 2
    assert recovered["name"] == "Nombre editado"
    assert [item["version"] for item in api.client.get("/api/businesses/cafe_aroma/versions").json()] == [1, 2]


def test_the_real_server_keeps_the_data_after_a_restart_and_only_listens_locally(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = {
        **os.environ,
        "BUSINESS_CONFIG_SECRETS_KEY": Fernet.generate_key().decode(),
        "BUSINESS_CONFIG_DATABASE_URL": f"sqlite:///{(tmp_path / 'servidor.sqlite3').as_posix()}",
        "ADMIN_API_PORT": str(port),
    }
    base = f"http://127.0.0.1:{port}"

    def _start():
        process = subprocess.Popen([sys.executable, str(RUN_SCRIPT)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _attempt in range(100):
            try:
                if httpx.get(f"{base}/api/health", timeout=1).status_code == 200:
                    return process
            except httpx.TransportError:
                time.sleep(0.2)
        process.kill()
        raise AssertionError("la API no arrancó")

    server = _start()
    try:
        assert httpx.post(f"{base}/api/businesses", json={"slug": "cafe_aroma", "name": "Café Aroma"}).status_code == 201
        saved = httpx.put(f"{base}/api/businesses/cafe_aroma/config", json={"document": plans_document("cafe_aroma"), "payment_values": ALL_VALUES})
        assert saved.status_code == 200
        assert LINK not in saved.text
    finally:
        server.terminate()
        server.wait(timeout=20)
    with pytest.raises(httpx.TransportError):
        httpx.get(f"{base}/api/health", timeout=1)

    server = _start()
    try:
        recovered = httpx.get(f"{base}/api/businesses/cafe_aroma/config").json()
        assert recovered["document"]["identity"]["name"] == "Negocio ficticio"
        assert httpx.get(f"{base}/api/businesses/cafe_aroma/review").json()["compiles"] is True
        lan_address = socket.gethostbyname(socket.gethostname())
        if not lan_address.startswith("127."):
            with pytest.raises(OSError):
                socket.create_connection((lan_address, port), timeout=1).close()
    finally:
        server.terminate()
        server.wait(timeout=20)


def _load_run_script():
    spec = importlib.util.spec_from_file_location("run_admin_api_script", RUN_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _empty_engine(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'clave.sqlite3').as_posix()}")
    create_local_schema(engine)
    return engine


def test_the_first_start_creates_the_key_once_without_showing_it(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BUSINESS_CONFIG_SECRETS_KEY", "")
    engine = _empty_engine(tmp_path)
    key_file = tmp_path / "perfil" / ".ai-sales-engine" / "secreto.key"

    assert ensure_secrets_key(engine, key_file) is True
    created = key_file.read_text(encoding="ascii")
    Fernet(created.encode())
    assert os.environ["BUSINESS_CONFIG_SECRETS_KEY"] == created
    assert created not in capsys.readouterr().out

    monkeypatch.setenv("BUSINESS_CONFIG_SECRETS_KEY", "")
    assert ensure_secrets_key(engine, key_file) is False
    assert key_file.read_text(encoding="ascii") == created
    assert os.environ["BUSINESS_CONFIG_SECRETS_KEY"] == created
    engine.dispose()


def test_the_key_file_lives_outside_the_repository():
    key_file = KEY_FILE
    assert key_file.parent.name == ".ai-sales-engine"
    assert ROOT_DIR not in key_file.resolve().parents


def test_the_key_of_the_environment_wins_and_no_file_is_created(tmp_path, monkeypatch):
    chosen = Fernet.generate_key().decode()
    monkeypatch.setenv("BUSINESS_CONFIG_SECRETS_KEY", chosen)
    engine = _empty_engine(tmp_path)
    key_file = tmp_path / "perfil" / "secreto.key"
    ensure_secrets_key(engine, key_file)
    assert os.environ["BUSINESS_CONFIG_SECRETS_KEY"] == chosen
    assert not key_file.exists()
    engine.dispose()


def test_a_lost_key_is_never_replaced_when_there_is_encrypted_data(tmp_path, monkeypatch):
    monkeypatch.setenv("BUSINESS_CONFIG_SECRETS_KEY", Fernet.generate_key().decode())
    engine = _empty_engine(tmp_path)
    build_business_config_service(engine).create_business("cafe_aroma", "Café Aroma", document=plans_document("cafe_aroma"), payment_values=ALL_VALUES)

    monkeypatch.setenv("BUSINESS_CONFIG_SECRETS_KEY", "")
    key_file = tmp_path / "perfil" / "secreto.key"
    with pytest.raises(SecretResolutionError, match="falta su clave"):
        ensure_secrets_key(engine, key_file)
    assert not key_file.exists()
    engine.dispose()


def test_the_real_server_starts_with_no_key_configured_and_reads_its_data_after_a_restart(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    home = tmp_path / "perfil"
    home.mkdir()
    env = {
        **os.environ,
        "BUSINESS_CONFIG_SECRETS_KEY": "",
        "BUSINESS_CONFIG_DATABASE_URL": f"sqlite:///{(tmp_path / 'servidor.sqlite3').as_posix()}",
        "ADMIN_API_PORT": str(port),
        "HOME": str(home),
        "USERPROFILE": str(home),
    }
    base = f"http://127.0.0.1:{port}"
    output = tmp_path / "salida.txt"

    def _start():
        with output.open("a", encoding="utf-8") as sink:
            process = subprocess.Popen([sys.executable, str(RUN_SCRIPT)], env=env, stdout=sink, stderr=subprocess.STDOUT)
        # El mismo paso de los lanzadores: solo se sigue cuando la API responde.
        waited = subprocess.run([sys.executable, str(RUN_SCRIPT), "--wait"], env=env, capture_output=True, encoding="utf-8", timeout=60)
        if waited.returncode != 0:
            process.kill()
            raise AssertionError("la API no arrancó")
        return process

    server = _start()
    try:
        key = (home / ".ai-sales-engine" / "business_config_secrets.key").read_text(encoding="ascii")
        assert httpx.post(f"{base}/api/businesses", json={"slug": "cafe_aroma", "name": "Café Aroma"}).status_code == 201
        assert httpx.put(f"{base}/api/businesses/cafe_aroma/config", json={"document": plans_document("cafe_aroma"), "payment_values": ALL_VALUES}).status_code == 200
    finally:
        server.terminate()
        server.wait(timeout=20)

    server = _start()
    try:
        assert httpx.get(f"{base}/api/businesses/cafe_aroma/review").json()["compiles"] is True
    finally:
        server.terminate()
        server.wait(timeout=20)
    assert (home / ".ai-sales-engine" / "business_config_secrets.key").read_text(encoding="ascii") == key
    assert key not in output.read_text(encoding="utf-8")


def test_the_server_does_not_start_with_an_invalid_key(tmp_path):
    env = {**os.environ, "BUSINESS_CONFIG_SECRETS_KEY": "no-es-una-clave", "BUSINESS_CONFIG_DATABASE_URL": f"sqlite:///{(tmp_path / 'x.sqlite3').as_posix()}"}
    result = subprocess.run([sys.executable, str(RUN_SCRIPT)], env=env, capture_output=True, encoding="utf-8", timeout=60)
    assert result.returncode == 1
    assert "BUSINESS_CONFIG_SECRETS_KEY" in result.stdout
    assert "no-es-una-clave" not in result.stdout


def test_waiting_for_the_api_fails_when_it_does_not_answer():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert _load_run_script()._wait_until_ready(port, timeout=0.2) == 1


@pytest.mark.parametrize("launcher", ["run_local.bat", "run_local.sh"])
def test_the_launchers_open_the_panel_only_after_the_api_answers(launcher):
    source = (ROOT_DIR / launcher).read_text(encoding="utf-8")
    assert source.index("run_admin_api.py") < source.index("run_admin_api.py\" --wait") < source.index("npm run dev")
    assert "BUSINESS_CONFIG_SECRETS_KEY" not in source


def test_the_unix_launchers_are_executable_in_git():
    """Windows no lo nota, pero sin este permiso `./run_local.sh` falla en macOS y Linux."""
    listed = subprocess.run(["git", "ls-files", "-s", "run_local.sh", "run_local_stop.sh"], cwd=ROOT_DIR, capture_output=True, encoding="utf-8").stdout.splitlines()
    assert [line.split()[0] for line in listed] == ["100755", "100755"]


def test_the_only_launchers_are_the_existing_ones_and_stop_covers_the_api():
    assert sorted(path.name for path in ROOT_DIR.glob("run_*") if path.is_file()) == ["run_local.bat", "run_local.sh", "run_local_stop.sh"]
    stop = (ROOT_DIR / "run_local_stop.sh").read_text(encoding="utf-8")
    assert "admin-api" in stop
    assert "run_admin_api.py" in stop
    # La parada reconoce la interfaz por su puerto: la ventana de los lanzadores y el script para abrir solo el panel deben indicarlo.
    assert "*run*dev*--port*" in stop
    assert "*vite*--port*" in stop
    scripts = json.loads((ROOT_DIR / "apps" / "admin-web" / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert scripts["panel"] == f"vite --port {ADMIN_WEB_PORT} --strictPort"


def test_the_panel_port_is_the_same_wherever_it_is_repeated():
    """La API, Vite y los lanzadores no pueden compartir el puerto de la interfaz: cada uno lo define una vez y aquí se comprueba que
    coincidan. Si uno cambiara solo, el panel no abriría, la parada no lo encontraría o la API rechazaría sus peticiones."""
    definitions = {
        "apps/admin-web/vite.config.ts": f"const ADMIN_WEB_PORT = {ADMIN_WEB_PORT};",
        "run_local.sh": f"ADMIN_WEB_PORT={ADMIN_WEB_PORT}",
        "run_local_stop.sh": f"ADMIN_WEB_PORT={ADMIN_WEB_PORT}",
        "run_local.bat": f"set ADMIN_WEB_PORT={ADMIN_WEB_PORT}",
    }
    sources = {path: (ROOT_DIR / path).read_text(encoding="utf-8") for path in definitions}
    for path, definition in definitions.items():
        assert definition in sources[path].splitlines(), path
    assert "port: ADMIN_WEB_PORT," in sources["apps/admin-web/vite.config.ts"]
    assert "--port $ADMIN_WEB_PORT" in sources["run_local.sh"]
    assert "--port %ADMIN_WEB_PORT%" in sources["run_local.bat"]
    assert {f"http://127.0.0.1:{ADMIN_WEB_PORT}", f"http://localhost:{ADMIN_WEB_PORT}"} <= PANEL_ORIGINS


@pytest.mark.parametrize("guide", ["apps/admin-web/README.md", "docs/operations.md"])
def test_the_guides_open_the_panel_with_an_order_that_works_in_every_shell(guide):
    """En PowerShell, `npm.ps1` pierde el `--`: `run dev -- --port 5180` ejecuta `vite 5180` y arranca sin configuración ni panel."""
    text = (ROOT_DIR / guide).read_text(encoding="utf-8")
    assert "npm --prefix apps/admin-web run panel" in text
    assert "npm --prefix apps/admin-web run dev --" not in text


def test_the_server_address_is_fixed_to_this_computer():
    source = RUN_SCRIPT.read_text(encoding="utf-8")
    assert 'HOST = "127.0.0.1"' in source
    assert "host=HOST" in source


def test_changes_made_elsewhere_are_not_overwritten(api):
    _create_with_document(api)
    stale = _load(api)
    assert _edit(api, lambda document: document["identity"].update(name="Cambio de otra pestaña")).status_code == 200

    document = copy.deepcopy(stale["document"])
    document["identity"]["name"] = "Cambio con datos viejos"
    response = _save(api, "cafe_aroma", document, base=stale["latest_version"])

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert _load(api)["document"]["identity"]["name"] == "Cambio de otra pestaña"


# 7 a 12. Las secciones comerciales del contrato se guardan y se recuperan.


def test_products_and_services_with_prices_and_availability(api):
    _create_with_document(api)
    premium = {
        "id": "premium",
        "name": "Plan premium",
        "description": "Con todo incluido.",
        "target": "Empresas medianas",
        "prices": [
            {"currency": "COP", "implementation": 500000, "monthly": 200000, "first_payment": 150000, "annual": 2000000},
            {"currency": "USD", "monthly": 50},
        ],
        "includes": ["Soporte prioritario"],
        "not_included": ["Publicidad pagada"],
        "payment_profile": "principal",
        "available": False,
    }

    def add_plan(document):
        document["offer"]["plans"][0]["prices"][0]["monthly"] = 120000
        document["offer"]["plans"].append(premium)

    assert _edit(api, add_plan).status_code == 200
    api.restart()
    plans = _load(api)["document"]["offer"]["plans"]
    assert plans[0]["prices"][0]["monthly"] == 120000
    assert plans[1] == premium

    assert _edit(api, lambda document: document["offer"]["plans"].pop()).status_code == 200
    assert [plan["id"] for plan in _load(api)["document"]["offer"]["plans"]] == ["basico"]


def test_catalog_with_categories_variants_and_stock(api):
    _create(api, "tienda")
    assert _save(api, "tienda", catalog_document("tienda")).status_code == 200

    def extend(document):
        document["offer"]["catalog"]["categories"].append({"id": "ropa", "name": "Ropa"})
        document["offer"]["catalog"]["items"].append(
            {"id": "camiseta", "name": "Camiseta", "category": "ropa", "prices": [{"currency": "COP", "amount": 40000}], "available": True}
        )
        document["inventory"] = {
            "track_stock": True,
            "items": [{"product_id": "camiseta", "variants": [{"sku": "CAM-M", "attributes": {"talla": "M"}, "stock": 3, "prices": [{"currency": "COP", "amount": 42000}]}]}],
        }

    assert _edit(api, extend, "tienda").status_code == 200
    stored = _load(api, "tienda")["document"]
    assert [item["id"] for item in stored["offer"]["catalog"]["items"]] == ["cafe", "camiseta"]
    assert stored["inventory"]["items"][0]["variants"][0]["stock"] == 3


def test_promotions_conditions_and_policies(api):
    _create_with_document(api)
    terms = {
        "conditions": ["Domicilio gratis en compras grandes"],
        "price_note": "El precio se confirma al cerrar.",
        "promotions": [{"name": "Lanzamiento", "details": "Descuento del 10 %", "valid_until": "2030-12-31"}],
        "financing": {"available": True, "providers": ["Entidad ficticia"], "options": ["Cuotas"]},
        "policies": {"warranty": "Un año.", "returns": "Treinta días.", "cancellation": "Sin costo."},
    }
    assert _edit(api, lambda document: document.update(terms=terms)).status_code == 200
    assert _load(api)["document"]["terms"] == terms


def test_personality_and_instructions(api):
    _create_with_document(api)
    style = {"tone": "cercano", "voice": "experta", "formality": "formal", "emojis": False, "instructions": ["Trata de usted"], "length": "long", "max_words": 90}

    def change(document):
        document["response_style"] = style
        document["sales"] = {
            "buying_motivation": {"primary": "tiempo", "secondary": "dinero"},
            "benefits": ["Ahorra horas"],
            "arguments": ["Sin contratos"],
            "discovery": {"questions": ["¿Cuántos clientes atiendes?"]},
            "recommendation_rules": [{"when": "Tiene poco presupuesto", "recommend": "basico"}],
            "instructions": ["No prometas plazos"],
        }

    assert _edit(api, change).status_code == 200
    stored = _load(api)["document"]
    assert stored["response_style"] == style
    assert stored["sales"]["instructions"] == ["No prometas plazos"]


def test_frequently_asked_questions(api):
    _create_with_document(api)
    assert _edit(api, lambda document: document["knowledge"].update(faqs=[{"question": "¿Hacen envíos?", "answer": "Sí."}])).status_code == 200
    assert _edit(api, lambda document: document["knowledge"]["faqs"][0].update(answer="Solo en la ciudad.")).status_code == 200
    assert _load(api)["document"]["knowledge"]["faqs"] == [{"question": "¿Hacen envíos?", "answer": "Solo en la ciudad."}]
    assert _edit(api, lambda document: document["knowledge"].update(faqs=[])).status_code == 200
    assert _load(api)["document"]["knowledge"]["faqs"] == []


def test_payment_methods_can_be_kept_replaced_and_removed(api):
    _create_with_document(api)
    first = _load(api)["document"]["payments"][0]

    # Sin valores nuevos, las referencias guardadas siguen igual.
    assert _edit(api, lambda document: document["identity"].update(name="Otro nombre")).status_code == 200
    assert _load(api)["document"]["payments"][0] == first

    # Reemplazar: la referencia cambia y el nuevo valor se usa al compilar; el anterior sigue en su versión.
    link_ref = first["link"]["secret_ref"]
    new_link = "https://pagos-ficticios.example/NUEVO"
    assert _edit(api, lambda document: None, values={link_ref: new_link}).status_code == 200
    latest = _load(api)
    assert latest["document"]["payments"][0]["link"]["secret_ref"] != link_ref
    # El servicio compila lo publicado: se publica para comprobar el valor.
    assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": latest["version"]["version"]}).status_code == 200
    compiled = api.service.compile_sections("cafe_aroma")
    assert new_link in payment_values(compiled)
    assert LINK not in payment_values(compiled)

    # Quitar un método.
    def remove_bank(document):
        document["payments"][0]["transfer_methods"] = [method for method in document["payments"][0]["transfer_methods"] if method["type"] != "bank"]

    assert _edit(api, remove_bank).status_code == 200
    assert [method["type"] for method in _load(api)["document"]["payments"][0]["transfer_methods"]] == ["nequi"]


# Métodos de pago: se reconocen sin exponer el valor, y el valor guardado se conserva hasta que se reemplaza de forma explícita.


def _method(stored: dict, kind: str) -> dict:
    return next(method for method in stored["document"]["payments"][0]["transfer_methods"] if method["type"] == kind)


def _ciphertexts(api: Local) -> dict:
    with api.engine.connect() as conn:
        return {row.ref_key: row.ciphertext for row in conn.execute(select(business_config_secrets.c.ref_key, business_config_secrets.c.ciphertext)).all()}


def test_saved_payment_data_is_reported_only_masked(api, caplog):
    caplog.set_level("DEBUG")
    saved = _create_with_document(api)
    fields = saved["payment_fields"]
    link_ref = saved["document"]["payments"][0]["link"]["secret_ref"]
    number_ref = _method(saved, "nequi")["number"]["secret_ref"]
    account_ref = _method(saved, "bank")["account_number"]["secret_ref"]
    assert fields == {
        link_ref: {"status": "configured", "masked": "https://pagos-ficticios.example/••••"},
        number_ref: {"status": "configured", "masked": "••••0999"},
        account_ref: {"status": "configured", "masked": "••••1234"},
    }

    # Todo lo que devuelve la configuración lleva lo mismo, y ningún valor completo: tampoco tras reiniciar ni en los registros.
    published = api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1}).json()
    restored = api.client.post("/api/businesses/cafe_aroma/versions/1/restore").json()
    api.restart()
    reopened = _load(api)
    for response in (published, restored, reopened):
        assert response["payment_fields"] == fields
    text = json.dumps([saved, published, restored, reopened], ensure_ascii=False)
    for value in ALL_VALUES.values():
        assert value not in text
        assert value not in caplog.text


def test_editing_descriptive_data_keeps_the_encrypted_value(api):
    saved = _create_with_document(api)
    ciphertexts = _ciphertexts(api)

    def change(document):
        _method({"document": document}, "bank").update(bank="Banco Otro", account_type="corriente", label="Cuenta de la tienda")

    response = _edit(api, change)
    assert response.status_code == 200
    stored = response.json()
    assert _method(stored, "bank") == {**_method(saved, "bank"), "bank": "Banco Otro", "account_type": "corriente", "label": "Cuenta de la tienda"}
    assert stored["payment_fields"] == saved["payment_fields"]
    assert _ciphertexts(api) == ciphertexts, "sin un valor nuevo no se vuelve a cifrar nada"


def test_replacing_a_value_is_explicit_and_each_version_keeps_its_own(api):
    saved = _create_with_document(api)
    old_ref = _method(saved, "nequi")["number"]["secret_ref"]
    response = _edit(api, lambda document: None, values={old_ref: "3111111234"})
    assert response.status_code == 200
    stored = response.json()
    new_ref = _method(stored, "nequi")["number"]["secret_ref"]
    assert new_ref != old_ref
    assert stored["payment_fields"][new_ref] == {"status": "configured", "masked": "••••1234"}
    assert old_ref not in stored["payment_fields"]
    assert "3111111234" not in response.text
    # Los demás datos siguen igual, y recuperar la versión anterior trae también su dato.
    assert _method(stored, "bank") == _method(saved, "bank")
    restored = api.client.post("/api/businesses/cafe_aroma/versions/1/restore").json()
    assert restored["payment_fields"][_method(restored, "nequi")["number"]["secret_ref"]]["masked"] == "••••0999"


@pytest.mark.parametrize("empty", ["", "   "], ids=["vacio", "solo_espacios"])
def test_an_empty_value_never_deletes_stored_data(api, empty):
    saved = _create_with_document(api)
    ciphertexts = _ciphertexts(api)
    ref = _method(saved, "nequi")["number"]["secret_ref"]
    response = _edit(api, lambda document: None, values={ref: empty})
    assert response.status_code == 422
    stored = _load(api)
    assert stored["version"]["version"] == 1
    assert stored["payment_fields"] == saved["payment_fields"]
    assert _ciphertexts(api) == ciphertexts


def test_methods_can_be_deactivated_activated_and_removed(api):
    saved = _create_with_document(api)
    plan_values = lambda: payment_values(api.service.compile_sections("cafe_aroma"))  # noqa: E731

    def publish_latest() -> None:
        assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": _load(api)["latest_version"]}).status_code == 200

    # Desactivar: los datos se conservan e identifican, pero no se ofrecen.
    def deactivate(document):
        document["payments"][0]["link_enabled"] = False
        _method({"document": document}, "nequi")["enabled"] = False

    paused = _edit(api, deactivate).json()
    assert paused["payment_fields"] == saved["payment_fields"]
    assert _method(paused, "nequi")["enabled"] is False
    publish_latest()
    assert plan_values() == [ACCOUNT]

    # Activar: vuelven los mismos datos, sin escribirlos de nuevo. El panel envía null, y el documento queda como estaba.
    def activate(document):
        document["payments"][0]["link_enabled"] = None
        _method({"document": document}, "nequi")["enabled"] = None

    active = _edit(api, activate).json()
    assert active["document"]["payments"] == saved["document"]["payments"]
    publish_latest()
    assert sorted(plan_values()) == sorted([LINK, NUMBER, ACCOUNT])

    # Eliminar: deja de aparecer en la versión nueva. Las anteriores conservan el suyo.
    def remove(document):
        document["payments"][0]["transfer_methods"] = [method for method in document["payments"][0]["transfer_methods"] if method["type"] != "nequi"]

    removed = _edit(api, remove).json()
    assert _method(saved, "nequi")["number"]["secret_ref"] not in removed["payment_fields"]
    publish_latest()
    assert NUMBER not in plan_values()

    # Todo sobrevive al reinicio.
    api.restart()
    assert _load(api)["payment_fields"] == removed["payment_fields"]
    assert api.client.post("/api/businesses/cafe_aroma/versions/1/restore").json()["payment_fields"] == saved["payment_fields"]


def test_only_active_methods_need_their_data_to_publish(api):
    _create(api)
    response = _save(api, "cafe_aroma", plans_document("cafe_aroma"), values={LINK_REF: LINK, NUMBER_REF: NUMBER})
    assert response.status_code == 200
    stored = response.json()
    assert stored["payment_fields"][_method(stored, "bank")["account_number"]["secret_ref"]] == {"status": "missing", "masked": None}
    assert api.client.get("/api/businesses/cafe_aroma/review").json()["compiles"] is False
    assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1}).status_code == 409

    assert _edit(api, lambda document: _method({"document": document}, "bank").update(enabled=False)).status_code == 200
    assert api.client.get("/api/businesses/cafe_aroma/review").json()["compiles"] is True
    assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 2}).status_code == 200


def test_a_label_with_a_payment_value_is_rejected(api):
    _create_with_document(api)
    response = _edit(api, lambda document: _method({"document": document}, "bank").update(label=f"Cuenta {ACCOUNT}"))
    assert response.status_code == 422
    assert ACCOUNT not in response.text


# 13 y 14. Validaciones y errores.


@pytest.mark.parametrize(
    ("change", "path"),
    [
        pytest.param(lambda d: d["identity"].pop("name"), "identity.name", id="obligatorio_que_falta"),
        pytest.param(lambda d: d["identity"].update(name="   "), "identity.name", id="obligatorio_en_blanco"),
        pytest.param(lambda d: d["offer"]["plans"][0]["prices"][0].update(monthly="mucho"), "offer.plans.0.prices.0.monthly", id="tipo_incorrecto"),
        pytest.param(lambda d: d["offer"]["plans"][0]["prices"][0].update(monthly=-5), "offer.plans.0.prices.0.monthly", id="importe_negativo"),
        pytest.param(lambda d: d["response_style"].update(length="larguisimas"), "response_style.length", id="valor_no_permitido"),
        pytest.param(lambda d: d["identity"].update(campo_inventado="x"), "identity.campo_inventado", id="campo_fuera_del_contrato"),
        pytest.param(lambda d: d.update(offer="no es un objeto"), "offer", id="estructura_invalida"),
        pytest.param(lambda d: d["offer"].update(plans=[]), "offer", id="oferta_vacia"),
        pytest.param(lambda d: d["offer"]["plans"].append(dict(d["offer"]["plans"][0])), "offer", id="ids_de_plan_duplicados"),
        pytest.param(lambda d: d["offer"]["plans"][0].update(payment_profile="no_existe"), "", id="relacion_con_perfil_inexistente"),
        pytest.param(lambda d: d["knowledge"].update(faqs=[{"question": "A", "answer": "1"}, {"question": "A", "answer": "2"}]), "knowledge", id="faq_duplicada"),
        pytest.param(lambda d: d["response_style"].update(length="short", max_words=500), "response_style", id="limite_incoherente"),
        pytest.param(lambda d: d["capabilities"]["closing_methods"].update(payment_link=False, data_collection=False), "capabilities.closing_methods", id="sin_metodo_de_cierre"),
        pytest.param(lambda d: d["messages"]["welcome"].update(enabled=True, text=" "), "messages.welcome", id="bienvenida_sin_texto"),
    ],
)
def test_invalid_documents_are_rejected_with_their_field(api, change, path):
    _create_with_document(api)
    before = _load(api)
    response = _edit(api, change)
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "invalid"
    assert path in [issue["path"] for issue in body["issues"]]
    assert all(issue["message"] for issue in body["issues"])
    assert _load(api) == before


def test_catalog_item_with_an_unknown_category_is_rejected(api):
    _create(api, "tienda")
    document = catalog_document("tienda")
    document["offer"]["catalog"]["items"][0]["category"] = "inexistente"
    response = _save(api, "tienda", document)
    assert response.status_code == 422
    assert "categorías inexistentes" in response.json()["issues"][0]["message"]


def test_inventory_of_an_unknown_product_is_rejected(api):
    _create(api, "tienda")
    document = catalog_document("tienda")
    document["inventory"] = {"items": [{"product_id": "fantasma", "variants": []}]}
    assert _save(api, "tienda", document).status_code == 422


def test_error_messages_are_in_spanish_and_do_not_repeat_the_value(api):
    _create_with_document(api)
    response = _edit(api, lambda d: d["identity"].update(name=["MARCA_VALOR_RECIBIDO"], brand_name=" "))
    assert response.status_code == 422
    assert "MARCA_VALOR_RECIBIDO" not in response.text
    messages = {issue["path"]: issue["message"] for issue in response.json()["issues"]}
    assert messages["identity.name"] == "El valor no tiene el tipo esperado."
    assert messages["identity.brand_name"] == "No puede estar vacío."


def test_a_malformed_request_does_not_repeat_what_it_received(api):
    _create(api)
    response = api.client.put("/api/businesses/cafe_aroma/config", json={"document": plans_document("cafe_aroma"), "payment_values": {LINK_REF: ["MARCA_VALOR_DE_PAGO"]}})
    assert response.status_code == 422
    assert "MARCA_VALOR_DE_PAGO" not in response.text
    assert "input" not in response.text


def test_unexpected_errors_do_not_expose_details(api, monkeypatch):
    def _boom(_slug):
        raise RuntimeError("MARCA_DETALLE_INTERNO")

    _create(api)
    monkeypatch.setattr(api.app.state.service, "history", _boom)
    response = api.client.get("/api/businesses/cafe_aroma/versions")
    assert response.status_code == 500
    assert "MARCA_DETALLE_INTERNO" not in response.text


# 15. Aislamiento entre negocios.


def test_an_operation_on_a_business_does_not_change_another(api):
    _create_with_document(api, "negocio_a")
    _create_with_document(api, "negocio_b")
    other_before = _load(api, "negocio_b")

    assert _edit(api, lambda document: document["identity"].update(name="Solo A"), "negocio_a").status_code == 200

    assert _load(api, "negocio_b") == other_before


def test_a_document_of_another_business_is_rejected(api):
    _create_with_document(api, "negocio_a")
    _create_with_document(api, "negocio_b")
    other_before = _load(api, "negocio_b")
    response = _save(api, "negocio_a", plans_document("negocio_b"), base=_load(api, "negocio_a")["latest_version"])
    assert response.status_code == 422
    assert response.json()["issues"][0]["path"] == "tenant_slug"
    assert _load(api, "negocio_b") == other_before


def test_a_business_cannot_reach_the_payment_data_of_another(api):
    _create_with_document(api, "negocio_a")
    foreign_ref = _load(api, "negocio_a")["document"]["payments"][0]["link"]["secret_ref"]
    _create(api, "negocio_b")
    document = plans_document("negocio_b")
    document["payments"][0]["link"] = {"secret_ref": foreign_ref}
    values = {NUMBER_REF: NUMBER, ACCOUNT_REF: ACCOUNT}
    response = _save(api, "negocio_b", document, values=values)
    assert response.status_code == 200
    version = response.json()["version"]["version"]

    review = api.client.get("/api/businesses/negocio_b/review").json()
    assert review["compiles"] is False
    assert LINK not in json.dumps(review)
    # Tampoco ve la versión enmascarada: para este negocio, ese dato no existe.
    assert response.json()["payment_fields"][foreign_ref] == {"status": "missing", "masked": None}
    assert api.client.post("/api/businesses/negocio_b/publish", json={"version": version}).status_code == 409


def test_a_version_of_another_business_cannot_be_published_or_restored(api):
    _create_with_document(api, "negocio_a")
    _create_with_document(api, "negocio_b")
    assert _edit(api, lambda document: document["identity"].update(name="Segunda versión de B"), "negocio_b").status_code == 200
    other_before = (_load(api, "negocio_b"), api.client.get("/api/businesses/negocio_b/versions").json())

    # La versión 2 solo existe en el otro negocio.
    assert api.client.post("/api/businesses/negocio_a/publish", json={"version": 2}).status_code == 409
    assert api.client.post("/api/businesses/negocio_a/versions/2/restore").status_code == 409

    assert [item["version"] for item in api.client.get("/api/businesses/negocio_a/versions").json()] == [1]
    assert (_load(api, "negocio_b"), api.client.get("/api/businesses/negocio_b/versions").json()) == other_before


def test_publishing_rolling_back_and_restoring_only_affect_their_business(api):
    for slug in ("negocio_a", "negocio_b"):
        _create_with_document(api, slug)
        assert api.client.post(f"/api/businesses/{slug}/publish", json={"version": 1}).status_code == 200
        assert _edit(api, lambda document: document["identity"].update(name="Versión dos"), slug).status_code == 200
        assert api.client.post(f"/api/businesses/{slug}/publish", json={"version": 2}).status_code == 200
    other_before = (_load(api, "negocio_b"), api.client.get("/api/businesses/negocio_b/versions").json())

    assert api.client.post("/api/businesses/negocio_a/rollback").json()["published_version"] == 1
    assert api.client.post("/api/businesses/negocio_a/versions/2/restore").json()["draft_version"] == 3
    assert api.client.post("/api/businesses/negocio_a/publish", json={"version": 3}).json()["published_version"] == 3

    assert (_load(api, "negocio_b"), api.client.get("/api/businesses/negocio_b/versions").json()) == other_before


def test_operations_on_a_business_do_not_read_the_others(api, monkeypatch):
    _create_with_document(api, "negocio_a")
    _create_with_document(api, "negocio_b")

    def _reached():
        raise AssertionError("una operación de un negocio leyó todos los negocios")

    monkeypatch.setattr(api.app.state.service._storage, "list_businesses", _reached)
    base = "/api/businesses/negocio_a"
    document = _load(api, "negocio_a")["document"]
    assert _edit(api, lambda stored: stored["identity"].update(name="Otro"), "negocio_a").status_code == 200
    assert api.client.post(f"{base}/validate", json={"document": document}).status_code == 200
    assert api.client.get(f"{base}/review").status_code == 200
    assert api.client.get(f"{base}/versions").status_code == 200
    assert api.client.post(f"{base}/publish", json={"version": 1}).status_code == 200
    assert api.client.post(f"{base}/publish", json={"version": 2}).status_code == 200
    assert api.client.post(f"{base}/rollback").status_code == 200
    assert api.client.post(f"{base}/versions/2/restore").status_code == 200
    assert api.client.delete(base, params={"confirm": "negocio_a"}).status_code == 204


def test_deleting_a_business_requires_confirmation_and_only_removes_that_one(api):
    _create_with_document(api, "negocio_a")
    _create_with_document(api, "negocio_b")

    assert api.client.delete("/api/businesses/negocio_a").status_code == 400
    assert api.client.delete("/api/businesses/negocio_a", params={"confirm": "negocio_b"}).status_code == 400
    assert len(api.client.get("/api/businesses").json()) == 2

    assert api.client.delete("/api/businesses/negocio_a", params={"confirm": "negocio_a"}).status_code == 204

    assert [item["slug"] for item in api.client.get("/api/businesses").json()] == ["negocio_b"]
    assert api.client.get("/api/businesses/negocio_a/config").status_code == 404
    assert _load(api, "negocio_b")["version"]["version"] == 1
    with api.engine.connect() as conn:
        assert len(conn.execute(select(business_configs.c.tenant_id)).all()) == 1
        assert len(conn.execute(select(business_config_secrets.c.ref_key)).all()) == 3


# 16. Los datos sensibles no se devuelven en claro.


def test_payment_data_is_never_returned_and_is_encrypted_on_disk(api):
    saved = _create_with_document(api)
    responses = [
        saved,
        _load(api),
        api.client.get("/api/businesses").json(),
        api.client.get("/api/businesses/cafe_aroma/versions").json(),
        api.client.get("/api/businesses/cafe_aroma/review").json(),
        api.client.post("/api/businesses/cafe_aroma/validate", json={"document": _load(api)["document"]}).json(),
        api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1}).json(),
    ]
    text = json.dumps(responses, ensure_ascii=False)
    for value in ALL_VALUES.values():
        assert value not in text
    assert "secret_store:principal.link~" in text

    api.engine.dispose()
    raw = api.path.read_bytes()
    for value in ALL_VALUES.values():
        assert value.encode() not in raw
    assert api.key.encode() not in raw


def test_a_payment_value_written_in_the_open_is_rejected(api):
    _create_with_document(api)
    response = _edit(api, lambda document: document["identity"].update(description=f"Consigna a la cuenta {ACCOUNT}"))
    assert response.status_code == 422
    assert "dato de pago" in response.json()["message"]
    assert ACCOUNT not in response.text


@pytest.mark.parametrize(
    ("ref", "value", "path"),
    [
        pytest.param(LINK_REF, "no-es-un-enlace", "payments.0.link", id="enlace"),
        pytest.param(NUMBER_REF, "12345", "payments.0.transfer_methods.0.number", id="celular"),
        pytest.param(ACCOUNT_REF, "cuenta con letras", "payments.0.transfer_methods.1.account_number", id="cuenta"),
    ],
)
def test_the_server_rejects_payment_values_with_a_wrong_format(api, ref, value, path):
    _create(api)
    response = _save(api, "cafe_aroma", plans_document("cafe_aroma"), values={**ALL_VALUES, ref: value})
    assert response.status_code == 422
    assert [issue["path"] for issue in response.json()["issues"]] == [path]
    assert response.json()["message"] == response.json()["issues"][0]["message"]
    assert value not in response.text
    assert _load(api)["version"] is None
    with api.engine.connect() as conn:
        assert conn.execute(select(business_config_secrets.c.ref_key)).all() == []


def test_technical_configuration_is_not_part_of_the_api(api):
    _create_with_document(api)
    api.service.save_engine_settings("cafe_aroma", {"schema_version": "1.0", "tenant_slug": "cafe_aroma"})
    stored = _load(api)
    assert set(stored["document"]) <= set(BusinessConfig.model_fields)
    assert "engine" not in json.dumps(sorted(stored["document"]))
    # Un campo técnico no se puede colar por el panel: el contrato no lo admite.
    assert _edit(api, lambda document: document.update(engine={"max_tokens": 10})).status_code == 422


def test_a_wrong_encryption_key_does_not_expose_or_alter_anything(api):
    _create_with_document(api)
    wrong = TestClient(create_app(build_business_config_service(api.engine, secrets_key=Fernet.generate_key().decode())), base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False)
    opened = wrong.get("/api/businesses/cafe_aroma/config")
    assert opened.status_code == 200
    assert [field["status"] for field in opened.json()["payment_fields"].values()] == ["unreadable"] * 3
    assert [field["masked"] for field in opened.json()["payment_fields"].values()] == [None] * 3
    stored = _load(api)
    response = wrong.put("/api/businesses/cafe_aroma/config", json={"document": stored["document"], "payment_values": {}, "base_version": stored["latest_version"]})
    assert response.status_code == 503
    assert response.json()["code"] == "payment_key"
    assert _load(api)["version"]["version"] == 1


# Solo este equipo.


def test_requests_from_other_computers_are_rejected(api):
    outsider = TestClient(api.app, base_url=BASE_URL, client=("192.168.1.50", 50000))
    assert outsider.get("/api/businesses").status_code == 403


@pytest.mark.parametrize("host", ["sitio-malicioso.example", "192.168.1.50:8010", "127.0.0.1.sitio-malicioso.example"])
def test_requests_with_another_host_are_rejected(api, host):
    # Protege frente a un sitio web que resuelve su dominio a 127.0.0.1 (DNS rebinding).
    assert api.client.get("/api/businesses", headers={"Host": host}).status_code == 403


def test_requests_from_other_websites_are_rejected(api):
    response = api.client.post("/api/businesses", headers={"Origin": "https://sitio-malicioso.example"}, json={"slug": "intruso", "name": "Intruso"})
    assert response.status_code == 403
    assert api.client.get("/api/businesses").json() == []


@pytest.mark.parametrize("origin", sorted(PANEL_ORIGINS))
def test_the_panel_is_accepted(api, origin):
    assert api.client.post("/api/businesses", headers={"Origin": origin}, json={"slug": "permitido", "name": "Permitido"}).status_code == 201


def test_no_other_website_is_allowed_to_read_the_responses(api):
    panel = f"http://localhost:{ADMIN_WEB_PORT}"
    response = api.client.get("/api/businesses", headers={"Origin": panel})
    assert "access-control-allow-origin" not in response.headers
    assert api.client.options("/api/businesses", headers={"Origin": panel, "Access-Control-Request-Method": "POST"}).status_code == 405
    assert response.headers["cache-control"] == "no-store"


def test_the_api_only_has_the_routes_of_the_panel(api):
    routes = {(method, route.path.removeprefix("/api")) for route in api.app.routes if isinstance(route, APIRoute) for method in route.methods}
    business = "/businesses/{slug}"
    assert routes == {
        ("GET", "/health"),
        ("GET", "/contract"),
        ("GET", "/businesses"),
        ("POST", "/businesses"),
        ("GET", "/business-templates"),
        # WhatsApp por código QR (`channel_routes.py`).
        ("GET", f"{business}/channels/whatsapp"),
        ("POST", f"{business}/channels/whatsapp/connect"),
        ("POST", f"{business}/channels/whatsapp/new-code"),
        ("GET", f"{business}/channels/whatsapp/status"),
        ("POST", f"{business}/channels/whatsapp/disconnect"),
        ("POST", "/businesses/import"),
        ("DELETE", business),
        ("GET", f"{business}/config"),
        ("PUT", f"{business}/config"),
        ("POST", f"{business}/validate"),
        ("GET", f"{business}/review"),
        ("GET", f"{business}/versions"),
        ("POST", f"{business}/versions/{{version}}/restore"),
        ("POST", f"{business}/publish"),
        ("POST", f"{business}/rollback"),
        # Inteligencia artificial y área de pruebas (`assistant_routes.py`).
        ("GET", f"{business}/ai"),
        ("PUT", f"{business}/ai"),
        ("GET", f"{business}/ai/usage"),
        ("GET", f"{business}/ai/models"),
        ("POST", f"{business}/ai/verify"),
        ("POST", f"{business}/playground"),
        ("DELETE", f"{business}/playground/{{session_id}}"),
        # Bandeja de conversaciones (`conversation_routes.py`).
        ("GET", "/conversations"),
        ("GET", "/conversations/{conversation_id}"),
        ("GET", "/conversations/{conversation_id}/live"),
        ("POST", "/conversations/{conversation_id}/messages"),
        ("POST", "/conversations/{conversation_id}/assistant"),
        ("POST", "/conversations/{conversation_id}/read"),
        ("GET", "/conversations/{conversation_id}/media/{media_id}"),
        ("GET", f"{business}/activity"),
        ("POST", "/conversations/{conversation_id}/handoff/resolve"),
        ("GET", "/notifications"),
        ("POST", "/notifications/read"),
    }
    assert api.client.post("/api/v1/simulate", json={}).status_code == 404


def test_the_routes_are_not_advertised(api):
    assert api.client.get("/docs").status_code == 404
    assert api.client.get("/openapi.json").status_code == 404


# 18. El panel usa de verdad BusinessConfig v1, y la Fase 1 sigue intacta.


def test_the_form_schema_is_the_published_contract(api):
    assert api.client.get("/api/contract").json() == json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_the_document_of_the_panel_is_validated_by_the_contract(api):
    _create(api)
    assert _save(api, "cafe_aroma", plans_document("cafe_aroma", with_payments=False)).status_code == 200
    BusinessConfig.model_validate(_load(api)["document"])


def test_validating_does_not_save(api):
    _create_with_document(api)
    document = _load(api)["document"]
    document["capabilities"]["service_channels"] = []
    response = api.client.post("/api/businesses/cafe_aroma/validate", json={"document": document})
    assert response.status_code == 200
    assert "sin_canales_de_atencion" in [item["code"] for item in response.json()["diagnostics"]]
    assert _load(api)["version"]["version"] == 1


def test_publish_rollback_and_restore(api):
    _create_with_document(api)
    assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1}).status_code == 200
    assert _load(api)["published_version"] == 1

    assert _edit(api, lambda document: document["identity"].update(name="Versión dos")).status_code == 200
    published = api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 2}).json()
    assert published["published_version"] == 2
    assert published["document"]["identity"]["name"] == "Versión dos"

    rolled = api.client.post("/api/businesses/cafe_aroma/rollback").json()
    assert rolled["published_version"] == 1
    assert rolled["document"]["identity"]["name"] == "Negocio ficticio"

    restored = api.client.post("/api/businesses/cafe_aroma/versions/2/restore").json()
    assert restored["document"]["identity"]["name"] == "Versión dos"
    assert restored["version"]["status"] == "draft"
    assert restored["published_version"] == 1

    assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 99}).status_code == 409
    assert api.client.post("/api/businesses/cafe_aroma/versions/99/restore").status_code == 409


def test_a_version_without_its_payment_data_cannot_be_published(api):
    _create(api)
    response = _save(api, "cafe_aroma", plans_document("cafe_aroma"), values={LINK_REF: LINK, NUMBER_REF: NUMBER})
    assert response.status_code == 200
    review = api.client.get("/api/businesses/cafe_aroma/review").json()
    assert review["compiles"] is False
    rejected = api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1})
    assert rejected.status_code == 409
    assert _load(api)["published_version"] is None
    # Lo explica sin referencias internas, que no le sirven a quien administra el negocio.
    for message in (review["compile_error"], rejected.json()["message"]):
        assert "Falta un dato de pago" in message
        assert "secret_store" not in message and "principal." not in message


def test_a_version_that_does_not_compile_is_explained_and_not_published(api):
    _create_with_document(api)
    api.service.save_engine_settings("cafe_aroma", {"schema_version": "1.0", "tenant_slug": "cafe_aroma", "legacy": {"business": {"name": "Otro nombre"}}})

    review = api.client.get("/api/businesses/cafe_aroma/review").json()
    assert review["compiles"] is False
    assert "conflicto" in review["compile_error"]

    rejected = api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1})
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "conflict"
    assert "onflicto" in rejected.json()["message"]
    assert _load(api)["published_version"] is None


def test_a_damaged_version_cannot_be_published_or_restored(api):
    _create_with_document(api)
    with api.engine.begin() as conn:
        conn.execute(business_configs.update().values(document={"tenant_slug": "cafe_aroma"}))

    assert api.client.post("/api/businesses/cafe_aroma/publish", json={"version": 1}).status_code == 409
    assert api.client.post("/api/businesses/cafe_aroma/versions/1/restore").status_code == 409
    assert len(api.client.get("/api/businesses/cafe_aroma/versions").json()) == 1
    # El listado sigue funcionando y leerla no la da por buena.
    assert api.client.get("/api/businesses").json()[0]["published_version"] is None
    assert api.client.get("/api/businesses/cafe_aroma/config").status_code == 422


def test_a_business_is_only_saved_when_its_document_is_complete(api):
    _create(api)
    empty = plans_document("cafe_aroma")
    empty["offer"]["plans"] = []
    assert _save(api, "cafe_aroma", empty).status_code == 422
    assert _load(api)["version"] is None


@pytest.fixture
def imported(api):
    response = api.client.post("/api/businesses/import")
    assert response.status_code == 200
    return api, response.json()


def test_the_nine_businesses_can_be_imported_once(imported):
    api, report = imported
    assert len(report["created"]) == 9
    assert report["skipped"] == []
    assert len(api.client.get("/api/businesses").json()) == 9

    again = api.client.post("/api/businesses/import").json()
    assert again["created"] == []
    assert sorted(again["skipped"]) == sorted(report["created"])


def test_saving_an_imported_business_without_changes_loses_nothing(imported):
    # Es la garantía central del panel: lo que no edita no se pierde, aunque no tenga pantalla propia.
    api, report = imported
    for slug in report["created"]:
        stored = _load(api, slug)
        compiled_before = api.service.compile_sections(slug)
        response = _save(api, slug, copy.deepcopy(stored["document"]), base=stored["latest_version"])
        assert response.status_code == 200, slug
        saved = response.json()
        assert saved["document"] == stored["document"], slug
        assert saved["version"]["version"] == stored["latest_version"] + 1, slug
        assert api.client.post(f"/api/businesses/{slug}/publish", json={"version": saved["version"]["version"]}).status_code == 200, slug
        assert api.service.compile_sections(slug) == compiled_before, slug


def test_imported_businesses_do_not_return_their_payment_data(imported):
    api, report = imported
    for slug in report["created"]:
        values = payment_values(api.service.compile_sections(slug))
        text = _load(api, slug)
        assert sum(1 for value in values if value in json.dumps(text, ensure_ascii=False)) == 0, slug


def test_the_api_does_not_load_the_engine_nor_read_the_env_file_or_the_yaml(tmp_path):
    script = """
import json, os, sys
opened = []
def audit(event, args):
    if event == "open" and isinstance(args[0], (str, os.PathLike)):
        name = os.path.basename(os.fspath(args[0]))
        if name.startswith(".env") or name.endswith((".yaml", ".yml")):
            opened.append(name)
sys.addaudithook(audit)
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from app.admin_api.main import create_app
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
engine = create_business_config_engine(sys.argv[1])
create_local_schema(engine)
client = TestClient(create_app(build_business_config_service(engine, secrets_key=Fernet.generate_key().decode())), base_url="http://127.0.0.1:8010", client=("127.0.0.1", 50000))
assert client.post("/api/businesses", json={"slug": "negocio", "name": "Negocio"}).status_code == 201
assert client.get("/api/businesses/negocio/config").status_code == 200
forbidden = ("yaml", "app.api", "app.application", "app.config", "app.connectors", "app.database", "app.main", "app.services", "app.models", "app.infrastructure.config", "app.infrastructure.ai", "app.infrastructure.persistence")
print(json.dumps({"opened": opened, "loaded": sorted(name for name in sys.modules if name in forbidden or name.startswith(tuple(item + "." for item in forbidden)))}))
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "project")}
    env.pop("PYTEST_CURRENT_TEST", None)
    result = subprocess.run(
        [sys.executable, "-c", script, f"sqlite:///{(tmp_path / 'x.sqlite3').as_posix()}"],
        env=env, cwd=tmp_path, capture_output=True, encoding="utf-8", timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    output = json.loads(result.stdout.strip().splitlines()[-1])
    assert output == {"opened": [], "loaded": []}
