"""Los recordatorios avisan cuando llega su hora.

Con la base real (SQLite), la API del panel «en la nube» y notificaciones de mentira:
- un recordatorio que llegó a su hora avisa una sola vez en la campana: a su responsable; sin responsable, a todo el equipo; si su
  responsable ya no es del equipo, también a todo el equipo;
- uno que se marcó hecho antes no avisa (si se vuelve a abrir, sí); uno futuro todavía no; uno que venció hace días sin avisar, tampoco;
- cada persona ve en su campana solo los avisos para ella o para todos, y «marcar todo como leído» solo toca los suyos;
- la notificación al celular va solo a los dispositivos del responsable, sin correo, y abre la ficha del cliente en Recordatorios;
- la revisión avisa cada uno aunque la notificación de otro falle, y nunca toca las conversaciones de prueba.
"""
from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert, select, update

from app.admin_api.main import create_app
from app.application.attention.reminder_sweep import ReminderSweep
from app.business_config_application.access import BusinessAccess
from app.business_config_application.attention import TeamAlerts
from app.business_config_application.ports import PushOutcome
from app.domain.business_config.access import Principal
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.push import validated_subscription
from app.domain.business_config.reminders import alert_text
from app.infrastructure.business_config import reminder_store
from app.infrastructure.business_config.attention_store import AttentionStore
from app.infrastructure.business_config.commerce_store import CommerceStore
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.notification_store import NotificationStore
from app.infrastructure.business_config.push_store import PushStore
from app.infrastructure.business_config.tables import business_members, customer_reminders, notifications, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
CARO = Principal(user_id="usuario-caro", email="caro@example.com")
BASE = "/api/businesses/restaurant"


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-caro": CARO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


def _soon(hours: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _later(hours: float) -> datetime:
    """Un momento del futuro: la revisión «corre» entonces."""
    return datetime.now(timezone.utc) + timedelta(hours=hours)


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'avisos.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=key)
    import_example(service, load_example("restaurant"))
    with engine.begin() as conn:
        tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == "restaurant")).scalar_one()
        # Ana es la dueña del restaurante y Caro su asesora.
        for user, role in ((ANA, "owner"), (CARO, "agent")):
            conn.execute(business_members.insert().values(tenant_id=tenant_id, user_id=user.user_id, role=role, email=user.email, created_at=datetime.now(timezone.utc)))
    store = ConversationStore(engine)
    app = create_app(
        service, None, access=BusinessAccess(service, BusinessMembersStore(engine)), verifier=Tokens(), conversations=store,
        notifications=NotificationStore(engine), usage=UsageCounterStore(engine), commerce=CommerceStore(engine),
    )
    yield engine, store, TestClient(app), key
    engine.dispose()


def _chat(store: ConversationStore, contact: str, name: str | None, *, channel: str = "whatsapp") -> str:
    return store.append("restaurant", channel=channel, contact_ref=contact, contact_name=name, message=NewMessage("customer", "Hola")).conversation_id


def _remind(client: TestClient, conversation_id: str, title: str, hours: float, user: str = "ana", **extra) -> str:
    made = client.post(f"{BASE}/customers/{conversation_id}/reminders", json={"title": title, "due_at": _soon(hours), **extra}, headers=_as(user))
    assert made.status_code == 201, made.text
    return made.json()["id"]


def _bell(client: TestClient, user: str) -> dict:
    return client.get("/api/notifications", headers=_as(user)).json()


# ------------------------------------------------------------------ la campana


