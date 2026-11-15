"""Esperar a que el cliente termine de escribir (`application/channels/inbound.py`, 15 nov 2026).

Por WhatsApp la gente parte lo que quiere decir en varios mensajes seguidos. El asistente espera unos segundos después de cada uno; si
llega otro, vuelve a esperar, y cuando el cliente se detiene responde una sola vez a todo. Cada mensaje lo procesa su propio proceso
(en la nube, quizá en otro servidor): quién responde se decide en la base, que aquí es la real (SQLite). El reloj es simulado: nada
espera de verdad.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from app.application.channels.inbound import MAX_UNDERSTANDING_WAIT_SECONDS, ChannelInbound
from app.domain.business_config.channels import ChannelSecrets, IncomingMessage
from app.domain.business_config.conversations import NewMessage
from app.domain.business_config.reply_timing import DEFAULT_REPLY_DELAY_SECONDS, MAX_REPLY_WAIT_SECONDS, reply_delay
from app.infrastructure.business_config.conversation_store import ConversationStore
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example

PHONE = "573001112233"
SECRETS = ChannelSecrets(tenant_slug="saas", server_url="https://servidor.test", instance_token="token", webhook_id="webhook-1")


@pytest.fixture
def store(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'bandeja.sqlite3').as_posix()}")
    create_local_schema(engine)
    import_example(build_business_config_service(engine, secrets_key=Fernet.generate_key().decode()), load_example("saas"))
    yield ConversationStore(engine)
    engine.dispose()


class Gateway:
    """La bandeja real, como la ve el motor (`runtime_access`)."""

    def __init__(self, store: ConversationStore):
        self.store = store

    def __getattr__(self, name):
        return getattr(self.store, name)

    def ai_paused(self, conversation_id):
        return self.store.is_ai_paused(conversation_id)


class Server:
    def __init__(self):
        self.sent: list[str] = []

    def send_text(self, _token, _phone, text):
        self.sent.append(text)
        return f"WA-{len(self.sent)}"

    def presence(self, *_args, **_kwargs):
        return None

    def download(self, *_args):
        return None


class Clock:
    """El reloj del proceso: avanza solo cuando el asistente espera (`pause`). `during` corre algo en una espera, como lo que pasa
    en otro proceso mientras este espera (llega otro mensaje, se termina de entender un audio)."""

    def __init__(self):
        self.offset = timedelta()
        self.pauses: list[float] = []
        self.during: list = []

    def now(self):
        return datetime.now(timezone.utc) + self.offset

    def pause(self, seconds):
        self.pauses.append(seconds)
        self.offset += timedelta(seconds=seconds)
        if self.during:
            self.during.pop(0)()


def _setup(store, *, delay=None):
    server, clock, asked = Server(), Clock(), []
    sections = {"config": {"response": {"reply_delay_seconds": delay}}} if delay is not None else {}

    def responder(_slug, _phone, text):
        asked.append(text)
        return f"Respuesta a: {text}", {"intent": "info"}

    inbound = ChannelInbound(
        conversations=Gateway(store), server=lambda _secrets: server, responder=responder, media=None, api_key=lambda _slug: None,
        usage=lambda _slug: None, sections=lambda _slug: sections, set_status=lambda *a, **k: None, mark_delivery=lambda *a: 0,
        clock=clock.now, pause=clock.pause,
    )
    return inbound, server, clock, asked


def _arrives(store, text, number):
    """Un mensaje del cliente que llega por el webhook: se guarda enseguida (`receive`)."""
    message = IncomingMessage(message_id=f"MSG{number}", phone=PHONE, contact_name="Laura", text=text)
    stored = store.append("saas", channel="whatsapp", contact_ref=PHONE, contact_name="Laura",
                          message=NewMessage("customer", text, provider_message_id=f"MSG{number}"))
    return message, stored


def test_three_messages_in_a_row_get_one_answer_to_all_of_them(store):
    inbound, server, clock, asked = _setup(store)
    arrived = [_arrives(store, text, n) for n, text in enumerate(["Hola", "quiero el plan básico", "¿cuánto vale?"], start=1)]
    for message, stored in arrived:
        inbound.process(SECRETS, message, stored)
    assert asked == ["Hola\nquiero el plan básico\n¿cuánto vale?"]
    assert server.sent == ["Respuesta a: Hola\nquiero el plan básico\n¿cuánto vale?"]
    # Cada proceso esperó lo de la plataforma después de su mensaje.
    assert clock.pauses == [DEFAULT_REPLY_DELAY_SECONDS] * 3


def test_a_message_that_arrives_while_waiting_restarts_the_wait(store):
    inbound, server, clock, asked = _setup(store)
    first = _arrives(store, "Hola", 1)
    later = []
    clock.during.append(lambda: later.append(_arrives(store, "¿tienen Nequi?", 2)))
    inbound.process(SECRETS, *first)
    assert asked == [] and server.sent == []
    inbound.process(SECRETS, *later[0])
    assert asked == ["Hola\n¿tienen Nequi?"]


def test_a_message_after_the_answer_gets_its_own_answer(store):
    inbound, server, _clock, asked = _setup(store)
    inbound.process(SECRETS, *_arrives(store, "Hola", 1))
    inbound.process(SECRETS, *_arrives(store, "Gracias", 2))
    assert asked == ["Hola", "Gracias"] and len(server.sent) == 2


def test_a_message_that_arrives_while_the_assistant_answers_is_not_lost(store):
    """El asistente ya reclamó los mensajes y está respondiendo cuando llega otro: ese no entró en la respuesta, y su proceso lo
    responde después (antes de marcar cada mensaje, se habría perdido)."""
    inbound, server, _clock, asked = _setup(store)
    late: list = []
    original = inbound._responder

    def answering(slug, phone, text):
        if not late:
            late.append(_arrives(store, "y ¿hay descuento?", 2))
        return original(slug, phone, text)

    inbound._responder = answering
    inbound.process(SECRETS, *_arrives(store, "¿Cuánto vale?", 1))
    inbound.process(SECRETS, *late[0])
    assert asked == ["¿Cuánto vale?", "y ¿hay descuento?"] and len(server.sent) == 2


def test_a_customer_who_never_stops_writing_is_answered_after_the_limit(store):
    inbound, _server, clock, asked = _setup(store)
    first = _arrives(store, "Hola", 1)
    second = _arrives(store, "una pregunta", 2)
    store.set_reading(second[1].entry_id, "una pregunta")
    # Lleva escribiendo más que el límite: el proceso del primer mensaje responde a los dos, aunque haya uno más nuevo.
    clock.offset = timedelta(seconds=MAX_REPLY_WAIT_SECONDS)
    inbound.process(SECRETS, *first)
    assert asked == ["Hola\nuna pregunta"]
    inbound.process(SECRETS, *second)
    assert asked == ["Hola\nuna pregunta"]


def test_a_photo_or_audio_still_being_understood_is_waited_for_and_keeps_its_place(store):
    inbound, _server, clock, asked = _setup(store)
    audio = _arrives(store, "", 1)
    text = _arrives(store, "¿me puedes ayudar con eso?", 2)
    # Otro proceso termina de transcribir el audio mientras este espera.
    clock.during.extend([lambda: None, lambda: store.set_reading(audio[1].entry_id, "Quiero pagar el plan básico por Nequi")])
    inbound.process(SECRETS, *text)
    assert asked == ["Quiero pagar el plan básico por Nequi\n¿me puedes ayudar con eso?"]


def test_a_message_never_understood_does_not_block_the_answer_forever(store):
    inbound, _server, clock, asked = _setup(store)
    _arrives(store, "", 1)
    inbound.process(SECRETS, *_arrives(store, "¿hola?", 2))
    assert asked == ["¿hola?"]
    assert sum(clock.pauses) - DEFAULT_REPLY_DELAY_SECONDS >= MAX_UNDERSTANDING_WAIT_SECONDS


def test_while_a_person_attends_the_messages_are_the_teams_and_never_enter_a_later_answer(store):
    inbound, server, _clock, asked = _setup(store)
    message, stored = _arrives(store, "¿alguien me ayuda?", 1)
    store.team_replied(stored.conversation_id)
    inbound.process(SECRETS, message, store.append(
        "saas", channel="whatsapp", contact_ref=PHONE, contact_name="Laura", message=NewMessage("customer", "sigo aquí", provider_message_id="MSG2")
    ))
    assert asked == [] and server.sent == []
    # El equipo vuelve a activar el asistente sin responder: lo que escribió el cliente mientras tanto ya era del equipo.
    store.set_ai_paused(stored.conversation_id, False)
    inbound.process(SECRETS, *_arrives(store, "Hola de nuevo", 3))
    assert asked == ["Hola de nuevo"]


def test_with_zero_seconds_it_answers_at_once(store):
    inbound, _server, clock, asked = _setup(store, delay=0)
    inbound.process(SECRETS, *_arrives(store, "Hola", 1))
    assert asked == ["Hola"] and clock.pauses == []


def test_the_business_chooses_the_wait(store):
    inbound, _server, clock, _asked = _setup(store, delay=3)
    inbound.process(SECRETS, *_arrives(store, "Hola", 1))
    assert clock.pauses == [3]


def test_two_processes_never_claim_the_same_message(store):
    _message, stored = _arrives(store, "Hola", 1)
    assert store.claim(stored.conversation_id, [stored.entry_id]) == [stored.entry_id]
    assert store.claim(stored.conversation_id, [stored.entry_id]) == []


def test_the_wait_comes_from_what_the_business_published():
    assert reply_delay({}) == DEFAULT_REPLY_DELAY_SECONDS == 8
    assert reply_delay({"config": {"response": {"reply_delay_seconds": 0}}}) == 0
    assert reply_delay({"config": {"response": {"reply_delay_seconds": 12}}}) == 12
    assert reply_delay({"config": {"response": {"reply_delay_seconds": 99}}}) == 20
    assert reply_delay({"config": {"response": {"reply_delay_seconds": True}}}) == DEFAULT_REPLY_DELAY_SECONDS


def test_the_contract_accepts_from_0_to_20_seconds_and_publishes_it_only_when_chosen():
    from app.domain.business_config.compiler import compile_business_config
    from app.domain.business_config.contract.assistant import ResponseStyle

    assert ResponseStyle(reply_delay_seconds=0).reply_delay_seconds == 0
    for wrong in (-1, 21):
        with pytest.raises(ValidationError):
            ResponseStyle(reply_delay_seconds=wrong)
    from app.domain.business_config.contract import BusinessConfig

    example = load_example("saas")
    config = BusinessConfig.model_validate(example.document)
    assert "reply_delay_seconds" not in compile_business_config(config, example.payment_resolver())["config"]["response"]
    chosen = config.model_copy(update={"response_style": config.response_style.model_copy(update={"reply_delay_seconds": 5})})
    assert compile_business_config(chosen, example.payment_resolver())["config"]["response"]["reply_delay_seconds"] == 5
