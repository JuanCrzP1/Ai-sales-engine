"""Atención humana completa (Fase 3): horario del equipo, avisos al equipo y la IA que retoma lo que nadie atendió.

- El horario del equipo sale de «Mi negocio», de uno propio o es «siempre hay alguien». Dentro de él, al pasar un chat a una persona
  la IA se pausa y el cliente sabe cuánto suele tardar el equipo; fuera de él, la IA sigue ayudando y le dice cuándo lo atienden.
- Desde que la IA se pausa, el cliente espera. La respuesta del equipo (desde el panel o desde el celular) termina la espera.
- Si nadie responde a tiempo, la IA retoma el chat una sola vez, pide disculpas, responde lo pendiente y avisa al equipo. Después no
  se vuelve a pausar sola hasta que alguien del equipo lo atienda.
- Cada aviso sale una sola vez por correo (Resend) y por notificación (Web Push, cifrada y firmada). Las pruebas del panel nunca.
- La API del panel guarda los ajustes con validación, solo para el dueño, y activa las notificaciones de cada navegador.
- La revisión periódica de Vercel necesita `CRON_SECRET`.
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import http_ece
import httpx
import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.admin_api.main import create_app
from app.api.controllers import attention_tasks, whatsapp_qr_webhook
from app.application.attention.resume_sweep import ResumeSweep, Throttle
from app.application.channels.inbound import ChannelInbound
from app.business_config_application.access import BusinessAccess
from app.business_config_application.attention import SUMMARY_LABEL, TeamAlerts, alert_email
from app.business_config_application.ports import EmailNotSent, PushOutcome
from app.domain.business_config.access import Principal
from app.domain.business_config.attention import (
    AttentionSettings,
    HoursRange,
    clock_text,
    handoff_plan,
    hours_text,
    is_open,
    next_opening,
    resume_due,
    validated,
    wait_text,
    when_text,
)
from app.domain.business_config.channels import ChannelSecrets
from app.domain.business_config.conversations import AppendResult, NewMessage
from app.domain.business_config.errors import InvalidFieldsError
from app.domain.business_config.push import PushMessage, PushSubscription, validated_subscription
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import (
    _refresh_outdated_checks,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.push_store import PushStore
from app.infrastructure.business_config.tables import business_members, conversations, notification_deliveries, platform_keys, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore
from app.infrastructure.notifications.resend_email import RESEND_URL, ResendEmailSender
from app.infrastructure.notifications.web_push import WebPushSender

BOGOTA = ZoneInfo("America/Bogota")
WEEKDAYS = ("lunes", "martes", "miercoles", "jueves", "viernes")
OFFICE = (HoursRange(WEEKDAYS, "08:00", "18:00"), HoursRange(("sabado",), "09:00", "13:00"))
ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
TOKENS = {"token-de-ana": ANA, "token-de-beto": BETO}
PHONE = "573001112233"
PUSH_ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"
# El nombre del negocio de ejemplo importado (el de la tabla `tenants`, que es el que ven los avisos).
BUSINESS_NAME = load_example("restaurant").name


def at(text: str) -> datetime:
    """Una hora de Colombia, en UTC (como las guarda todo el sistema)."""
    return datetime.fromisoformat(text).replace(tzinfo=BOGOTA).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# El horario y lo que se le dice al cliente
# ---------------------------------------------------------------------------

def test_the_team_hours_come_from_my_business_another_schedule_or_always():
    wednesday_10am, wednesday_9pm = at("2026-11-11T10:00"), at("2026-11-11T21:00")
    assert handoff_plan(AttentionSettings(), OFFICE, wednesday_10am).pause_ai is True
    assert handoff_plan(AttentionSettings(), OFFICE, wednesday_9pm).pause_ai is False
    always = AttentionSettings(hours_mode="always")
    assert handoff_plan(always, OFFICE, wednesday_9pm).pause_ai is True
    nights = AttentionSettings(hours_mode="custom", team_hours=(HoursRange(("miercoles",), "20:00", "23:00"),))
    assert handoff_plan(nights, OFFICE, wednesday_9pm).pause_ai is True and handoff_plan(nights, OFFICE, wednesday_10am).pause_ai is False
    # Sin horario en «Mi negocio», siempre hay alguien.
    assert handoff_plan(AttentionSettings(), (), wednesday_9pm).pause_ai is True


def test_inside_the_hours_the_ai_pauses_and_the_customer_knows_how_long_the_team_takes():
    plan = handoff_plan(AttentionSettings(reply_minutes=15), OFFICE, at("2026-11-11T10:00"))
    assert (plan.team_available, plan.pause_ai, plan.notice) == (True, True, "Una persona de nuestro equipo te responderá en unos 15 minutos.")
    assert handoff_plan(AttentionSettings(reply_minutes=0), OFFICE, at("2026-11-11T10:00")).notice is None
    assert (wait_text(60), wait_text(120), wait_text(5)) == ("una hora", "unas 2 horas", "unos 5 minutos")


def test_outside_the_hours_the_ai_keeps_helping_and_says_when_a_person_will_write():
    friday_night = handoff_plan(AttentionSettings(), OFFICE, at("2026-11-13T20:00"))
    assert friday_night.notice == (
        "Nuestro equipo atiende de lunes a viernes de 8:00 a. m. a 6:00 p. m. y el sábado de 9:00 a. m. a 1:00 p. m. "
        "Una persona te escribirá mañana a las 9:00 a. m. Mientras tanto, sigo aquí para ayudarte en lo que pueda."
    )
    saturday_afternoon = handoff_plan(AttentionSettings(), OFFICE, at("2026-11-14T15:00"))
    assert "Una persona te escribirá el lunes a las 8:00 a. m." in saturday_afternoon.notice
    early = handoff_plan(AttentionSettings(), OFFICE, at("2026-11-11T06:30"))
    assert "Una persona te escribirá hoy a las 8:00 a. m." in early.notice
    custom = handoff_plan(AttentionSettings(), OFFICE, at("2026-11-13T20:00"), after_hours_message="Mañana te escribe Laura.")
    assert (custom.pause_ai, custom.notice) == (False, "Mañana te escribe Laura.")


def test_hours_are_said_like_a_person_would():
    assert hours_text((HoursRange(("lunes", "miercoles", "viernes"), "13:00", "17:30"),)) == "lunes, miércoles y viernes de 1:00 p. m. a 5:30 p. m."
    assert hours_text((HoursRange(("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"), "07:00", "12:00"),)) == (
        "todos los días de 7:00 a. m. a 12:00 m."
    )
    noon = at("2026-11-11T12:00")
    assert when_text(at("2026-11-12T13:00"), BOGOTA, noon) == "mañana a la 1:00 p. m."
    assert clock_text(datetime(2026, 1, 1, 0, 15).time()) == "12:15 a. m."
    assert is_open(OFFICE, BOGOTA, at("2026-11-11T17:59")) and not is_open(OFFICE, BOGOTA, at("2026-11-11T18:00"))
    assert next_opening((), BOGOTA, noon) is None


def test_invalid_settings_say_what_and_where():
    with pytest.raises(InvalidFieldsError) as error:
        validated(
            hours_mode="custom", team_hours=[{"days": ["lunes", "lunes"], "opens": "18:00", "closes": "08:00"}, "no"], timezone_name="Marte/Base",
            reply_minutes=7, resume_after_minutes=3, email_enabled="sí", email_to="sin-arroba",
        )
    assert {issue.path for issue in error.value.issues} == {
        "team_hours[0].days", "team_hours[0].closes", "team_hours[1]", "timezone", "reply_minutes", "resume_after_minutes", "email_enabled", "email_to",
    }
    good = validated(
        hours_mode="custom", team_hours=[{"days": ["sabado"], "opens": "09:00", "closes": "13:00"}], timezone_name="America/Mexico_City",
        reply_minutes=30, resume_after_minutes=None, email_enabled=False, email_to="  ",
    )
    assert (good.team_hours, good.resume_after_minutes, good.email_to) == ((HoursRange(("sabado",), "09:00", "13:00"),), None, None)
    with pytest.raises(InvalidFieldsError):
        validated(hours_mode="custom", team_hours=[], timezone_name="America/Bogota", reply_minutes=10, resume_after_minutes=30, email_enabled=True, email_to=None)


def test_the_ai_resumes_only_after_the_chosen_wait():
    now = at("2026-11-11T10:00")
    settings = AttentionSettings(resume_after_minutes=30)
    assert not resume_due(settings, now - timedelta(minutes=29), now)
    assert resume_due(settings, now - timedelta(minutes=30), now)
    assert not resume_due(AttentionSettings(resume_after_minutes=None), now - timedelta(days=1), now)
    assert not resume_due(settings, None, now)


# ---------------------------------------------------------------------------
# El almacén: la espera del cliente y la IA que retoma
# ---------------------------------------------------------------------------

@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'plataforma.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=key)
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    yield engine, service, key
    engine.dispose()


def _chat(store: ConversationStore, text: str = "Hola", *, channel: str = "whatsapp", contact: str = PHONE) -> str:
    return store.append("restaurant", channel=channel, contact_ref=contact, contact_name="Laura", message=NewMessage("customer", text)).conversation_id


def _summary(store: ConversationStore, conversation_id: str):
    return store.thread(conversation_id)[0]


def _waited(engine, conversation_id: str, minutes: int) -> None:
    """El cliente lleva `minutes` esperando."""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    with engine.begin() as conn:
        conn.execute(update(conversations).where(conversations.c.id == conversation_id_key(conversation_id)).values(customer_waiting_since=since))


def conversation_id_key(value: str):
    import uuid

    return uuid.UUID(value)


def test_a_handoff_inside_the_hours_pauses_and_the_customer_starts_waiting(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    chat = _chat(store, "Quiero hablar con alguien")
    notification = store.request_handoff(chat, "human_request", "Quiero hablar con alguien")
    summary = _summary(store, chat)
    assert notification and (summary.ai_paused, summary.needs_human) == (True, True) and summary.customer_waiting_since is not None
    # Mientras siga esperando, no hay más avisos.
    assert store.request_handoff(chat, "human_request") is None
    store.append("restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("customer", "¿Hola?"))
    assert _summary(store, chat).customer_waiting_since == summary.customer_waiting_since


def test_a_handoff_outside_the_hours_waits_for_a_person_without_pausing(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    chat = _chat(store)
    assert store.request_handoff(chat, "complaint", "Llegó frío", pause_ai=False)
    summary = _summary(store, chat)
    assert (summary.ai_paused, summary.needs_human, summary.customer_waiting_since) == (False, True, None)


def test_the_team_reply_ends_the_wait_and_takes_the_chat(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    chat = _chat(store)
    store.request_handoff(chat, "human_request")
    store.append("restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("agent", "Hola Laura, ya te ayudo"))
    assert _summary(store, chat).customer_waiting_since is None
    store.append("restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("customer", "Gracias"))
    assert _summary(store, chat).customer_waiting_since is not None  # Le escribió al equipo: ahora espera su respuesta.
    store.resolve_handoff(chat)
    assert _summary(store, chat).customer_waiting_since is None


def test_the_ai_resumes_a_chat_only_once_and_tells_the_team(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    chat = _chat(store)
    store.request_handoff(chat, "human_request")
    _waited(engine, chat, 31)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    assert [item.id for item in store.waiting_chats(waiting_before=cutoff)] == [chat]
    first = store.resume_waiting(chat, waiting_before=cutoff, minutes=30)
    assert first and store.resume_waiting(chat, waiting_before=cutoff, minutes=30) is None
    summary = _summary(store, chat)
    assert (summary.ai_paused, summary.needs_human, summary.customer_waiting_since) == (False, True, None) and summary.ai_resumed_at is not None
    alert = AttentionStore(engine).alert(first)
    assert (alert.kind, alert.title, alert.body) == ("ai_resumed", "La IA retomó el chat con Laura", "Nadie le respondió en 30 minutos. El chat sigue esperando a alguien del equipo.")


def test_a_chat_still_inside_its_wait_or_answered_by_the_team_is_not_resumed(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    chat = _chat(store)
    store.request_handoff(chat, "human_request")
    _waited(engine, chat, 10)
    assert store.resume_waiting(chat, waiting_before=datetime.now(timezone.utc) - timedelta(minutes=30), minutes=30) is None
    store.append("restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("agent", "Ya te atiendo"))
    assert store.resume_waiting(chat, waiting_before=datetime.now(timezone.utc), minutes=30) is None


def test_after_resuming_on_its_own_the_ai_does_not_pause_again_until_someone_attends(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    chat = _chat(store)
    store.request_handoff(chat, "human_request")
    _waited(engine, chat, 45)
    store.resume_waiting(chat, waiting_before=datetime.now(timezone.utc) - timedelta(minutes=30), minutes=30)
    store.request_handoff(chat, "human_request", "¡Quiero una persona!")
    assert _summary(store, chat).ai_paused is False  # Sin pausas cada media hora para quien insiste.
    store.append("restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("agent", "Hola, soy Laura"))
    store.set_ai_paused(chat, False)
    store.request_handoff(chat, "human_request")
    assert _summary(store, chat).ai_paused is True


def test_test_chats_never_wait_and_pending_text_is_what_the_customer_wrote_while_waiting(platform):
    engine, _service, _key = platform
    store = ConversationStore(engine)
    test_chat = store.record("restaurant", channel="prueba", contact_ref="sesion", contact_name="Prueba", messages=[NewMessage("customer", "Hola")], handoff=True)
    assert _summary(store, test_chat).customer_waiting_since is None
    chat = _chat(store, "Quiero una persona")
    store.request_handoff(chat, "human_request")
    since = _summary(store, chat).customer_waiting_since
    store.append("restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None, message=NewMessage("customer", "¿Tienen domicilio?"))
    store.append(
        "restaurant", channel="whatsapp", contact_ref=PHONE, contact_name=None,
        message=NewMessage("customer", "", kind="audio", media_note="Y también quiero saber el horario"),
    )
    assert store.pending_customer_text(chat, since=since) == "¿Tienen domicilio?\n[Y también quiero saber el horario]"


def test_an_old_local_database_accepts_the_new_alerts(tmp_path):
    path = tmp_path / "anterior.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE tenants (id CHAR(32) PRIMARY KEY);
            CREATE TABLE conversations (id CHAR(32) PRIMARY KEY);
            CREATE TABLE notifications (id CHAR(32) PRIMARY KEY, tenant_id CHAR(32) NOT NULL REFERENCES tenants(id), conversation_id CHAR(32),
              kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT, created_at DATETIME NOT NULL,
              CONSTRAINT notifications_kind_check CHECK (kind IN ('handoff')));
            CREATE TABLE notification_reads (notification_id CHAR(32) NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
              user_id TEXT NOT NULL, read_at DATETIME NOT NULL, PRIMARY KEY (notification_id, user_id));
            INSERT INTO tenants VALUES ('t');
            INSERT INTO notifications VALUES ('n', 't', NULL, 'handoff', 'Laura pidió hablar con una persona', NULL, '2026-11-10 10:00:00');
            INSERT INTO notification_reads VALUES ('n', 'ana', '2026-11-10 11:00:00');
            """
        )
    engine = create_business_config_engine(f"sqlite:///{path.as_posix()}")
    _refresh_outdated_checks(engine)
    with engine.begin() as conn:
        assert "ai_resumed" in conn.exec_driver_sql("SELECT sql FROM sqlite_master WHERE name = 'notifications'").scalar()
        conn.exec_driver_sql("INSERT INTO notifications VALUES ('m', 't', NULL, 'ai_resumed', 'La IA retomó', NULL, '2026-11-11 10:00:00')")
        assert conn.exec_driver_sql("SELECT count(*) FROM notification_reads").scalar() == 1
        assert conn.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    engine.dispose()