def test_a_due_reminder_alerts_once_in_the_bell_of_its_owner_and_without_owner_of_everyone(platform):
    engine, store, client, _key = platform
    laura, pedro = _chat(store, "573001", "Laura"), _chat(store, "573002", None)
    _remind(client, laura, "Llamar para cerrar", 1, user="caro")  # sin elegir: para Caro, que lo crea
    _remind(client, pedro, "Enviar la propuesta", 2, assignee_id="")  # para nadie: para todo el equipo
    _remind(client, laura, "Confirmar la entrega", 30)  # todavía no

    created = reminder_store.alert_due_reminders(engine, now=_later(3))
    assert len(created) == 2
    assert reminder_store.alert_due_reminders(engine, now=_later(4)) == []  # cada uno avisa una sola vez

    caro = _bell(client, "caro")
    assert caro["unread"] == 2
    # Los dos avisan en la misma revisión (el mismo momento): el orden entre ellos no importa.
    assert sorted((item["kind"], item["title"], item["body"], item["conversation_id"]) for item in caro["items"]) == [
        ("reminder", "Recordatorio: Enviar la propuesta", "Cliente: 573002", pedro),  # sin nombre, su número
        ("reminder", "Recordatorio: Llamar para cerrar", "Cliente: Laura", laura),
    ]
    ana = _bell(client, "ana")
    assert (ana["unread"], [item["title"] for item in ana["items"]]) == (1, ["Recordatorio: Enviar la propuesta"])

    # «Marcar todo como leído» de Ana no toca el aviso de Caro.
    assert client.post("/api/notifications/read", json={}, headers=_as("ana")).json() == {"marked": 1}
    assert (_bell(client, "ana")["unread"], _bell(client, "caro")["unread"]) == (0, 2)


def test_done_future_and_too_old_reminders_do_not_alert_and_a_reopened_one_does(platform):
    engine, store, client, _key = platform
    laura = _chat(store, "573001", "Laura")
    done = _remind(client, laura, "Llamar", 1)
    client.patch(f"{BASE}/reminders/{done}", json={"done": True}, headers=_as("ana"))
    old = _remind(client, laura, "Muy viejo", 1)
    with engine.begin() as conn:
        conn.execute(update(customer_reminders).where(customer_reminders.c.id == reminder_store._key(old, ValueError, "x")).values(due_at=_later(-24 * 4)))
    _remind(client, laura, "Más adelante", 48)
    assert reminder_store.alert_due_reminders(engine, now=_later(2)) == []

    # Se vuelve a abrir: si ya le llegó la hora, avisa en la siguiente revisión.
    client.patch(f"{BASE}/reminders/{done}", json={"done": False}, headers=_as("ana"))
    assert len(reminder_store.alert_due_reminders(engine, now=_later(2))) == 1
    # Uno que ya avisó y se marca hecho y se vuelve a abrir no avisa otra vez.
    client.patch(f"{BASE}/reminders/{done}", json={"done": True}, headers=_as("ana"))
    client.patch(f"{BASE}/reminders/{done}", json={"done": False}, headers=_as("ana"))
    assert reminder_store.alert_due_reminders(engine, now=_later(3)) == []


def test_if_its_owner_left_the_team_the_whole_team_is_alerted(platform):
    engine, store, client, _key = platform
    laura = _chat(store, "573001", "Laura")
    _remind(client, laura, "Llamar", 1, assignee_id=CARO.user_id)
    with engine.begin() as conn:
        conn.execute(delete(business_members).where(business_members.c.user_id == CARO.user_id))
    (notification_id,) = reminder_store.alert_due_reminders(engine, now=_later(2))
    with engine.connect() as conn:
        assert conn.execute(select(notifications.c.recipient_id).where(notifications.c.id == reminder_store._key(notification_id, ValueError, "x"))).scalar_one() is None
    assert [item["title"] for item in _bell(client, "ana")["items"]] == ["Recordatorio: Llamar"]


def test_test_conversations_never_alert(platform):
    engine, store, _client, _key = platform
    test_chat = _chat(store, "s1", "Prueba", channel="prueba")
    with engine.begin() as conn:
        tenant_id = conn.execute(select(tenants.c.id).where(tenants.c.slug == "restaurant")).scalar_one()
        conn.execute(
            insert(customer_reminders).values(
                tenant_id=tenant_id, conversation_id=store._key(test_chat), title="x", due_at=_later(-1), created_at=datetime.now(timezone.utc)
            )
        )
    assert reminder_store.alert_due_reminders(engine, now=_later(0)) == []


