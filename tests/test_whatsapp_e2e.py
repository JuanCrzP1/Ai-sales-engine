"""Recorridos de punta a punta por WhatsApp, con el WhatsApp simulado (`apps/wa-sim`).

Corren de verdad el panel (sus rutas), el motor (su webhook y todo el flujo de cada mensaje), el simulador (un uazapi falso por HTTP)
y el teléfono de prueba (el cliente). Solo el modelo de IA tiene respuestas fijas (`ScriptedModel`) y la IA que ve fotos dice que la
foto es un comprobante. Nada sale de este equipo.

Cada recorrido deja su parte del informe en español en `.wa-sim/informe-e2e.md`.
"""
from __future__ import annotations

import base64
import copy
import dataclasses
import os
from contextlib import contextmanager
from dataclasses import dataclass
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from app.domain.business_config.payment_data import iter_secret_refs, payment_values, redact_values
from pipeline_harness import prepared_tenant, publish_store
from test_admin_api import BASE_URL, LOCAL_CLIENT
from test_business_config_engine_integration import _payment_choices
from test_whatsapp_qr_channel import FakeMedia
from wa_sim_harness import REPO_ROOT, Phone, Report, ScriptedModel, ServerThread, free_port, start_simulator, wait_for

ANA = "573001112233"
RECEIPT_PNG = base64.b64encode(b"\x89PNG\r\n\x1a\ncomprobante-nequi").decode()
REPORT_PATH = REPO_ROOT / ".wa-sim" / "informe-e2e.md"
REPORTS: dict[str, Report] = {}
_EXAMPLE_PAYMENT_VALUES = {value for slug in ("saas", "restaurant") for value in prepared_tenant(slug).payment_values.values()}

MODEL = [
    (r"qu[eé] venden", {"response": "Tenemos planes para que tu WhatsApp venda solo. ¿Quieres saber precios?", "intent": "info", "metadata": {}}),
    (r"pagar por nequi", {"response": "¡Listo! Te envío los datos.", "intent": "buy", "metadata": {"payment_method": "nequi"}}),
    # Lo que pasó en producción el 13 nov 2026: el modelo dice que no puede reenviar el número. El sistema debe enviarlo igual.
    (r"se me borr", {"response": "Lo siento, no puedo enviarlo de nuevo.", "intent": "info", "metadata": {}}),
    (r"ya pagu", {"response": "Gracias, lo paso al equipo para verificarlo.", "intent": "buy", "metadata": {"payment_status": "reportado"}}),
    # Con la IA real, un negocio de Perú (13 nov 2026): «los datos de pago son los mismos, solo cambia el medio».
    (r"pago por nu", {"response": "Los datos de pago son los mismos, solo cambia el medio.", "intent": "info", "metadata": {}}),
    (r"por yape", {"response": "Listo.", "intent": "buy", "metadata": {"payment_method": "Yape"}}),
    (r"efectivo", {"response": "Perfecto.", "intent": "info", "metadata": {}}),
]


@dataclass
class Stack:
    panel: TestClient
    phone: Phone
    model: ScriptedModel
    alerts: list


def _peru(document: dict) -> None:
    """Un negocio de Perú: Yape, «otro medio» (Nu) y efectivo, en las mismas casillas cifradas."""
    profile = document["payments"][0]
    number = next(method["number"] for method in profile["transfer_methods"] if method.get("number"))
    reference = next(method["reference"] for method in profile["transfer_methods"] if method.get("reference"))
    profile["transfer_methods"] = [
        {"type": "yape", "number": number, "holder": "Asesor Comercial S.A.C.", "instructions": "Envía la captura con tu nombre."},
        {"type": "custom", "name": "Nu", "data_label": "Cuenta", "reference": reference},
        {"type": "cash", "instructions": "Pagas al asesor cuando te visite."},
    ]


def _publish(monkeypatch, tmp_path, slugs: list[str], mutate) -> str:
    tenants = []
    for slug in slugs:
        tenant = prepared_tenant(slug)
        document = copy.deepcopy(tenant.document)
        if mutate is not None:
            mutate(document)
        refs = {holder["secret_ref"] for holder in iter_secret_refs(document)}
        tenants.append(dataclasses.replace(tenant, document=document, payment_values={ref: value for ref, value in tenant.payment_values.items() if ref in refs}))
    return publish_store(monkeypatch, tmp_path, tenants)


