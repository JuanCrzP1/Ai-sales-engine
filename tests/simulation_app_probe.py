"""Arranca la aplicación real en un proceso aparte y resume cómo responde `/simulate` con la configuración recibida.

`test_simulation_endpoint_security.py` lo ejecuta una vez por configuración, porque los ajustes se resuelven al importar
`app`. No lee ningún `.env`, no sale a la red y simula el modelo. Solo escribe estados HTTP y nombres de campos.

Primero mide sin simular nada. Después sustituye únicamente la verificación del token, que depende de la autenticación
aplazada a la fase de nube, para comprobar la respuesta de un administrador identificado.
"""
import json
import pathlib
import socket
import sys

_exists = pathlib.Path.exists
pathlib.Path.exists = lambda self, *args, **kwargs: self.name != ".env" and _exists(self, *args, **kwargs)
_connect = socket.socket.connect


def _loopback_only(self, address):
    # El bucle de eventos de Windows usa un socket local; cualquier otro destino queda bloqueado.
    if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
        return _connect(self, address)
    raise OSError("red bloqueada")


socket.socket.connect = _loopback_only
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "project"))

from fastapi.testclient import TestClient  # noqa: E402
from pipeline_harness import reply  # noqa: E402

from app.application.ai_pipeline import AIPipeline  # noqa: E402
from app.config import settings  # noqa: E402
from app.database.connection import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import AdminUser, Tenant  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402

_pipeline_init = AIPipeline.__init__
model_calls = []


def _fake_model(self, *args, **kwargs):
    _pipeline_init(self, *args, **kwargs)

    def _generate(prompt, *, user_message, bot_config=None):
        model_calls.append(1)
        return reply("Respuesta simulada.")

    self.runtime.generate = _generate


AIPipeline.__init__ = _fake_model

init_db()
with SessionLocal() as db:
    business = Tenant(name="Negocio ficticio", slug="saas")
    db.add(business)
    db.commit()
    admin = AdminUser(tenant_id=business.id, email="admin@negocio-ficticio.com", full_name="Admin ficticio", password_hash="no-usada")
    db.add(admin)
    db.commit()
    admin_id = admin.id

client = TestClient(app, raise_server_exceptions=False)
url = f"{settings.api_prefix}/simulate"
message = {"user_message": "tengo muchos mensajes"}
tenant = {"X-Tenant-Slug": "saas"}

registered = client.post(
    f"{settings.api_prefix}/auth/register",
    json={
        "tenant_name": "Otro negocio ficticio",
        "tenant_slug": "negocio-nuevo",
        "full_name": "Otro admin ficticio",
        "email": "otro@negocio-ficticio.com",
        "password": "clave-ficticia-123",
    },
)
result = {
    "flag": settings.enable_simulation_endpoint,
    "anonymous": client.post(url, headers=tenant, json=message).status_code,
    "bad_token": client.post(url, headers={**tenant, "Authorization": "Bearer basura"}, json=message).status_code,
    "malformed": client.post(url, headers={**tenant, "Content-Type": "application/json"}, content=b"{mal").status_code,
    "get": client.get(url).status_code,
    "in_openapi": url in app.openapi()["paths"],
    "register": registered.status_code,
    "register_issued_token": registered.status_code == 200 and "access_token" in registered.json(),
    "model_calls_without_identity": len(model_calls),
}

AuthService.get_user_from_token = lambda self, token: self.db.get(AdminUser, admin_id) if token == "token-de-prueba" else None
response = client.post(url, headers={**tenant, "Authorization": "Bearer token-de-prueba"}, json=message)
result["authenticated"] = response.status_code
if response.status_code == 200:
    body = response.json()
    result.update(fields=sorted(body), metadata_fields=sorted(body["metadata"]), reply=body["reply"])

pathlib.Path(sys.argv[1]).write_text(json.dumps(result), encoding="utf-8")