# ---------------------------------------------------------------------------
# El motor: WhatsApp al pasar a una persona y al retomar
# ---------------------------------------------------------------------------

SECRETS = ChannelSecrets(tenant_slug="restaurant", server_url="https://free.uazapi.com", instance_token="token-de-instancia", webhook_id="w" * 32)


class FakeServer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_text(self, token, phone, text):
        self.sent.append((phone, text))
        return f"WA-{len(self.sent)}"

    def presence(self, *_args, **_kwargs):
        return None

    def download(self, *_args):
        return None


class FakeGateway:
    """La bandeja vista desde el motor, con lo que pidió cada paso."""

    def __init__(self) -> None:
        self.appended: list[NewMessage] = []
        self.handoffs: list[tuple[str, str, bool]] = []

    def append(self, tenant_slug, *, channel, contact_ref, contact_name, message, media=None):
        self.appended.append(message)
        return AppendResult("chat-1", f"entry-{len(self.appended)}", True, False)

    def update_entry(self, *args, **kwargs):
        return None

    def set_typing(self, *args):
        return None

    def request_handoff(self, conversation_id, reason, detail=None, *, pause_ai=True, summary=None):
        self.handoffs.append((conversation_id, reason, pause_ai))
        return "aviso-1"

    def ai_paused(self, conversation_id):
        return False

    def team_replied(self, conversation_id):
        return None