@contextmanager
def running_stack(monkeypatch, tmp_path, slugs: list[str], mutate=None):
    """El simulador, el motor (servidor de verdad) y el panel, con esos negocios publicados y su clave de IA."""
    from app.api.controllers import whatsapp_qr_webhook
    from app.infrastructure.business_config.ai_settings_store import AISettingsStore
    from app.infrastructure.business_config.database import create_business_config_engine
    from app.services.ai_runtime.runtime_llm.prompting import RuntimeLLMImplementation

    _simulator, sim_server = start_simulator(receipt_seconds=0.15)
    engine_port = free_port()
    monkeypatch.setenv("WHATSAPP_SIMULATOR_URL", sim_server.url)
    monkeypatch.setenv("ENGINE_PUBLIC_URL", f"http://127.0.0.1:{engine_port}")
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("ATTENTION_SWEEP_ON_TRAFFIC", raising=False)

    store = create_business_config_engine(_publish(monkeypatch, tmp_path, slugs, mutate))
    keys = AISettingsStore(store, os.environ["BUSINESS_CONFIG_SECRETS_KEY"])
    for slug in slugs:
        keys.save_ai_settings(slug, model=None, api_key="sk-or-v1-clave-de-prueba-e2e", clear_key=False)

    model = ScriptedModel(rules=list(MODEL))
    monkeypatch.setattr(RuntimeLLMImplementation, "generate", lambda self, prompt, **kwargs: model.generate(prompt, **kwargs))
    monkeypatch.setattr(whatsapp_qr_webhook, "OpenRouterMediaInterpreter", FakeMedia)
    alerts: list = []
    monkeypatch.setattr(whatsapp_qr_webhook, "deliver_alert", alerts.append)

    from app.main import app as engine_app

    engine = ServerThread(engine_app, engine_port).start()
    phone = Phone(sim_server.url)
    try:
        yield Stack(TestClient(_panel_app(store), base_url=BASE_URL, client=LOCAL_CLIENT, raise_server_exceptions=False), phone, model, alerts)
    finally:
        phone.close()
        engine.stop()
        sim_server.stop()
        store.dispose()


def _panel_app(store):
    """El panel como lo arma `scripts/run_admin_api.py`, con WhatsApp apuntando al simulador."""
    from app.admin_api.main import create_app
    from app.config import settings
    from app.infrastructure.business_config.conversation_store import ConversationStore
    from app.infrastructure.business_config.database import build_business_config_service, build_channel_messenger, build_whatsapp_channel_service
    from app.infrastructure.channels.platform import uazapi_platform
    from app.infrastructure.channels.public_url import webhook_base
    from app.infrastructure.channels.uazapi import UazapiClient

    key = os.environ["BUSINESS_CONFIG_SECRETS_KEY"]
    return create_app(
        build_business_config_service(store, secrets_key=key),
        conversations=ConversationStore(store),
        whatsapp=build_whatsapp_channel_service(store, UazapiClient, platform=uazapi_platform(), webhook_base=webhook_base(settings.api_prefix), secrets_key=key),
        messenger=build_channel_messenger(store, UazapiClient, secrets_key=key),
    )


def _run(report: Report, steps) -> None:
    REPORTS[report.title] = report
    try:
        for name, check in steps:
            report.step(name, check)
    finally:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        text = "# Recorridos con el WhatsApp simulado\n\n" + "\n".join(item.markdown() for item in REPORTS.values())
        # El informe nunca muestra datos de pago, aunque sean de ejemplo.
        REPORT_PATH.write_text(redact_values(text, sorted(_EXAMPLE_PAYMENT_VALUES, key=len, reverse=True)), encoding="utf-8")


