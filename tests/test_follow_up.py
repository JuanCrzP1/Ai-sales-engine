"""El seguimiento a los clientes que dejaron de responder (Mensajes → Seguimiento): cuándo sale cada mensaje, a quién nunca, que no
salga dos veces y que se detenga cuando el cliente cierra la conversación.

Que lo publicado es lo que sale está en `test_business_config_engine_integration.py`; el lector con la IA real, en
`experiments/quality_lab/run_follow_up_eval.py`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.application.follow_up.follow_up_reading import reads_follow_up
from app.application.follow_up.follow_up_sweep import FollowUpSweep
from app.domain.business_config.attention import HoursRange
from app.domain.business_config.channels import ChannelSecrets
from app.domain.business_config.conversations import FollowUpCandidate, NewMessage
from app.domain.business_config.follow_up import STALE_AFTER, FollowUpPlan, FollowUpStepPlan, due_step
from app.infrastructure.ai.prompting.follow_up_reader import FOLLOW_UP_READER, follow_up_turn
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.tables import conversation_entries, conversations

NOW = datetime(2026, 11, 10, 20, 0, tzinfo=timezone.utc)  # un martes a las 3 p. m. en Bogotá
BOGOTA = ZoneInfo("America/Bogota")
PLAN = FollowUpPlan(
    enabled=True,
    business_hours_only=False,
    steps=(
        FollowUpStepPlan(timedelta(hours=1), "¿Pudiste revisarlo?"),
        FollowUpStepPlan(timedelta(days=1), "¿Seguimos?"),
        FollowUpStepPlan(timedelta(days=3), "Te escribo por última vez."),
    ),
)


# ---------------------------------------------------------------------------
# Cuándo toca cada mensaje
# ---------------------------------------------------------------------------

def test_each_message_goes_out_after_its_time_since_the_customer_stopped_writing():
    quiet = NOW - timedelta(minutes=59)
    assert due_step(PLAN, last_customer_at=quiet, sent=0, now=NOW) is None
    first = due_step(PLAN, last_customer_at=NOW - timedelta(minutes=61), sent=0, now=NOW)
    assert (first.index, first.message) == (0, "¿Pudiste revisarlo?")
    # Ya salió el primero: el segundo, al día siguiente.
    assert due_step(PLAN, last_customer_at=NOW - timedelta(hours=5), sent=1, now=NOW) is None
    second = due_step(PLAN, last_customer_at=NOW - timedelta(hours=25), sent=1, now=NOW)
    assert (second.index, second.message) == (1, "¿Seguimos?")
    assert due_step(PLAN, last_customer_at=NOW - timedelta(days=20), sent=3, now=NOW) is None


def test_when_several_are_due_only_the_latest_goes_out_and_an_old_one_never():
    # El negocio estuvo cerrado: pasaron el primero y el segundo; sale solo el segundo.
    latest = due_step(PLAN, last_customer_at=NOW - timedelta(hours=30), sent=0, now=NOW)
    assert (latest.index, latest.message) == (1, "¿Seguimos?")
    # Al encender el seguimiento, quien dejó de responder hace semanas no recibe nada.
    stale = due_step(PLAN, last_customer_at=NOW - timedelta(days=3) - STALE_AFTER - timedelta(minutes=1), sent=0, now=NOW)
    assert (stale.index, stale.message) == (2, None)


def test_with_business_hours_only_it_waits_for_the_business_to_open():
    hours = (HoursRange(("lunes", "martes", "miercoles", "jueves", "viernes"), "08:00", "18:00"),)
    plan = FollowUpPlan(enabled=True, business_hours_only=True, steps=PLAN.steps, business_hours=hours)
    assert plan.may_send_now(BOGOTA, NOW)
    assert not plan.may_send_now(BOGOTA, NOW + timedelta(hours=6))  # 9 p. m.
    # Sin horario escrito, a cualquier hora; si el negocio eligió «a cualquier hora», también.
    assert FollowUpPlan(enabled=True, steps=PLAN.steps).may_send_now(BOGOTA, NOW + timedelta(hours=6))
    assert PLAN.may_send_now(BOGOTA, NOW + timedelta(hours=6))
    assert not FollowUpPlan(enabled=False, steps=PLAN.steps).active and not FollowUpPlan(enabled=True).active


# ---------------------------------------------------------------------------
# La revisión, con el almacén de verdad
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'plataforma.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="Cjv0D1Gm8mWlcxx3ffl0qlFfxrdVdu7hIbo2hrvl0oA=")
    import_example(service, load_example("restaurant"))
    yield ConversationStore(engine)
    engine.dispose()


def _quiet_chat(store: ConversationStore, contact="573001", *, minutes_ago=90, channel="whatsapp", author="assistant") -> str:
    """Un chat en el que el cliente escribió hace `minutes_ago` y el negocio le respondió un minuto después."""
    chat = store.append("restaurant", channel=channel, contact_ref=contact, contact_name="Ana", message=NewMessage("customer", "¿Tienen mesa?"))
    store.append("restaurant", channel=channel, contact_ref=contact, contact_name=None, message=NewMessage(author, "Sí, ¿para cuántos?", status="sent"))
    _age(store, chat.conversation_id, minutes_ago)
    return chat.conversation_id


def _age(store: ConversationStore, conversation_id: str, minutes_ago: int) -> None:
    """Corre hacia atrás las horas del chat: el cliente escribió hace `minutes_ago` y lo demás un minuto después de cada uno."""
    key = store._key(conversation_id)
    with store._engine.begin() as conn:
        rows = conn.execute(select(conversation_entries.c.id).where(conversation_entries.c.conversation_id == key).order_by(conversation_entries.c.created_at)).all()
        start = NOW - timedelta(minutes=minutes_ago)
        for index, row in enumerate(rows):
            conn.execute(update(conversation_entries).where(conversation_entries.c.id == row.id).values(created_at=start + timedelta(minutes=index)))
        conn.execute(update(conversations).where(conversations.c.id == key).values(last_message_at=start + timedelta(minutes=len(rows) - 1)))


class Channel:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.remembered: list[tuple[str, str, str]] = []
        self.read: list[str] = []
        self.decision: bool | None = True
        self.deliver = True
        self.connected = True


def _sweep(store: ConversationStore, channel: Channel, plan: FollowUpPlan = PLAN, now: datetime = NOW) -> FollowUpSweep:
    def send(secrets, contact, text):
        if channel.deliver:
            channel.sent.append((contact, text))
        return channel.deliver

    def read(slug, messages, message):
        channel.read.append(message)
        return channel.decision

    return FollowUpSweep(
        candidates=store.follow_up_candidates,
        plan=lambda slug: plan,
        zone=lambda slug: BOGOTA,
        claim=store.claim_follow_up,
        release=store.release_follow_up,
        stop=store.stop_follow_up,
        recent=lambda conversation_id: [(m.author, m.body) for m in store.thread(conversation_id)[1]],
        read=read,
        secrets=lambda slug, name: ChannelSecrets(slug, "https://servidor", "token", "webhook", name) if channel.connected else None,
        send=send,
        remember=lambda slug, contact, text: channel.remembered.append((slug, contact, text)),
        clock=lambda: now,
    )


def test_the_customer_who_stopped_writing_gets_each_message_once_and_the_ai_sees_it(store):
    chat = _quiet_chat(store, minutes_ago=90)
    channel = Channel()
    result = _sweep(store, channel).run()
    assert (result.checked, result.sent) == (1, 1)
    assert channel.sent == [("573001", "¿Pudiste revisarlo?")] and channel.remembered == [("restaurant", "573001", "¿Pudiste revisarlo?")]
    # La siguiente revisión no lo repite.
    assert _sweep(store, channel).run().sent == 0 and len(channel.sent) == 1
    # Al día siguiente, el segundo.
    _sweep(store, channel, now=NOW + timedelta(days=1)).run()
    assert channel.sent[-1] == ("573001", "¿Seguimos?")
    assert store.thread(chat)[0].follow_up_stopped_by is None


def test_if_the_customer_writes_again_the_sequence_starts_over_when_they_go_quiet(store):
    chat = _quiet_chat(store, minutes_ago=90)
    channel = Channel()
    _sweep(store, channel).run()
    store.append("restaurant", channel="whatsapp", contact_ref="573001", contact_name=None, message=NewMessage("customer", "Para 4"))
    store.append("restaurant", channel="whatsapp", contact_ref="573001", contact_name=None, message=NewMessage("assistant", "¡Listo! ¿A qué hora?"))
    _age(store, chat, 70)
    _sweep(store, channel).run()
    assert [text for _, text in channel.sent] == ["¿Pudiste revisarlo?", "¿Pudiste revisarlo?"]


def test_a_follow_up_message_is_marked_in_the_inbox(store):
    from app.application.channels.inbound import ChannelInbound

    chat = _quiet_chat(store)

    class Server:
        def send_text(self, token, phone, text):
            return "WA-SEG-1"

    class Conversations:
        append = store.append

    inbound = ChannelInbound(
        conversations=Conversations(), server=lambda secrets: Server(), responder=None, media=None, api_key=lambda slug: None,
        usage=lambda slug: None, sections=lambda slug: {}, set_status=lambda *args, **kwargs: None, mark_delivery=lambda *args: 0,
    )
    assert inbound.send_follow_up(ChannelSecrets("restaurant", "https://s", "t", "w"), "573001", "¿Seguimos?")
    last = store.thread(chat)[1][-1]
    assert (last.author, last.body, last.intent, last.status) == ("assistant", "¿Seguimos?", "follow_up", "sent")


@pytest.mark.parametrize(
    "change",
    [
        "ai_paused",  # lo atiende el equipo
        "needs_human",  # espera a una persona
        "payment",  # avisó un pago
        "customer",  # ya compró
        "stopped",  # el equipo lo detuvo
    ],
)
def test_never_to_someone_the_team_handles_who_paid_or_whose_follow_up_was_stopped(store, change):
    chat = _quiet_chat(store)
    values = {
        "ai_paused": {"ai_paused": True},
        "needs_human": {"needs_human": True},
        "payment": {"stage": "payment"},
        "customer": {"stage": "customer"},
        "stopped": {"follow_up_stopped_at": NOW, "follow_up_stopped_by": "team"},
    }[change]
    with store._engine.begin() as conn:
        conn.execute(update(conversations).where(conversations.c.id == store._key(chat)).values(**values))
    channel = Channel()
    assert _sweep(store, channel).run().checked == 0 and channel.sent == []


def test_never_to_tests_other_channels_a_customer_waiting_for_an_answer_or_old_chats(store):
    _quiet_chat(store, "s1", channel="prueba")
    _quiet_chat(store, "web-1", channel="web")
    _quiet_chat(store, "573002", author="customer")  # el último mensaje es del cliente: espera respuesta, no seguimiento
    _quiet_chat(store, "573003", minutes_ago=60 * 24 * 40)  # hace 40 días
    _quiet_chat(store, "573004", minutes_ago=20)  # todavía no pasa ni media hora
    channel = Channel()
    assert _sweep(store, channel).run().checked == 0 and channel.sent == []


def test_if_the_customer_closed_the_conversation_the_follow_up_stops_for_good(store):
    chat = _quiet_chat(store)
    channel = Channel()
    channel.decision = False
    assert _sweep(store, channel).run().stopped == 1
    assert channel.sent == [] and store.thread(chat)[0].follow_up_stopped_by == "customer"
    channel.decision = True
    assert _sweep(store, channel, now=NOW + timedelta(days=1)).run().checked == 0


def test_without_a_reading_nothing_goes_out_and_the_next_sweep_tries_again(store):
    _quiet_chat(store)
    channel = Channel()
    channel.decision = None
    assert _sweep(store, channel).run().sent == 0 and channel.sent == []
    channel.decision = True
    assert _sweep(store, channel).run().sent == 1


def test_a_message_the_channel_did_not_deliver_is_not_retried(store):
    _quiet_chat(store)
    channel = Channel()
    channel.deliver = False
    assert _sweep(store, channel).run().sent == 0
    channel.deliver = True
    assert _sweep(store, channel).run().sent == 0 and channel.sent == [] and channel.remembered == []


def test_with_the_channel_disconnected_or_the_business_closed_it_waits(store):
    _quiet_chat(store)
    channel = Channel()
    channel.connected = False
    assert _sweep(store, channel).run().sent == 0 and channel.read == []
    channel.connected = True
    hours = (HoursRange(("lunes", "martes", "miercoles", "jueves", "viernes"), "08:00", "18:00"),)
    closed = FollowUpPlan(enabled=True, business_hours_only=True, steps=PLAN.steps, business_hours=hours)
    assert _sweep(store, channel, closed, now=NOW + timedelta(hours=6)).run().sent == 0
    assert _sweep(store, channel, closed).run().sent == 1


def test_an_old_message_is_skipped_without_sending_and_the_sequence_goes_on(store):
    chat = _quiet_chat(store, minutes_ago=60 * 24 * 7)  # hace una semana: el tercero (a los 3 días) ya es viejo
    channel = Channel()
    assert _sweep(store, channel).run().skipped == 1
    assert channel.sent == [] and channel.read == []
    assert store.follow_up_candidates(active_since=NOW - timedelta(days=40), quiet_before=NOW)[0].sent_since_last_message == 3
    assert store.thread(chat)[0].follow_up_stopped_by is None


def test_turned_off_nothing_goes_out(store):
    _quiet_chat(store)
    channel = Channel()
    assert _sweep(store, channel, FollowUpPlan(enabled=False, steps=PLAN.steps)).run().sent == 0 and channel.read == []


def test_taking_a_follow_up_is_one_operation(store):
    _quiet_chat(store)
    [candidate] = store.follow_up_candidates(active_since=NOW - timedelta(days=40), quiet_before=NOW)
    assert store.claim_follow_up(candidate, 1)
    assert not store.claim_follow_up(candidate, 1)  # otra revisión, con lo que leyó antes
    store.release_follow_up(candidate)
    assert store.claim_follow_up(candidate, 1)


# ---------------------------------------------------------------------------
# El lector y el panel
# ---------------------------------------------------------------------------

def test_the_reader_reads_the_end_of_the_chat_and_answers_only_with_a_clear_yes_or_no():
    calls = []

    class Runtime:
        answer = '{"enviar": false}'

        def classify(self, prompt, *, user_message, bot_config, max_tokens):
            calls.append((prompt, user_message))
            return self.answer

    runtime = Runtime()
    messages = [("customer", "¿Cuánto vale?"), ("assistant", "Vale $20.000"), ("customer", "No gracias, ya compré en otro lado")]
    assert reads_follow_up(runtime, bot_config=None, messages=messages, message="¿Seguimos?") is False
    assert calls[0] == (FOLLOW_UP_READER, follow_up_turn(messages, "¿Seguimos?"))
    assert "Cliente: No gracias, ya compré en otro lado" in calls[0][1] and "«¿Seguimos?»" in calls[0][1]
    runtime.answer = 'Claro: {"enviar": true}'
    assert reads_follow_up(runtime, bot_config=None, messages=messages, message="¿Seguimos?") is True
    runtime.answer = "no sé"
    assert reads_follow_up(runtime, bot_config=None, messages=messages, message="¿Seguimos?") is None
    assert reads_follow_up(runtime, bot_config=None, messages=[], message="¿Seguimos?") is None


def test_the_team_stops_and_resumes_the_follow_up_of_a_customer_from_the_panel(store):
    from test_conversations_inbox import ANA, BETO

    from app.business_config_application.access import BusinessAccess
    from app.business_config_application.conversations import ConversationsService

    class Access(BusinessAccess):
        def __init__(self):
            pass

        def require(self, principal, business, need=None):
            if principal is not ANA:
                from app.domain.business_config.errors import BusinessNotFoundError

                raise BusinessNotFoundError("ajeno")

    service = ConversationsService(store, Access())
    chat = _quiet_chat(store)
    assert service.set_follow_up(ANA, chat, active=False).follow_up_stopped_by == "team"
    assert store.follow_up_candidates(active_since=NOW - timedelta(days=40), quiet_before=NOW) == []
    assert service.set_follow_up(ANA, chat, active=True).follow_up_stopped_by is None
    assert len(store.follow_up_candidates(active_since=NOW - timedelta(days=40), quiet_before=NOW)) == 1
    from app.domain.business_config.errors import ConversationNotFoundError

    with pytest.raises(ConversationNotFoundError):
        service.set_follow_up(BETO, chat, active=False)


def test_a_candidate_counts_the_follow_ups_only_since_the_last_customer_message():
    at = NOW - timedelta(hours=2)
    assert FollowUpCandidate("c", "r", "whatsapp", "1", at, at, 2).sent_since_last_message == 2
    assert FollowUpCandidate("c", "r", "whatsapp", "1", at, at - timedelta(days=1), 2).sent_since_last_message == 0
    assert FollowUpCandidate("c", "r", "whatsapp", "1", at, None, 0).sent_since_last_message == 0