def test_the_alert_says_what_to_do_and_with_whom():
    assert alert_text("Llamar para cerrar", " Laura ", "573001") == ("Recordatorio: Llamar para cerrar", "Cliente: Laura")
    assert alert_text("Llamar", None, "573001")[1] == "Cliente: 573001"


# ------------------------------------------------------------------ al celular


class FakePush:
    def __init__(self) -> None:
        self.sent: list[tuple[str, object]] = []

    def send(self, subscription, message):
        self.sent.append((subscription.endpoint, message))
        return PushOutcome("sent")


class FakeEmail:
    configured = True

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, **email):
        self.sent.append(email)
        return "correo-1"


def _subscription(user: str, endpoint: str):
    client = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    b64 = lambda raw: base64.urlsafe_b64encode(raw).decode().rstrip("=")  # noqa: E731
    return validated_subscription(user, endpoint=endpoint, p256dh=b64(client), auth=b64(os.urandom(16)), device="Chrome en Android")


def test_the_push_reaches_only_the_owner_without_email_and_opens_the_customer_file(platform):
    engine, store, client, key = platform
    attention, push_store = AttentionStore(engine), PushStore(engine, key)
    attention.remember_email(ANA.user_id, ANA.email)  # el correo de avisos está listo: aun así, un recordatorio no se envía por correo
    caro_phone = _subscription(CARO.user_id, "https://fcm.googleapis.com/fcm/send/caro")
    for item in (_subscription(ANA.user_id, "https://fcm.googleapis.com/fcm/send/ana"), caro_phone):
        push_store.subscribe(item)
    laura = _chat(store, "573001", "Laura")
    _remind(client, laura, "Llamar para cerrar", 1, assignee_id=CARO.user_id)

    push, email = FakePush(), FakeEmail()
    alerts = TeamAlerts(attention, push_storage=push_store, email=email, push=push)
    (notification_id,) = reminder_store.alert_due_reminders(engine, now=_later(2))
    alerts.deliver(notification_id)
    alerts.deliver(notification_id)  # una sola vez
    ((endpoint, message),) = push.sent
    assert endpoint == caro_phone.endpoint and email.sent == []
    assert (message.title, message.body) == ("Recordatorio: Llamar para cerrar", f"{load_example('restaurant').name}: Cliente: Laura")
    assert message.url == f"/negocios/restaurant/clientes?vista=recordatorios&cliente={laura}"
    assert message.tag == notification_id  # no reemplaza en el celular el aviso del chat de Laura
    assert attention.delivery(notification_id, "push") == ("sent", "1 de 1 dispositivos")

    # Sin responsable, a los dispositivos de todo el equipo.
    _remind(client, laura, "Enviar la propuesta", 1, assignee_id="")
    (team_alert,) = reminder_store.alert_due_reminders(engine, now=_later(2))
    alerts.deliver(team_alert)
    assert len(push.sent) == 3


# ------------------------------------------------------------------ la revisión


def test_the_sweep_alerts_each_one_even_if_one_push_fails():
    delivered: list[str] = []

    def deliver(notification_id: str | None) -> None:
        if notification_id == "falla":
            raise RuntimeError("sin red")
        delivered.append(str(notification_id))

    seen: list[datetime] = []
    moment = datetime(2026, 11, 28, 15, 0, tzinfo=timezone.utc)

    def due(*, now: datetime) -> list[str]:
        seen.append(now)
        return ["uno", "falla", "dos"]

    assert ReminderSweep(alert_due=due, alerts=deliver, clock=lambda: moment).run() == 3
    assert delivered == ["uno", "dos"] and seen == [moment]
