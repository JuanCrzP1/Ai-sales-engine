"""Las etiquetas de los clientes en la base: el catálogo de cada negocio y las que lleva cada cliente.

`CommerceStore` lo expone (`labels`, `create_label`, `update_label`, `delete_label`, `set_customer_labels`); aquí están sus
consultas. Cada una recibe el negocio y solo alcanza sus filas: una etiqueta o un cliente de otro negocio no existen.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine

from app.domain.business_config.commerce import Customer
from app.domain.business_config.customer_labels import MAX_LABELS, Label, LabelChange, LabelError, label_key
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.commerce_queries import customers_of, real_customers, utc
from app.infrastructure.business_config.tables import conversation_labels, conversations, customer_labels
from app.infrastructure.business_config.tenancy import tenant_of


class LabelNotFoundError(ConversationNotFoundError):
    """La etiqueta no existe o es de otro negocio (la API responde como con un cliente que no existe)."""


def _key(value: str, error: type[Exception], what: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise error(f"{what} no existe") from exc


def _label(row: Any, customers: int = 0) -> Label:
    return Label(id=str(row.id), name=row.name, color=row.color, customers=customers, created_at=utc(row.created_at))


def _mine(conn: Connection, tenant_id: Any, label_id: str) -> Any:
    key = _key(label_id, LabelNotFoundError, "esa etiqueta")
    row = conn.execute(select(customer_labels).where(customer_labels.c.id == key, customer_labels.c.tenant_id == tenant_id)).first()
    if row is None:
        raise LabelNotFoundError("esa etiqueta no existe o es de otro negocio")
    return row


def _taken(conn: Connection, tenant_id: Any, name: str, *, except_id: Any = None) -> bool:
    """Si ya hay otra etiqueta que se lee igual en ese negocio."""
    query = select(customer_labels.c.id).where(customer_labels.c.tenant_id == tenant_id, customer_labels.c.name_key == label_key(name))
    if except_id is not None:
        query = query.where(customer_labels.c.id != except_id)
    return conn.execute(query).first() is not None


def list_labels(engine: Engine, tenant_slug: str) -> list[Label]:
    """El catálogo, por nombre, con cuántos clientes (de canales reales) llevan cada etiqueta."""
    with engine.connect() as conn:
        tenant = tenant_of(conn, tenant_slug)
        counts = dict(
            conn.execute(
                select(conversation_labels.c.label_id, func.count())
                .join(conversations, conversations.c.id == conversation_labels.c.conversation_id)
                .where(*real_customers(tenant.id))
                .group_by(conversation_labels.c.label_id)
            ).all()
        )
        rows = conn.execute(select(customer_labels).where(customer_labels.c.tenant_id == tenant.id).order_by(customer_labels.c.name_key)).all()
        return [_label(row, int(counts.get(row.id, 0))) for row in rows]


def create_label(engine: Engine, tenant_slug: str, name: str, color: str, *, created_by: str | None = None) -> Label:
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        total = conn.execute(select(func.count()).select_from(customer_labels).where(customer_labels.c.tenant_id == tenant.id)).scalar_one()
        if total >= MAX_LABELS:
            raise LabelError("name", f"Ya tienes {MAX_LABELS} etiquetas: borra alguna antes de crear otra.")
        if _taken(conn, tenant.id, name):
            raise LabelError("name", "Ya tienes una etiqueta con ese nombre.")
        label_id = uuid.uuid4()
        conn.execute(
            insert(customer_labels).values(
                id=label_id, tenant_id=tenant.id, name=name, name_key=label_key(name), color=color, created_by=created_by,
                created_at=datetime.now(timezone.utc),
            )
        )
        return _label(conn.execute(select(customer_labels).where(customer_labels.c.id == label_id)).one())


def update_label(engine: Engine, tenant_slug: str, label_id: str, change: LabelChange) -> Label:
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        row = _mine(conn, tenant.id, label_id)
        values: dict[str, Any] = {}
        if change.name is not None:
            if _taken(conn, tenant.id, change.name, except_id=row.id):
                raise LabelError("name", "Ya tienes una etiqueta con ese nombre.")
            values.update(name=change.name, name_key=label_key(change.name))
        if change.color is not None:
            values["color"] = change.color
        conn.execute(update(customer_labels).where(customer_labels.c.id == row.id).values(**values))
        customers = conn.execute(select(func.count()).select_from(conversation_labels).where(conversation_labels.c.label_id == row.id)).scalar_one()
        return _label(conn.execute(select(customer_labels).where(customer_labels.c.id == row.id)).one(), int(customers))


def delete_label(engine: Engine, tenant_slug: str, label_id: str) -> None:
    """Borra la etiqueta: sus clientes solo la pierden."""
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        row = _mine(conn, tenant.id, label_id)
        conn.execute(delete(conversation_labels).where(conversation_labels.c.label_id == row.id))
        conn.execute(delete(customer_labels).where(customer_labels.c.id == row.id))


def set_customer_labels(engine: Engine, tenant_slug: str, conversation_id: str, label_ids: list[str]) -> Customer:
    """Deja al cliente exactamente con esas etiquetas (todas de su negocio)."""
    key = _key(conversation_id, ConversationNotFoundError, "ese cliente")
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        row = conn.execute(select(conversations).where(conversations.c.id == key, *real_customers(tenant.id))).first()
        if row is None:
            raise ConversationNotFoundError("ese cliente no existe o es de otro negocio")
        wanted = [_mine(conn, tenant.id, label_id).id for label_id in label_ids]
        conn.execute(delete(conversation_labels).where(conversation_labels.c.conversation_id == key))
        for label_id in wanted:
            conn.execute(insert(conversation_labels).values(conversation_id=key, label_id=label_id, tenant_id=tenant.id, created_at=now))
        return customers_of(conn, [row])[0]
