"""El contrato del WhatsApp simulado: se usa con el cliente REAL de uazapi del motor y sus lectores REALES de avisos.

Si el simulador se aleja de cómo habla uazapi, o el motor cambia lo que espera, esta prueba falla: así los recorridos con el simulador
prueban de verdad lo que pasará con uazapi. Cuando uazapi cambie algo, se ajustan juntos los lectores del motor y el simulador.
"""
from __future__ import annotations

import base64
import json

import httpx
import pytest

from app.domain.business_config.channels import ChannelError, WhatsAppUnavailableError
from app.domain.business_config.conversations import MediaFile
from app.infrastructure.channels import platform
from app.infrastructure.channels.uazapi import UazapiClient, connection_event, parse_incoming, parse_own_message, parse_receipt
from wa_sim_harness import Phone, ServerThread, free_port, wait_for
from wa_sim.config import ProductionRefused, SimConfig, load_config
from wa_sim.server import create_simulator

CUSTOMER = "573001112233"
PNG = base64.b64encode(b"\x89PNG\r\n\x1a\nfoto-del-comprobante").decode()


@pytest.fixture
def simulated(monkeypatch):
    received: list[dict] = []
    capture = httpx.MockTransport(lambda request: received.append(json.loads(request.content)) or httpx.Response(200, json={"status": "ok"}))
    simulator = create_simulator(SimConfig(receipt_seconds=0.05), persist=False, webhook_transport=capture)
    server = ServerThread(simulator.app, free_port()).start()
    monkeypatch.setenv(platform.SIMULATOR_URL_ENV, server.url)
    monkeypatch.delenv("VERCEL", raising=False)
    phone = Phone(server.url)
    yield UazapiClient(server.url), phone, received
    phone.close()
    server.stop()


def _events(received: list[dict], kind: str) -> list[dict]:
    return [payload for payload in received if payload.get("EventType") == kind]


def _connected(client: UazapiClient, phone: Phone) -> str:
    token = client.create_instance("simulador", "ventas-prueba")
    client.set_webhook(token, "http://motor.local/api/v1/channels/whatsapp/abc")
    client.connect(token)
    phone.scan(token)
    phone.add_client(CUSTOMER, "Ana")
    return token


def test_a_number_is_created_linked_by_qr_and_reported_like_uazapi(simulated):
    client, phone, received = simulated
    token = client.create_instance("simulador", "ventas-prueba")
    client.set_webhook(token, "http://motor.local/api/v1/channels/whatsapp/abc")
    waiting = client.connect(token)
    assert waiting.status == "connecting" and waiting.qrcode.startswith("data:image/png;base64,") and waiting.paircode
    phone.scan(token, "573110000000")
    connected = client.status(token)
    assert (connected.status, connected.phone, connected.qrcode) == ("connected", "573110000000", None)
    # El aviso de conexión lo entiende el lector real del motor.
    last = connection_event(_events(received, "connection")[-1])
    assert (last.status, last.phone, last.profile_name) == ("connected", "573110000000", "Negocio de prueba")


def test_the_admin_token_and_the_instance_token_behave_like_uazapi(simulated):
    client, _phone, _received = simulated
    with pytest.raises(WhatsAppUnavailableError):
        client.create_instance("otro-token", "x")
    with pytest.raises(ChannelError) as gone:
        client.status("token-que-no-existe")
    assert gone.value.gone
    token = client.create_instance("simulador", "ventas-prueba")
    client.delete_instance(token)
    with pytest.raises(ChannelError) as deleted:
        client.status(token)
    assert deleted.value.gone


def test_customer_messages_files_and_own_messages_are_read_by_the_real_parsers(simulated):
    client, phone, received = simulated
    token = _connected(client, phone)
    phone.write(token, CUSTOMER, "Hola, ¿qué venden?")
    text = parse_incoming(_events(received, "messages")[-1])
    assert (text.phone, text.contact_name, text.text, text.kind) == (CUSTOMER, "Ana", "Hola, ¿qué venden?", "text")

    phone.write(token, CUSTOMER, "Este es el comprobante", kind="image", file_base64=PNG, mime_type="image/png", file_name="pago.png")
    photo = parse_incoming(_events(received, "messages")[-1])
    assert (photo.kind, photo.text, photo.mime_type) == ("image", "Este es el comprobante", "image/png")
    assert client.download(token, photo.message_id) == MediaFile("image/png", base64.b64decode(PNG))

    phone.write(token, CUSTOMER, "nota de voz", kind="audio", file_base64=PNG, mime_type="audio/ogg", file_name="nota.ogg")
    assert parse_incoming(_events(received, "messages")[-1]).kind == "audio"

    phone.write(token, CUSTOMER, "Hola Ana, soy Laura del negocio", from_business_phone=True)
    own = _events(received, "messages")[-1]
    assert parse_incoming(own) is None
    assert parse_own_message(own).text == "Hola Ana, soy Laura del negocio"


def test_what_the_business_sends_arrives_with_sent_delivered_and_read_receipts(simulated):
    client, phone, received = simulated
    token = _connected(client, phone)
    client.presence(token, CUSTOMER, "composing", 5_000)
    assert f"{token}:{CUSTOMER}" in phone.state()["typing"]

    message_id = client.send_text(token, CUSTOMER, "¡Hola Ana! 👋")
    first = phone.from_business(token, CUSTOMER)[0]
    assert (first["id"], first["text"], first["status"]) == (message_id, "¡Hola Ana! 👋", "sent")
    delivered = wait_for(lambda: [parse_receipt(p) for p in _events(received, "messages_update")], what="el ✓✓")[0]
    assert (delivered.message_ids, delivered.status) == ((message_id,), "delivered")

    phone.open(token, CUSTOMER)
    read = parse_receipt(_events(received, "messages_update")[-1])
    assert (read.message_ids, read.status) == ((message_id,), "read")

    document = client.send_media(token, CUSTOMER, "document", MediaFile("application/pdf", b"%PDF-1.4", "lista.pdf"), "La lista de precios")
    sent = phone.from_business(token, CUSTOMER)[-1]
    assert (sent["id"], sent["kind"], sent["text"], sent["media"]["file_name"], sent["media"]["mime_type"]) == (document, "document", "La lista de precios", "lista.pdf", "application/pdf")


def test_the_simulator_never_runs_in_production_and_the_platform_only_trusts_it_locally(monkeypatch):
    with pytest.raises(ProductionRefused):
        load_config({"VERCEL": "1"})
    with pytest.raises(ProductionRefused):
        load_config({"ENV": "production"})
    monkeypatch.setenv(platform.SIMULATOR_URL_ENV, "http://127.0.0.1:3300")
    monkeypatch.delenv("VERCEL", raising=False)
    assert platform.simulator_url() == "http://127.0.0.1:3300" and platform.uazapi_platform().server_url == "http://127.0.0.1:3300"
    monkeypatch.setenv("VERCEL", "1")
    assert platform.simulator_url() is None and not platform.is_simulator("http://127.0.0.1:3300")
    monkeypatch.delenv("VERCEL")
    for address in ("http://simulador.example.com:3300", "https://127.0.0.1:3300", "http://10.0.0.5:3300"):
        monkeypatch.setenv(platform.SIMULATOR_URL_ENV, address)
        assert platform.simulator_url() is None, address