def _connect(stack: Stack, slug: str, business_phone: str) -> str:
    """Conecta el WhatsApp del negocio por QR, como en el panel, y devuelve el token de su número en el simulador."""
    channel = f"/api/businesses/{slug}/channels/whatsapp"
    known = {instance["token"] for instance in stack.phone.state()["instances"]}
    waiting = stack.panel.post(f"{channel}/connect").json()
    assert waiting["status"] == "connecting" and waiting["qrcode"].startswith("data:image/png;base64,"), waiting
    new = next(instance for instance in stack.phone.state()["instances"] if instance["token"] not in known)
    assert new["webhook_url"], "el panel no registró el aviso del número"
    stack.phone.scan(new["token"], business_phone)
    wait_for(lambda: stack.panel.get(f"{channel}/status").json()["status"] == "connected", what=f"el panel ve conectado a {slug}")
    return new["token"]


def _conversation(stack: Stack, slug: str) -> dict:
    found = [item for item in stack.panel.get("/api/conversations").json() if item["channel"] == "whatsapp" and item["business"]["slug"] == slug]
    assert found, f"la conversación de {slug} no aparece en el panel"
    return stack.panel.get(f"/api/conversations/{found[0]['id']}").json()


def _runtime(slug: str) -> dict:
    from app.application.runtime import load_tenant_runtime_yaml

    return load_tenant_runtime_yaml(slug)


# ---------------------------------------------------------------------------------------------------------- recorridos