SECTIONS = {
    "config": {
        "profile": {"opening_hours": [{"days": list(WEEKDAYS), "opens": "08:00", "closes": "18:00"}]},
        "attention_messages": {"ai_resumed": "Perdón la demora, sigo yo."},
    }
}


def _inbound(server, gateway, *, reply=("Te paso con alguien del equipo.", {"intent": "info", "handoff": True, "handoff_reason": "human_request"}),
             attention=None, clock=None, alerts=None, sections=SECTIONS):
    return ChannelInbound(
        conversations=gateway,
        server=lambda _url: server,
        responder=lambda slug, phone, text: reply,
        media=None,
        api_key=lambda _slug: None,
        usage=lambda _slug: None,
        sections=lambda _slug: sections,
        set_status=lambda *args, **kwargs: None,
        mark_delivery=lambda *args: 0,
        attention=attention,
        alerts=alerts,
        clock=clock,
    )


def _customer(text: str):
    from app.domain.business_config.channels import IncomingMessage

    return IncomingMessage(message_id="MSG1", phone=PHONE, contact_name="Laura", text=text)


def test_inside_the_hours_the_chat_pauses_the_customer_is_told_the_wait_and_the_team_is_alerted():
    server, gateway, alerts = FakeServer(), FakeGateway(), []
    inbound = _inbound(server, gateway, clock=lambda: at("2026-11-11T10:00"), alerts=alerts.append)
    inbound.process(SECRETS, _customer("Quiero hablar con una persona"), AppendResult("chat-1", "entry-0", True, False))
    assert [text for _phone, text in server.sent] == ["Te paso con alguien del equipo.", "Una persona de nuestro equipo te responderá en unos 10 minutos."]
    assert gateway.handoffs == [("chat-1", "human_request", True)] and alerts == ["aviso-1"]


