"""Seguridad del motor: ningún registro con tokens o datos de clientes, y el webhook de WhatsApp solo acepta lo que firmó Meta."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.controllers import whatsapp_webhook
from app.config import settings

APP_DIR = Path(__file__).resolve().parents[1] / "project" / "app"
SECRET = "secreto-de-la-app-de-meta"
# Sin `phone_number_id`: pasa la firma y el motor la ignora sin tocar ninguna base.
BODY = json.dumps({"object": "whatsapp_business_account", "entry": []}).encode()


def test_the_engine_never_prints():
    """Un `print` termina en los registros de la nube: ahí no puede ir un token ni el mensaje de un cliente."""
    offenders = [
        f"{path.relative_to(APP_DIR)}:{number}"
        for path in APP_DIR.rglob("*.py")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if re.search(r"(?<![\w.])print\(", line)
    ]
    assert offenders == []


@pytest.fixture
def webhook(monkeypatch):
    monkeypatch.setattr(settings, "meta_app_secret", SECRET, raising=False)
    monkeypatch.setattr(settings, "enable_webhook_processing", True, raising=False)
    app = FastAPI()
    app.include_router(whatsapp_webhook.router)
    return TestClient(app)


def _signature(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_the_whatsapp_webhook_only_accepts_what_meta_signed(webhook):
    url = "/whatsapp/webhook"
    assert webhook.post(url, content=BODY).status_code == 403
    assert webhook.post(url, content=BODY, headers={"X-Hub-Signature-256": _signature(BODY, "otro-secreto")}).status_code == 403
    assert webhook.post(url, content=BODY + b" ", headers={"X-Hub-Signature-256": _signature(BODY)}).status_code == 403
    accepted = webhook.post(url, content=BODY, headers={"X-Hub-Signature-256": _signature(BODY)})
    assert accepted.status_code == 200 and accepted.json() == {"status": "ignored"}


def test_without_the_app_secret_nothing_is_accepted(webhook, monkeypatch):
    monkeypatch.setattr(settings, "meta_app_secret", "", raising=False)
    response = webhook.post("/whatsapp/webhook", content=BODY, headers={"X-Hub-Signature-256": _signature(BODY, "")})
    assert response.status_code == 403