def test_a_business_day_on_whatsapp(monkeypatch, tmp_path):
    with running_stack(monkeypatch, tmp_path, ["saas"]) as stack:
        phone, panel = stack.phone, stack.panel
        nequi = dict(_payment_choices(_runtime("saas")))["nequi"][0]
        state: dict = {}

        def connect() -> str:
            state["token"] = _connect(stack, "saas", "573110000000")
            return "el panel pidió el QR, el teléfono lo escaneó y el panel lo muestra conectado al +573110000000"

        def greeting() -> str:
            phone.add_client(ANA, "Ana")
            phone.write(state["token"], ANA, "Hola")
            reply = phone.wait_reply(state["token"], ANA, 0, what="el saludo del negocio")
            return f"Ana escribió «Hola» y le llegó: «{reply['text'][:70]}…»"

        def receipts() -> str:
            first = phone.from_business(state["token"], ANA)[0]
            wait_for(lambda: phone.from_business(state["token"], ANA)[0]["status"] == "delivered", what="el ✓✓ en el teléfono")
            wait_for(lambda: any(m["author"] == "assistant" and m["status"] == "delivered" for m in _conversation(stack, "saas")["messages"]), what="el ✓✓ en el panel")
            phone.open(state["token"], ANA)
            wait_for(lambda: any(m["status"] == "read" for m in _conversation(stack, "saas")["messages"]), what="el leído en el panel")
            return f"el mensaje {first['id'][:8]}… pasó a ✓✓ y a leído, en el teléfono y en el panel"

        def question() -> str:
            before = len(phone.from_business(state["token"], ANA))
            phone.write(state["token"], ANA, "¿Qué venden?")
            reply = phone.wait_reply(state["token"], ANA, before, what="la respuesta del asistente")
            assert "planes" in reply["text"], reply["text"]
            return f"el asistente respondió: «{reply['text']}»"

        def payment() -> str:
            before = len(phone.from_business(state["token"], ANA))
            phone.write(state["token"], ANA, "Quiero pagar por Nequi")
            reply = phone.wait_reply(state["token"], ANA, before, what="los datos de Nequi")
            assert reply["text"].startswith("💳 *Datos para pagar*") and "*Nequi*" in reply["text"] and nequi in reply["text"], reply["text"]
            assert all(nequi not in prompt for prompt in stack.model.prompts), "el número de pago llegó a la IA"
            return "le llegaron los datos de Nequi ordenados, con el número real; la IA nunca vio el número"

        def resend() -> str:
            before = len(phone.from_business(state["token"], ANA))
            phone.write(state["token"], ANA, "Se me borró el número, ¿me lo envías otra vez?")
            reply = phone.wait_reply(state["token"], ANA, before, what="el reenvío de los datos")
            assert nequi in reply["text"] and "no puedo" not in reply["text"].lower(), reply["text"]
            return "la IA dijo «no puedo enviarlo» y aun así le llegaron los datos (la red de seguridad)"

        def receipt_photo() -> str:
            before = len(phone.from_business(state["token"], ANA))
            phone.write(state["token"], ANA, "Ya pagué, este es el comprobante", kind="image", file_base64=RECEIPT_PNG, mime_type="image/png", file_name="pago.png")
            reply = phone.wait_reply(state["token"], ANA, before, what="la respuesta al comprobante")
            thread = wait_for(lambda: (lambda c: c if c["conversation"]["needs_human"] else None)(_conversation(stack, "saas")), what="el chat pasa a una persona")
            photo = next(m for m in thread["messages"] if m["kind"] == "image")
            assert photo.get("media_note"), photo
            assert stack.alerts and stack.alerts[-1], "el equipo no recibió el aviso"
            return f"la foto se descargó del simulador, la IA la leyó como comprobante, el chat pasó al equipo y le llegó: «{reply['text'][:60]}…»"

        def team_reply() -> str:
            conversation_id = _conversation(stack, "saas")["conversation"]["id"]
            before = len(phone.from_business(state["token"], ANA))
            sent = panel.post(f"/api/conversations/{conversation_id}/messages", json={"text": "Hola Ana, ya confirmamos tu pago. ¡Gracias!"})
            assert sent.status_code == 201, sent.text
            reply = phone.wait_reply(state["token"], ANA, before, what="la respuesta del equipo en el teléfono")
            assert reply["text"] == "Hola Ana, ya confirmamos tu pago. ¡Gracias!"
            return "el equipo respondió desde el panel y le llegó a Ana por WhatsApp"

        def team_file() -> str:
            conversation_id = _conversation(stack, "saas")["conversation"]["id"]
            before = len(phone.from_business(state["token"], ANA))
            sent = panel.post(
                f"/api/conversations/{conversation_id}/attachments",
                content=b"%PDF-1.4\n% factura de prueba\n",
                headers={"Content-Type": "application/pdf", "X-File-Name": quote("factura.pdf"), "X-Caption": quote("Tu factura 🧾")},
            )
            assert sent.status_code == 201, sent.text
            document = phone.wait_reply(state["token"], ANA, before, what="el PDF en el teléfono")
            assert (document["kind"], document["text"], document["media"]["file_name"]) == ("document", "Tu factura 🧾", "factura.pdf"), document
            return "el equipo envió un PDF con su texto desde el panel y a Ana le llegó como documento"

        def from_business_phone() -> str:
            phone.write(state["token"], ANA, "Te escribo desde el celular del negocio", from_business_phone=True)
            wait_for(lambda: any(m["author"] == "agent" and m["body"] == "Te escribo desde el celular del negocio" for m in _conversation(stack, "saas")["messages"]), what="lo escrito desde el celular en el panel")
            return "lo que el negocio escribió desde su celular quedó en el panel como respuesta del equipo"

        def disconnect() -> str:
            result = panel.post("/api/businesses/saas/channels/whatsapp/disconnect").json()
            assert result["status"] == "disconnected" and phone.instance() is None, result
            return "el panel desconectó el número y el simulador lo borró"

        _run(Report("Un día de negocio por WhatsApp"), (
            ("Conectar WhatsApp por QR", connect),
            ("El cliente saluda", greeting),
            ("Entregado y leído", receipts),
            ("Una pregunta al asistente", question),
            ("Elegir Nequi para pagar", payment),
            ("«Se me borró el número»", resend),
            ("El comprobante en foto", receipt_photo),
            ("El equipo responde desde el panel", team_reply),
            ("El equipo envía un PDF", team_file),
            ("El negocio escribe desde su celular", from_business_phone),
            ("Desconectar", disconnect),
        ))