def test_outside_the_hours_the_ai_keeps_helping_and_says_when_a_person_will_write():
    server, gateway, alerts = FakeServer(), FakeGateway(), []
    inbound = _inbound(server, gateway, clock=lambda: at("2026-11-11T21:00"), alerts=alerts.append)
    inbound.process(SECRETS, _customer("Quiero hablar con una persona"), AppendResult("chat-1", "entry-0", True, False))
    assert server.sent[-1][1] == (
        "Nuestro equipo atiende de lunes a viernes de 8:00 a. m. a 6:00 p. m. Una persona te escribirá mañana a las 8:00 a. m. "
        "Mientras tanto, sigo aquí para ayudarte en lo que pueda."
    )
    assert gateway.handoffs == [("chat-1", "human_request", False)] and alerts == ["aviso-1"]


def test_if_the_attention_settings_cannot_be_read_the_chat_still_goes_to_a_person():
    server, gateway = FakeServer(), FakeGateway()

    def broken(_slug):
        raise RuntimeError("sin base")

    _inbound(server, gateway, attention=broken).process(SECRETS, _customer("Una persona, por favor"), AppendResult("chat-1", "entry-0", True, False))
    assert gateway.handoffs == [("chat-1", "human_request", True)] and len(server.sent) == 1


def test_when_the_ai_resumes_it_apologizes_and_answers_what_was_pending():
    server, gateway = FakeServer(), FakeGateway()
    asked = []
    inbound = _inbound(server, gateway, reply=("Sí, tenemos domicilio hasta las 9 p. m.", {"intent": "info"}))
    inbound._responder = lambda slug, phone, text: (asked.append(text), ("Sí, tenemos domicilio hasta las 9 p. m.", {"intent": "info"}))[1]
    inbound.continue_after_resume(SECRETS, "chat-1", PHONE, "¿Tienen domicilio?")
    assert [text for _phone, text in server.sent] == ["Perdón la demora, sigo yo.", "Sí, tenemos domicilio hasta las 9 p. m."]
    assert asked == ["¿Tienen domicilio?"]
    # Sin mensaje del negocio, el de la plataforma; sin nada pendiente, solo la disculpa.
    server.sent.clear()
    _inbound(server, gateway, sections={}).continue_after_resume(SECRETS, "chat-1", PHONE, "")
    assert [text for _phone, text in server.sent] == ["Disculpa la espera. Mientras alguien del equipo se libera, sigo ayudándote yo."]


