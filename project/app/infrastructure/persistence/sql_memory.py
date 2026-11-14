"""La memoria del motor en PostgreSQL: lo que recuerda de cada cliente entre un mensaje y el siguiente.

Guarda dos cosas por negocio y cliente (`clients`, del esquema del motor en `project/docs/postgresql_schema.sql`):
- **los mensajes** (`conversation_messages`): la conversación que la IA ve como historial;
- **la memoria** (`conversation_memory.memory`, un JSON): el medio de pago elegido, el estado del pago, el paso de la conversación, la
  necesidad del cliente, la etapa, la hora de su último mensaje…

Reglas, porque en la nube cada mensaje puede llegar a un servidor distinto:
- **La base es la única fuente.** Ningún servidor guarda nada en su RAM entre mensajes: lo que escribe uno es lo que lee el siguiente.
  (Antes cada servidor respondía con su copia en RAM y podía recordar «Nequi» cuando el cliente ya había cambiado a Daviplata.)
- **Una lectura y una escritura por mensaje.** El motor atiende cada mensaje dentro de un turno (`turn`): al empezar se lee la memoria
  (y el historial, cuando se pide), durante el turno se lee y se escribe en esa copia, y al terminar se guarda todo en una sola
  transacción: los mensajes nuevos y solo los datos que cambiaron. Dos mensajes del mismo cliente atendidos a la vez no se borran lo
  que cambió el otro. Fuera de un turno (el panel, las pruebas), cada operación es su propio turno.
- **El historial son los mensajes más recientes** (`HISTORY_LIMIT`), en orden. (Antes eran los primeros 40: en un chat largo la IA
  respondía con lo de hace rato.) Cada mensaje lleva su hora exacta para que el orden no dependa de la transacción.
- **Si la base no responde**, el turno sigue sin memoria: lee vacío, no guarda nada y deja el aviso `memoria_no_disponible`. Nunca
  guarda en la RAM de un servidor lo que no pudo guardar en la base (eso partía la memoria entre servidores).

Borrar a un cliente o las pruebas del panel (`forget_contact`, `forget_contacts_with_prefix`) sí avisa si falla: el panel debe saberlo.
Las pruebas contra un PostgreSQL de verdad están en `tests/test_memory_postgres.py`.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.domain.conversation.memory import ConversationState
from app.utils.logger import logger

# Los mensajes más recientes que se leen como historial. La IA ve los últimos (`prompting/history.py`); el resto sirve para saber
# cuál fue el mensaje anterior del cliente y para el resumen de lo que pasó antes.
HISTORY_LIMIT = 40

# Cómo se llama cada dato en el JSON de la memoria. Son los nombres que ya tiene la base en producción.
LAST_INTENT, DETECTED_INTENT, PAYMENT_METHOD, PAYMENT_STATUS = "last_intent", "intent_detectado", "metodo_pago_elegido", "estado_pago"
LAST_PAIN, MODE, STAGE, LAST_RESPONSE = "last_pain", "mode", "stage", "last_ai_response"
CONVERSATION_STATE, OP_STATE = "conversation_state", "estado_operativo"
SUMMARY, SUMMARY_UNTIL = "resumen", "resumen_hasta"
LAST_USER_MESSAGE_AT, INITIAL_MESSAGE_SENT_AT = "last_user_message_at", "initial_message_last_sent_at"


def _key(tenant_slug: str, user_id: str) -> tuple[str, str] | None:
    slug, user = str(tenant_slug or "").strip().lower(), str(user_id or "").strip().lower()
    return (slug, user) if slug and user else None


def _lower(value: object) -> str:
    return str(value or "").strip().lower()


def _moment(value: object) -> datetime | None:
    try:
        moment = value if isinstance(value, datetime) else datetime.fromisoformat(str(value)) if value else None
    except ValueError:
        return None
    if moment is not None and moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


@dataclass
class _Turn:
    """La memoria de un cliente durante un turno: lo que se leyó al empezar y lo que se guardará al terminar."""

    ids: tuple[str, str] | None
    memory: dict
    history: list[dict] | None = None
    changed: dict = field(default_factory=dict)
    removed: set[str] = field(default_factory=set)
    messages: list[tuple[str, str, datetime]] = field(default_factory=list)

    def set(self, name: str, value: object) -> None:
        self.memory[name] = value
        self.changed[name] = value
        self.removed.discard(name)

    def remove(self, name: str) -> None:
        if name in self.memory or name in self.changed:
            self.memory.pop(name, None)
            self.changed.pop(name, None)
            self.removed.add(name)


class SQLMemoryRepository:
    """La memoria del motor en PostgreSQL (`MemoryRepositoryPort`). Ver las reglas arriba."""

    def __init__(self, *, engine: Engine | None = None) -> None:
        self._own_engine = engine
        # Los turnos abiertos de este repositorio en este hilo o tarea: cliente → su memoria del turno.
        self._turns: ContextVar[dict[tuple[str, str], _Turn] | None] = ContextVar(f"memoria_{id(self)}", default=None)

    def _engine(self) -> Engine:
        if self._own_engine is not None:
            return self._own_engine
        from app.infrastructure.db.connection import get_engine

        return get_engine()

    # ------------------------------------------------------------------------------------------------------------- el turno

    @contextmanager
    def turn(self, *, tenant_slug: str, user_id: str) -> Iterator[None]:
        """Atiende un mensaje de ese cliente: lee la memoria al empezar y la guarda una vez al terminar. Dentro de otro turno del mismo
        cliente, sigue en ese."""
        key = _key(tenant_slug, user_id)
        turns = self._turns.get() or {}
        if key is None or key in turns:
            yield
            return
        current = self._open(key)
        token = self._turns.set({**turns, key: current})
        try:
            yield
        finally:
            self._turns.reset(token)
            self._save(key, current)

    def _current(self, tenant_slug: str, user_id: str) -> tuple[tuple[str, str] | None, _Turn | None]:
        key = _key(tenant_slug, user_id)
        return key, (self._turns.get() or {}).get(key) if key else None

    @contextmanager
    def _using(self, tenant_slug: str, user_id: str) -> Iterator[_Turn | None]:
        """La memoria del turno abierto de ese cliente o, fuera de un turno, la de un turno solo para esta operación."""
        key, current = self._current(tenant_slug, user_id)
        if key is None:
            yield None
            return
        if current is not None:
            yield current
            return
        with self.turn(tenant_slug=tenant_slug, user_id=user_id):
            yield self._current(tenant_slug, user_id)[1]

    def _open(self, key: tuple[str, str]) -> _Turn:
        try:
            with self._engine().begin() as conn:
                ids = self._ids(conn, key)
                memory = self._read_memory(conn, ids) if ids else {}
            return _Turn(ids=ids, memory=memory)
        except Exception as exc:  # noqa: BLE001 - sin base, el turno sigue sin memoria
            self._unavailable("leer", key, exc)
            return _Turn(ids=None, memory={}, history=[])

    def _save(self, key: tuple[str, str], current: _Turn) -> None:
        if current.ids is None or not (current.changed or current.removed or current.messages):
            return
        tenant_id, client_id = current.ids
        try:
            with self._engine().begin() as conn:
                if current.messages:
                    conn.execute(
                        text("INSERT INTO conversation_messages (tenant_id, client_id, role, content, created_at) VALUES (:tid, :cid, :role, :content, :at)"),
                        [{"tid": tenant_id, "cid": client_id, "role": role, "content": content, "at": at} for role, content, at in current.messages],
                    )
                if current.changed or current.removed:
                    # Solo lo que cambió en este turno: lo que guardó otro mensaje a la vez se conserva.
                    conn.execute(
                        text(
                            "INSERT INTO conversation_memory (tenant_id, client_id, memory, updated_at) VALUES (:tid, :cid, CAST(:changed AS JSONB), now()) "
                            "ON CONFLICT (tenant_id, client_id) DO UPDATE SET memory = "
                            "(COALESCE(conversation_memory.memory, CAST('{}' AS JSONB)) - CAST(:removed AS TEXT[])) || CAST(:changed AS JSONB), updated_at = now()"
                        ),
                        {"tid": tenant_id, "cid": client_id, "changed": json.dumps(current.changed, default=str), "removed": sorted(current.removed)},
                    )
        except Exception as exc:  # noqa: BLE001 - el cliente ya recibió su respuesta; queda el aviso
            self._unavailable("guardar", key, exc)

    @staticmethod
    def _unavailable(operation: str, key: tuple[str, str], exc: Exception) -> None:
        # Solo el tipo de error: el texto de un error de base de datos puede traer datos de conexión.
        logger.error("memoria_no_disponible", extra={"operation": operation, "tenant": key[0], "error": type(exc).__name__})

    @staticmethod
    def _ids(conn, key: tuple[str, str]) -> tuple[str, str] | None:
        """El negocio y el registro del cliente (se crea la primera vez), en una sola consulta. None si el negocio no está en el motor."""
        row = conn.execute(
            text(
                "WITH t AS (SELECT id FROM tenants WHERE slug = :slug OR CAST(id AS TEXT) = :slug LIMIT 1) "
                "INSERT INTO clients (tenant_id, external_id) SELECT id, :ext FROM t "
                "ON CONFLICT (tenant_id, external_id) DO UPDATE SET external_id = EXCLUDED.external_id RETURNING tenant_id, id"
            ),
            {"slug": key[0], "ext": key[1]},
        ).first()
        if row is None:
            logger.warning("memoria_sin_negocio", extra={"tenant": key[0]})
            return None
        return str(row[0]), str(row[1])

    @staticmethod
    def _read_memory(conn, ids: tuple[str, str]) -> dict:
        raw = conn.execute(
            text("SELECT memory FROM conversation_memory WHERE tenant_id = :tid AND client_id = :cid"), {"tid": ids[0], "cid": ids[1]}
        ).scalar()
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                raw = {}
        return dict(raw) if isinstance(raw, dict) else {}

    def _history(self, current: _Turn, key: tuple[str, str]) -> list[dict]:
        """Los mensajes más recientes del cliente, del más antiguo al más nuevo. Se leen una vez por turno, la primera vez que se piden."""
        if current.history is None:
            current.history = []
            if current.ids is not None:
                try:
                    with self._engine().connect() as conn:
                        rows = conn.execute(
                            text(
                                "SELECT role, content, created_at FROM conversation_messages WHERE tenant_id = :tid AND client_id = :cid "
                                "ORDER BY created_at DESC LIMIT :limit"
                            ),
                            {"tid": current.ids[0], "cid": current.ids[1], "limit": HISTORY_LIMIT},
                        ).all()
                    current.history = [
                        {"role": _lower(row[0]) or "user", "text": str(row[1] or "").strip(), "at": _moment(row[2])}
                        for row in reversed(rows) if str(row[1] or "").strip()
                    ]
                except Exception as exc:  # noqa: BLE001
                    self._unavailable("leer_historial", key, exc)
        return current.history

    # ------------------------------------------------------------------------------------------------------------- los mensajes

    def save_message(self, *, tenant_slug: str, user_id: str, message_text: str, role: str = "user") -> None:
        content = str(message_text or "").strip()
        if not content:
            return
        with self._using(tenant_slug, user_id) as current:
            if current is None or current.ids is None:
                return
            key = _key(tenant_slug, user_id)
            history = self._history(current, key)
            # Su hora exacta, siempre después del mensaje anterior: el orden no depende de la transacción.
            at = datetime.now(timezone.utc)
            last = history[-1]["at"] if history and history[-1].get("at") else None
            if last is not None and at <= last:
                at = last + timedelta(microseconds=1)
            normalized_role = _lower(role) or "user"
            current.messages.append((normalized_role, content, at))
            history.append({"role": normalized_role, "text": content, "at": at})
            del history[:-HISTORY_LIMIT]

    def get_history(self, *, tenant_slug: str, user_id: str) -> list[dict[str, str]]:
        with self._using(tenant_slug, user_id) as current:
            if current is None:
                return []
            return [{"role": item["role"], "text": item["text"]} for item in self._history(current, _key(tenant_slug, user_id))]

    def get_history_entries(self, *, tenant_slug: str, user_id: str) -> list[dict]:
        """Los mensajes más recientes con su hora (`role`, `text`, `at`): para saber cuáles ya están en el resumen."""
        with self._using(tenant_slug, user_id) as current:
            if current is None:
                return []
            return [dict(item) for item in self._history(current, _key(tenant_slug, user_id))]

    def get_last_timestamp(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        with self._using(tenant_slug, user_id) as current:
            if current is None:
                return None
            history = self._history(current, _key(tenant_slug, user_id))
            return history[-1]["at"] if history else None

    # ------------------------------------------------------------------------------------------------------------- los datos

    def _get(self, tenant_slug: str, user_id: str, name: str, default: object = "") -> object:
        with self._using(tenant_slug, user_id) as current:
            return default if current is None else current.memory.get(name, default)

    def _set(self, tenant_slug: str, user_id: str, name: str, value: object) -> None:
        """Guarda el dato; con `None`, lo quita."""
        with self._using(tenant_slug, user_id) as current:
            if current is None or current.ids is None:
                return
            if value is None:
                current.remove(name)
            else:
                current.set(name, value)

    def set_last_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        self._set(tenant_slug, user_id, LAST_INTENT, _lower(intent))

    def get_last_intent(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, LAST_INTENT) or "")

    def set_detected_intent(self, *, tenant_slug: str, user_id: str, intent: str) -> None:
        self._set(tenant_slug, user_id, DETECTED_INTENT, _lower(intent) or None)

    def get_detected_intent(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, DETECTED_INTENT) or "")

    def set_payment_method(self, *, tenant_slug: str, user_id: str, method: str) -> None:
        self._set(tenant_slug, user_id, PAYMENT_METHOD, _lower(method) or None)

    def get_payment_method(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, PAYMENT_METHOD) or "")

    def set_payment_status(self, *, tenant_slug: str, user_id: str, status: str) -> None:
        self._set(tenant_slug, user_id, PAYMENT_STATUS, _lower(status) or None)

    def get_payment_status(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, PAYMENT_STATUS) or "")

    def set_last_pain(self, *, tenant_slug: str, user_id: str, pain: str) -> None:
        # Una necesidad vacía no borra la que ya contó el cliente.
        if _lower(pain):
            self._set(tenant_slug, user_id, LAST_PAIN, _lower(pain))

    def get_last_pain(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, LAST_PAIN) or "")

    def set_mode(self, *, tenant_slug: str, user_id: str, mode: str) -> None:
        self._set(tenant_slug, user_id, MODE, _lower(mode) or None)

    def get_mode(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, MODE) or "")

    def set_stage(self, *, tenant_slug: str, user_id: str, stage: str) -> None:
        self._set(tenant_slug, user_id, STAGE, _lower(stage))

    def get_stage(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, STAGE) or "")

    def set_last_response(self, *, tenant_slug: str, user_id: str, response: str) -> None:
        if str(response or "").strip():
            self._set(tenant_slug, user_id, LAST_RESPONSE, str(response).strip())

    def get_last_response(self, *, tenant_slug: str, user_id: str) -> str:
        return str(self._get(tenant_slug, user_id, LAST_RESPONSE) or "")

    def set_conversation_state(self, *, tenant_slug: str, user_id: str, state: ConversationState) -> None:
        timeline = getattr(state, "pain_timeline", None)
        self._set(tenant_slug, user_id, CONVERSATION_STATE, {
            "pain_detected": bool(getattr(state, "pain_detected", False)),
            "pain_timeline": [str(item).strip() for item in (timeline if isinstance(timeline, list) else []) if str(item).strip()][-20:],
            "urgency": _lower(getattr(state, "urgency", "")),
            "last_intent": _lower(getattr(state, "last_intent", "")),
            "stage": _lower(getattr(state, "stage", "")),
            "objections": max(0, int(getattr(state, "objections", 0) or 0)),
            "last_cta": str(getattr(state, "last_cta", "") or "").strip(),
        })

    def get_conversation_state(self, *, tenant_slug: str, user_id: str) -> ConversationState:
        raw = self._get(tenant_slug, user_id, CONVERSATION_STATE, {})
        raw = raw if isinstance(raw, dict) else {}
        timeline = raw.get("pain_timeline") if isinstance(raw.get("pain_timeline"), list) else []
        return ConversationState(
            pain_detected=bool(raw.get("pain_detected", False)),
            pain_timeline=[str(item).strip() for item in timeline if str(item).strip()],
            urgency=_lower(raw.get("urgency")),
            last_intent=_lower(raw.get("last_intent")),
            stage=_lower(raw.get("stage")),
            objections=max(0, int(raw.get("objections") or 0)),
            last_cta=str(raw.get("last_cta") or "").strip(),
        )

    def set_last_user_message_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        if isinstance(sent_at, datetime):
            self._set(tenant_slug, user_id, LAST_USER_MESSAGE_AT, _moment(sent_at).isoformat())

    def get_last_user_message_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        return _moment(self._get(tenant_slug, user_id, LAST_USER_MESSAGE_AT, None))

    def set_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str, sent_at: datetime) -> None:
        if isinstance(sent_at, datetime):
            self._set(tenant_slug, user_id, INITIAL_MESSAGE_SENT_AT, _moment(sent_at).isoformat())

    def get_initial_message_last_sent_at(self, *, tenant_slug: str, user_id: str) -> datetime | None:
        return _moment(self._get(tenant_slug, user_id, INITIAL_MESSAGE_SENT_AT, None))

    def set_summary(self, *, tenant_slug: str, user_id: str, summary: str, until: datetime) -> None:
        """El resumen de lo que pasó antes en la conversación y la hora del último mensaje que cubre."""
        if str(summary or "").strip() and isinstance(until, datetime):
            self._set(tenant_slug, user_id, SUMMARY, str(summary).strip())
            self._set(tenant_slug, user_id, SUMMARY_UNTIL, _moment(until).isoformat())

    def get_summary(self, *, tenant_slug: str, user_id: str) -> tuple[str, datetime | None]:
        return str(self._get(tenant_slug, user_id, SUMMARY) or ""), _moment(self._get(tenant_slug, user_id, SUMMARY_UNTIL, None))

    def set_op_state(self, *, tenant_slug: str, user_id: str, state_dict: dict) -> None:
        """El paso de la conversación (`OperationalState`). Uno vacío no borra el que hay: vence solo (`expires_at`)."""
        if isinstance(state_dict, dict) and state_dict.get("active_process"):
            self._set(tenant_slug, user_id, OP_STATE, dict(state_dict))

    def get_op_state(self, *, tenant_slug: str, user_id: str) -> dict:
        stored = self._get(tenant_slug, user_id, OP_STATE, {})
        return dict(stored) if isinstance(stored, dict) and stored.get("active_process") else {}

    # ------------------------------------------------------------------------------------------------------------- olvidar

    def reset_conversation(self, *, tenant_slug: str, user_id: str) -> None:
        """La conversación empieza de cero: sin mensajes ni memoria, pero el cliente sigue registrado."""
        key = _key(tenant_slug, user_id)
        if key is None:
            return
        try:
            with self._engine().begin() as conn:
                client = "SELECT c.id FROM clients c JOIN tenants t ON t.id = c.tenant_id WHERE (t.slug = :slug OR CAST(t.id AS TEXT) = :slug) AND c.external_id = :ext"
                conn.execute(text(f"DELETE FROM conversation_messages WHERE client_id IN ({client})"), {"slug": key[0], "ext": key[1]})
                conn.execute(text(f"UPDATE conversation_memory SET memory = CAST('{{}}' AS JSONB), updated_at = now() WHERE client_id IN ({client})"), {"slug": key[0], "ext": key[1]})
        except Exception as exc:  # noqa: BLE001
            self._unavailable("reiniciar", key, exc)

    def forget_contact(self, *, tenant_slug: str, user_id: str) -> None:
        """Borra todo lo que el motor guarda de ese cliente: sus mensajes, su memoria y su registro. Si falla, avisa (el panel debe
        saber que no pudo borrarlo)."""
        key = _key(tenant_slug, user_id)
        if key is not None:
            self._forget(key[0], "c.external_id = :ext", {"ext": key[1]})

    def forget_contacts_with_prefix(self, *, tenant_slug: str, prefix: str) -> None:
        """Borra a todos los contactos del negocio cuyo identificador empieza por `prefix` (las conversaciones de «Probar»,
        «prueba-<sesión>»). Si falla, avisa."""
        slug, start = _lower(tenant_slug), _lower(prefix)
        if slug and start:
            escaped = start.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            self._forget(slug, "c.external_id LIKE :pattern ESCAPE '\\'", {"pattern": f"{escaped}%"})

    def _forget(self, slug: str, condition: str, params: dict) -> None:
        clients = f"SELECT c.id FROM clients c JOIN tenants t ON t.id = c.tenant_id WHERE (t.slug = :slug OR CAST(t.id AS TEXT) = :slug) AND {condition}"
        values = {"slug": slug, **params}
        with self._engine().begin() as conn:
            ids = [row[0] for row in conn.execute(text(clients), values).all()]
            if ids:
                for table in ("conversation_messages", "conversation_memory"):
                    conn.execute(text(f"DELETE FROM {table} WHERE client_id = ANY(:ids)"), {"ids": ids})
                conn.execute(text("DELETE FROM clients WHERE id = ANY(:ids)"), {"ids": ids})

    def forget_business(self, *, tenant_slug: str) -> None:
        """Al eliminar un negocio, la base borra a sus clientes con él (`ON DELETE CASCADE`): aquí no queda nada en RAM que olvidar."""
        del tenant_slug