def test_a_business_from_another_country(monkeypatch, tmp_path):
    with running_stack(monkeypatch, tmp_path, ["saas"], mutate=_peru) as stack:
        phone = stack.phone
        state: dict = {}

        def connect() -> str:
            state["token"] = _connect(stack, "saas", "51987000000")
            phone.add_client("51912345678", "Rosa")
            phone.write(state["token"], "51912345678", "Hola")
            phone.wait_reply(state["token"], "51912345678", 0, what="el saludo")
            return "un negocio de Perú conectó su número (+51) y Rosa le escribió"

        def ask(text: str, expected: str, what: str) -> str:
            before = len(phone.from_business(state["token"], "51912345678"))
            phone.write(state["token"], "51912345678", text)
            reply = phone.wait_reply(state["token"], "51912345678", before, what=what)
            assert expected in reply["text"], reply["text"]
            return reply["text"]

        def yape() -> str:
            text = ask("Te pago por Yape", "*Yape*", "los datos de Yape")
            assert "A nombre de: Asesor Comercial S.A.C." in text and "Envía la captura con tu nombre." in text
            return "le llegaron los datos de Yape con el titular y la instrucción del negocio"

        def nu() -> str:
            text = ask("¿Y si te pago por Nu?", "*Nu*", "los datos de Nu")
            assert "son los mismos" not in text
            return "la IA dijo «los datos son los mismos» y aun así le llegaron los de Nu («otro medio»)"

        def cash() -> str:
            text = ask("Mejor en efectivo", "Pagas al asesor cuando te visite.", "la instrucción del efectivo")
            assert "comprobante" not in text
            return "le llegó cómo pagar en efectivo, sin pedirle comprobante"

        _run(Report("Un negocio de otro país (Perú)"), (
            ("Conectar y saludar", connect),
            ("Pagar por Yape", yape),
            ("Cambiar a «otro medio» (Nu)", nu),
            ("Pagar en efectivo", cash),
        ))


def test_two_businesses_never_cross(monkeypatch, tmp_path):
    with running_stack(monkeypatch, tmp_path, ["saas", "restaurant"]) as stack:
        phone = stack.phone
        tokens: dict[str, str] = {}

        def connect_both() -> str:
            tokens["saas"] = _connect(stack, "saas", "573110000001")
            tokens["restaurant"] = _connect(stack, "restaurant", "573110000002")
            assert tokens["saas"] != tokens["restaurant"]
            return "los dos negocios conectaron su propio número"

        def same_customer_writes_to_both() -> str:
            phone.add_client(ANA, "Ana")
            phone.write(tokens["saas"], ANA, "Hola, ¿qué venden?")
            phone.write(tokens["restaurant"], ANA, "Hola, ¿qué venden?")
            saas = phone.wait_reply(tokens["saas"], ANA, 0, what="la respuesta del negocio de software")
            restaurant = phone.wait_reply(tokens["restaurant"], ANA, 0, what="la respuesta del restaurante")
            assert saas["text"] != restaurant["text"] or saas["id"] != restaurant["id"]
            return "Ana le escribió a los dos y cada uno le respondió por su propio número"

        def each_panel_sees_only_its_chat() -> str:
            saas, restaurant = _conversation(stack, "saas"), _conversation(stack, "restaurant")
            assert saas["conversation"]["id"] != restaurant["conversation"]["id"]
            assert saas["conversation"]["business"]["slug"] == "saas" and restaurant["conversation"]["business"]["slug"] == "restaurant"
            return "cada negocio tiene su propia conversación con Ana; nada se cruzó"

        def payment_data_never_cross() -> str:
            saas_values = set(payment_values(_runtime("saas")))
            restaurant_values = set(payment_values(_runtime("restaurant")))
            before = len(phone.from_business(tokens["restaurant"], ANA))
            phone.write(tokens["restaurant"], ANA, "Quiero pagar por Nequi")
            reply = phone.wait_reply(tokens["restaurant"], ANA, before, what="los datos del restaurante")
            assert not any(value in reply["text"] for value in saas_values - restaurant_values), "le llegaron datos del otro negocio"
            return "al restaurante le pidió los datos de pago y nunca le llegaron los del otro negocio"

        _run(Report("Dos negocios a la vez"), (
            ("Conectar los dos", connect_both),
            ("La misma clienta le escribe a los dos", same_customer_writes_to_both),
            ("Cada panel ve solo lo suyo", each_panel_sees_only_its_chat),
            ("Los datos de pago no se cruzan", payment_data_never_cross),
        ))