def test_the_sweep_resumes_only_due_chats_and_each_one_once(platform):
    engine, _service, _key = platform
    store, attention = ConversationStore(engine), AttentionStore(engine)
    due, recent, other = _chat(store, contact="1"), _chat(store, contact="2"), _chat(store, contact="3")
    for chat in (due, recent, other):
        store.request_handoff(chat, "human_request")
    _waited(engine, due, 40)
    _waited(engine, recent, 12)
    _waited(engine, other, 50)
    with engine.begin() as conn:
        restaurant = conn.execute(select(tenants.c.id).where(tenants.c.slug == "restaurant")).scalar_one()
        saas = conn.execute(select(tenants.c.id).where(tenants.c.slug == "saas")).scalar_one()
        conn.execute(update(conversations).where(conversations.c.id == conversation_id_key(other)).values(tenant_id=saas))
    attention.save_attention_settings("saas", AttentionSettings(resume_after_minutes=None))
    continued, alerted = [], []
    sweep = ResumeSweep(
        waiting=store.waiting_chats, settings=attention.attention_settings, resume=store.resume_waiting, pending=store.pending_customer_text,
        secrets=lambda _slug, _channel: SECRETS, continue_chat=lambda secrets, chat, phone, text: continued.append((chat, phone)), alerts=alerted.append,
    )
    result = sweep.run()
    assert (result.checked, result.resumed) == (3, 1) and continued == [(due, "1")] and len(alerted) == 1
    assert sweep.run().resumed == 0  # Ya lo retomó: no se repite.
    assert restaurant is not None


def test_a_throttle_lets_it_run_at_most_once_per_window():
    now = [0.0]
    throttle = Throttle(60, clock=lambda: now[0])
    assert throttle.acquire() and not throttle.acquire()
    now[0] = 61
    assert throttle.acquire()


# ---------------------------------------------------------------------------
# Avisos al equipo: correo y notificaciones
# ---------------------------------------------------------------------------

class FakeEmail:
    def __init__(self, configured: bool = True, fail: bool = False) -> None:
        self.configured = configured
        self.fail = fail
        self.sent: list[dict] = []

    def send(self, *, to, subject, html, text, idempotency_key=None):
        if self.fail:
            raise EmailNotSent("Resend rechazó el correo (403): dominio sin verificar.")
        self.sent.append({"to": to, "subject": subject, "html": html, "text": text, "key": idempotency_key})
        return "correo-1"


class FakePush:
    def __init__(self, outcomes: dict[str, str] | None = None) -> None:
        self.outcomes = outcomes or {}
        self.sent: list[tuple[str, PushMessage]] = []

    def send(self, subscription, message):
        self.sent.append((subscription.endpoint, message))
        return PushOutcome(self.outcomes.get(subscription.endpoint, "sent"))


def _subscription(user: str, endpoint: str) -> PushSubscription:
    client = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    b64 = lambda raw: base64.urlsafe_b64encode(raw).decode().rstrip("=")  # noqa: E731
    return validated_subscription(user, endpoint=endpoint, p256dh=b64(client), auth=b64(os.urandom(16)), device="Chrome en Android")


def _handoff_alert(engine, *, channel: str = "whatsapp") -> tuple[str, str]:
    store = ConversationStore(engine)
    chat = _chat(store, "Quiero hablar con alguien", channel=channel)
    return chat, store.request_handoff(chat, "human_request", "Quiero hablar con alguien <script>")


def test_a_handoff_is_emailed_once_to_the_owner_with_a_link_to_the_chat(platform):
    engine, _service, key = platform
    attention = AttentionStore(engine)
    attention.remember_email(ANA.user_id, ANA.email)
    chat, notification = _handoff_alert(engine)
    email = FakeEmail()
    alerts = TeamAlerts(attention, email=email, panel_url="https://panel.example.com/")
    alerts.deliver(notification)
    alerts.deliver(notification)
    (sent,) = email.sent
    assert sent["to"] == ["ana@example.com"] and sent["key"] == f"aviso-{notification}"
    assert sent["subject"] == f"Laura pidió hablar con una persona · {BUSINESS_NAME}"
    assert f"https://panel.example.com/negocios/restaurant/conversaciones?c={chat}" in sent["text"]
    assert "&lt;script&gt;" in sent["html"] and "<script>" not in sent["html"]
    assert attention.delivery(notification, "email") == ("sent", None)


def test_the_email_goes_to_the_chosen_address_or_is_skipped_with_its_reason(platform):
    engine, _service, _key = platform
    attention = AttentionStore(engine)
    attention.save_attention_settings("restaurant", AttentionSettings(email_to="equipo@restaurante.com"))
    _chat_id, notification = _handoff_alert(engine)
    email = FakeEmail()
    TeamAlerts(attention, email=email).deliver(notification)
    assert email.sent[0]["to"] == ["equipo@restaurante.com"]

    attention.save_attention_settings("restaurant", AttentionSettings(email_enabled=False))
    store = ConversationStore(engine)
    second = store.request_handoff(_chat(store, contact="2"), "complaint")
    TeamAlerts(attention, email=email).deliver(second)
    assert len(email.sent) == 1 and attention.delivery(second, "email") is None

    attention.save_attention_settings("restaurant", AttentionSettings())
    third = store.request_handoff(_chat(store, contact="3"), "complaint")
    TeamAlerts(attention, email=FakeEmail(configured=False)).deliver(third)
    assert attention.delivery(third, "email") == ("skipped", "correo no activado en la plataforma")

    attention.remember_email(ANA.user_id, ANA.email)
    fourth = store.request_handoff(_chat(store, contact="4"), "complaint")
    TeamAlerts(attention, email=FakeEmail(fail=True)).deliver(fourth)
    assert attention.delivery(fourth, "email")[0] == "failed"


def test_push_reaches_every_device_of_the_team_and_forgets_the_gone_ones(platform):
    engine, _service, key = platform
    attention, push_store = AttentionStore(engine), PushStore(engine, key)
    phone, laptop = _subscription(ANA.user_id, PUSH_ENDPOINT), _subscription(ANA.user_id, "https://updates.push.services.mozilla.com/wpush/v2/xyz")
    stranger = _subscription(BETO.user_id, "https://web.push.apple.com/QWERTY")
    for item in (phone, laptop, stranger):
        push_store.subscribe(item)
    chat, notification = _handoff_alert(engine)
    push = FakePush({laptop.endpoint: "gone"})
    TeamAlerts(attention, push_storage=push_store, push=push).deliver(notification)
    assert sorted(endpoint for endpoint, _message in push.sent) == sorted([phone.endpoint, laptop.endpoint])
    message = push.sent[0][1]
    assert message.url == f"/negocios/restaurant/conversaciones?c={chat}" and message.tag == chat and message.title == "Laura pidió hablar con una persona"
    assert [item.endpoint for item in push_store.subscriptions_for([ANA.user_id])] == [phone.endpoint]
    assert attention.delivery(notification, "push") == ("sent", "1 de 2 dispositivos")


def test_test_chats_never_alert_and_a_resumed_chat_is_not_emailed(platform):
    engine, _service, key = platform
    attention, push_store = AttentionStore(engine), PushStore(engine, key)
    attention.remember_email(ANA.user_id, ANA.email)
    push_store.subscribe(_subscription(ANA.user_id, PUSH_ENDPOINT))
    store = ConversationStore(engine)
    test_chat = store.record("restaurant", channel="prueba", contact_ref="s", contact_name="Prueba", messages=[NewMessage("customer", "Hola")])
    test_alert = store.request_handoff(test_chat, "human_request")
    email, push = FakeEmail(), FakePush()
    alerts = TeamAlerts(attention, push_storage=push_store, email=email, push=push)
    alerts.deliver(test_alert)
    assert email.sent == [] and push.sent == []
    chat = _chat(store)
    store.request_handoff(chat, "human_request")
    _waited(engine, chat, 40)
    resumed = store.resume_waiting(chat, waiting_before=datetime.now(timezone.utc) - timedelta(minutes=30), minutes=30)
    alerts.deliver(resumed)
    assert email.sent == [] and [message.title for _endpoint, message in push.sent] == ["La IA retomó el chat con Laura"]


def test_the_email_has_text_and_html_and_escapes_what_the_customer_wrote():
    subject, text, body = alert_email(title="Laura tiene un reclamo", business_name="Sabor & Casa", detail='"<b>frío</b>"', link="https://x/?c=1&d=2", footer_business="Sabor & Casa")
    assert subject == "Laura tiene un reclamo · Sabor & Casa"
    assert "«\"<b>frío</b>\"»" in text and "Abrir el chat: https://x/?c=1&d=2" in text
    assert "&lt;b&gt;frío&lt;/b&gt;" in body and "Sabor &amp; Casa" in body and 'href="https://x/?c=1&amp;d=2"' in body


def test_the_email_shows_the_team_note_as_what_the_customer_needs_not_as_a_quote():
    note = "Laura pidió 3 almuerzos <b>sin cebolla</b> y quiere confirmar la hora."
    _subject, text, body = alert_email(title="Laura pidió hablar con una persona", business_name="Sabor", detail=None, link=None, footer_business="Sabor", summary=note)
    assert f"{SUMMARY_LABEL}: {note}" in text and "«" not in text
    assert SUMMARY_LABEL in body and "&lt;b&gt;sin cebolla&lt;/b&gt;" in body


# ---------------------------------------------------------------------------
# Conectores: Resend y Web Push
# ---------------------------------------------------------------------------

def test_resend_receives_the_email_with_its_idempotency_key_and_its_errors_are_explained():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if json.loads(request.content)["to"] == ["malo@example.com"]:
            return httpx.Response(403, json={"message": "The example.com domain is not verified."})
        return httpx.Response(200, json={"id": "re_123"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    sender = ResendEmailSender("re_clave", "Avisos <avisos@negocio.com>", client=client)
    assert sender.configured and sender.send(to=["ana@example.com"], subject="Hola", html="<p>Hola</p>", text="Hola", idempotency_key="aviso-1") == "re_123"
    request = seen[0]
    assert str(request.url) == RESEND_URL and request.headers["authorization"] == "Bearer re_clave" and request.headers["idempotency-key"] == "aviso-1"
    assert json.loads(request.content)["from"] == "Avisos <avisos@negocio.com>"
    with pytest.raises(EmailNotSent, match="403.*not verified"):
        sender.send(to=["malo@example.com"], subject="x", html="x", text="x")
    with pytest.raises(EmailNotSent, match="no está activado"):
        ResendEmailSender("", None).send(to=["a@b.co"], subject="x", html="x", text="x")


def test_web_push_is_encrypted_for_that_browser_signed_by_the_platform_and_gone_ones_are_reported(platform):
    engine, _service, key = platform
    store = PushStore(engine, key)
    browser_key = ec.generate_private_key(ec.SECP256R1())
    auth = os.urandom(16)
    b64 = lambda raw: base64.urlsafe_b64encode(raw).decode().rstrip("=")  # noqa: E731
    public = browser_key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    subscription = validated_subscription(ANA.user_id, endpoint=PUSH_ENDPOINT, p256dh=b64(public), auth=b64(auth))
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(410 if "gone" in str(request.url) else 201)

    sender = WebPushSender(store.vapid_keys, subject="https://panel.example.com", client=httpx.Client(transport=httpx.MockTransport(handler)))
    message = PushMessage(title="Laura pidió hablar con una persona", body="Sabor Casero: Quiero hablar", url="/negocios/restaurant/conversaciones?c=1", tag="1")
    assert sender.send(subscription, message).status == "sent"
    request = seen[0]
    assert request.headers["content-encoding"] == "aes128gcm" and request.headers["ttl"] == "86400" and request.headers["urgency"] == "high"
    assert request.headers["authorization"].startswith("vapid t=") and f"k={store.vapid_public_key()}" in request.headers["authorization"]
    # Solo ese navegador puede leerla.
    plain = http_ece.decrypt(request.content, private_key=browser_key, auth_secret=auth, version="aes128gcm")
    assert json.loads(plain) == {"title": message.title, "body": message.body, "url": message.url, "tag": "1"}
    gone = PushSubscription(PUSH_ENDPOINT + "gone", subscription.p256dh, subscription.auth)
    assert sender.send(gone, message).status == "gone"


def test_only_known_push_services_are_accepted():
    good = _subscription(ANA.user_id, PUSH_ENDPOINT)
    assert good.device == "Chrome en Android"
    for endpoint in ("http://fcm.googleapis.com/x", "https://evil.example.com/push", "https://fcm.googleapis.com.evil.com/x", "https://127.0.0.1/x", ""):
        with pytest.raises(InvalidFieldsError):
            validated_subscription(ANA.user_id, endpoint=endpoint, p256dh=good.p256dh, auth=good.auth)
    with pytest.raises(InvalidFieldsError):
        validated_subscription(ANA.user_id, endpoint=PUSH_ENDPOINT, p256dh="corta", auth=good.auth)
    assert validated_subscription(ANA.user_id, endpoint="https://wns2-bl2p.notify.windows.com/w/?token=1", p256dh=good.p256dh, auth=good.auth)


def test_the_platform_keys_are_created_once_and_kept_encrypted(platform):
    engine, _service, key = platform
    first, again = PushStore(engine, key).vapid_keys(), PushStore(engine, key).vapid_keys()
    assert first == again and len(base64.urlsafe_b64decode(first.public_key + "==")) == 65
    with engine.connect() as conn:
        stored = conn.execute(select(platform_keys.c.secret_ciphertext)).scalar_one()
    assert first.private_key not in stored
    assert PushStore(engine, key).vapid_public_key() == first.public_key


# ---------------------------------------------------------------------------
# La API del panel
# ---------------------------------------------------------------------------

class Tokens:
    def verify(self, token: str) -> Principal | None:
        return TOKENS.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def api(platform):
    engine, service, key = platform
    email, push = FakeEmail(), FakePush()
    app = create_app(
        service,
        access=BusinessAccess(service, BusinessMembersStore(engine)),
        verifier=Tokens(),
        conversations=ConversationStore(engine),
        notifications=NotificationStore(engine),
        usage=UsageCounterStore(engine),
        attention=AttentionStore(engine),
        push_storage=PushStore(engine, key),
        email=email,
        push=push,
    )
    yield engine, TestClient(app), email, push


def test_the_attention_settings_start_with_the_defaults_and_save_only_what_is_valid(api):
    engine, client, _email, _push = api
    current = client.get("/api/businesses/restaurant/attention", headers=_as("ana")).json()
    assert {key: current[key] for key in ("hours_mode", "timezone", "reply_minutes", "resume_after_minutes", "email_enabled", "email_to")} == {
        "hours_mode": "business", "timezone": "America/Bogota", "reply_minutes": 10, "resume_after_minutes": 30, "email_enabled": True, "email_to": None,
    }
    assert current["account_emails"] == ["ana@example.com"] and current["email_available"] is True and current["business_hours"] == []
    assert {"id": "America/Bogota", "label": "Colombia"} in current["options"]["timezones"]
    # El restaurante de ejemplo no tiene horario: «el de mi negocio» se guarda y, mientras tanto, siempre hay alguien.
    kept = client.put("/api/businesses/restaurant/attention", headers=_as("ana"), json={**current, "reply_minutes": 15})
    assert (kept.status_code, kept.json()["reply_minutes"], kept.json()["team_available_now"]) == (200, 15, True)
    invalid = client.put("/api/businesses/restaurant/attention", headers=_as("ana"), json={**current, "hours_mode": "custom", "team_hours": [], "reply_minutes": 7})
    assert invalid.status_code == 422 and {issue["path"] for issue in invalid.json()["issues"]} == {"team_hours", "reply_minutes"}
    saved = client.put(
        "/api/businesses/restaurant/attention", headers=_as("ana"),
        json={**current, "hours_mode": "custom", "team_hours": [{"days": ["lunes"], "opens": "08:00", "closes": "12:00"}], "resume_after_minutes": None,
              "email_to": "caja@restaurante.com"},
    ).json()
    assert (saved["hours_mode"], saved["team_hours"], saved["resume_after_minutes"], saved["email_to"]) == (
        "custom", [{"days": ["lunes"], "opens": "08:00", "closes": "12:00"}], None, "caja@restaurante.com",
    )
    assert AttentionStore(engine).attention_settings("restaurant").email_to == "caja@restaurante.com"


def test_someone_elses_attention_answers_like_a_business_that_does_not_exist(api):
    _engine, client, _email, _push = api
    assert client.get("/api/businesses/saas/attention", headers=_as("ana")).status_code == 404
    assert client.put("/api/businesses/saas/attention", headers=_as("ana"), json={}).status_code == 404
    assert client.get("/api/businesses/restaurant/attention").status_code == 401


def test_the_account_email_is_remembered_for_the_alerts(api):
    engine, client, _email, _push = api
    client.get("/api/businesses", headers=_as("ana"))
    assert AttentionStore(engine).owner_emails("restaurant") == ["ana@example.com"]
    assert AttentionStore(engine).owner_emails("saas") == []


def test_the_test_email_says_where_it_went(api):
    _engine, client, email, _push = api
    assert client.post("/api/businesses/restaurant/attention/test-email", headers=_as("ana")).json() == {"sent_to": ["ana@example.com"]}
    assert email.sent[0]["subject"] == f"Así te llegarán los avisos · {BUSINESS_NAME}"
    email.fail = True
    failed = client.post("/api/businesses/restaurant/attention/test-email", headers=_as("ana"))
    assert failed.status_code == 502 and "no verificado" not in failed.json()["message"] and failed.json()["code"] == "email_not_sent"


def test_each_browser_turns_notifications_on_and_off(api):
    _engine, client, _email, push = api
    status = client.get("/api/notifications/push", params={"endpoint": PUSH_ENDPOINT}, headers=_as("ana")).json()
    assert len(status["public_key"]) > 80 and status["subscribed"] is False
    sub = _subscription(ANA.user_id, PUSH_ENDPOINT)
    body = {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}, "device": "Safari en iPhone"}
    assert client.post("/api/notifications/push", headers=_as("ana"), json={**body, "endpoint": "https://evil.example.com"}).status_code == 422
    assert client.post("/api/notifications/push", headers=_as("ana"), json=body).status_code == 204
    assert client.get("/api/notifications/push", params={"endpoint": PUSH_ENDPOINT}, headers=_as("ana")).json()["subscribed"] is True
    assert client.get("/api/notifications/push", params={"endpoint": PUSH_ENDPOINT}, headers=_as("beto")).json()["subscribed"] is False
    assert client.post("/api/notifications/push/test", headers=_as("ana"), json={"endpoint": PUSH_ENDPOINT}).status_code == 204
    assert push.sent[-1][1].title == "Notificaciones activadas"
    assert client.post("/api/notifications/push/remove", headers=_as("ana"), json={"endpoint": PUSH_ENDPOINT}).status_code == 204
    assert client.get("/api/notifications/push", params={"endpoint": PUSH_ENDPOINT}, headers=_as("ana")).json()["subscribed"] is False


def test_the_inbox_shows_since_when_the_customer_waits_and_when_the_ai_resumed(api):
    engine, client, _email, _push = api
    store = ConversationStore(engine)
    chat = _chat(store)
    store.request_handoff(chat, "human_request")
    item = client.get(f"/api/conversations/{chat}", headers=_as("ana")).json()["conversation"]
    assert item["customer_waiting_since"] and item["ai_resumed_at"] is None


# ---------------------------------------------------------------------------
# La revisión periódica (Vercel)
# ---------------------------------------------------------------------------

def test_the_periodic_check_needs_the_cron_secret(monkeypatch):
    app = FastAPI()
    app.include_router(attention_tasks.router)
    client = TestClient(app)
    monkeypatch.delenv("CRON_SECRET", raising=False)
    assert client.post("/internal/attention/run").status_code == 503
    monkeypatch.setenv("CRON_SECRET", "corto")
    assert client.post("/internal/attention/run", headers={"Authorization": "Bearer corto"}).status_code == 503
    monkeypatch.setenv("CRON_SECRET", "una-llave-larga-de-la-revision")
    assert client.get("/internal/attention/run", headers={"Authorization": "Bearer otra"}).status_code == 401
    from app.application.attention.resume_sweep import SweepResult

    monkeypatch.setattr(whatsapp_qr_webhook, "run_resume_sweep", lambda: SweepResult(checked=4, resumed=1))
    ok = client.get("/internal/attention/run", headers={"Authorization": "Bearer una-llave-larga-de-la-revision"})
    assert ok.json() == {"status": "ok", "checked": 4, "resumed": 1}


def test_vercel_runs_the_check_every_fifteen_minutes():
    from pathlib import Path

    config = json.loads((Path(__file__).resolve().parents[1] / "project" / "vercel.json").read_text(encoding="utf-8"))
    assert config["schedules"] == {"atencion-humana": {"schedule": "*/15 * * * *", "path": "/api/v1/internal/attention/run"}}


def test_the_traffic_check_only_runs_in_vercel_or_when_asked(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("ATTENTION_SWEEP_ON_TRAFFIC", raising=False)
    assert whatsapp_qr_webhook.traffic_sweep_enabled() is False
    monkeypatch.setenv("ATTENTION_SWEEP_ON_TRAFFIC", "1")
    assert whatsapp_qr_webhook.traffic_sweep_enabled() is True
    monkeypatch.delenv("ATTENTION_SWEEP_ON_TRAFFIC")
    monkeypatch.setenv("VERCEL", "1")
    assert whatsapp_qr_webhook.traffic_sweep_enabled() is True


def test_every_delivery_row_belongs_to_one_alert_and_channel(platform):
    engine, _service, _key = platform
    attention = AttentionStore(engine)
    _chat_id, notification = _handoff_alert(engine)
    assert attention.claim_delivery(notification, "email") and not attention.claim_delivery(notification, "email")
    assert attention.claim_delivery(notification, "push")
    with engine.connect() as conn:
        assert conn.execute(select(notification_deliveries.c.channel).order_by(notification_deliveries.c.channel)).scalars().all() == ["email", "push"]
