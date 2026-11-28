"""Los campos del cliente en la base: el catálogo de cada negocio y el valor de cada campo en cada cliente.

`CommerceStore` lo expone (`customer_fields`, `create_customer_field`, `update_customer_field`, `delete_customer_field`,
`set_customer_field_values`); aquí están sus consultas, y la que usa la ficha (`fields_of_customer`). Cada una recibe el negocio y
solo alcanza sus filas: un campo o un cliente de otro negocio no existen.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.customer_fields import (
    CHOICE,
    MAX_FIELDS,
    CustomerField,
    FieldChange,
    FieldError,
    FieldValue,
    FieldValues,
    NewField,
    checked_value,
)
from app.domain.business_config.customer_labels import label_key
from app.domain.business_config.errors import ConversationNotFoundError
from app.infrastructure.business_config.commerce_queries import real_customers, utc
from app.infrastructure.business_config.tables import conversations, customer_field_values, customer_fields
from app.infrastructure.business_config.tenancy import tenant_of


class FieldNotFoundError(ConversationNotFoundError):
    """El campo no existe o es de otro negocio (la API responde como con un cliente que no existe)."""


def _key(value: str, error: type[Exception], what: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise error(f"{what} no existe") from exc


def _field(row: Any, filled: int = 0) -> CustomerField:
    return CustomerField(
        id=str(row.id), name=row.name, kind=row.kind, options=tuple(row.options or ()), filled=filled, created_at=utc(row.created_at),
    )


def _catalog(conn: Connection, tenant_id: Any) -> list[Any]:
    """Los campos del negocio en el orden en que se crearon (así se ven en la ficha)."""
    return conn.execute(
        select(customer_fields).where(customer_fields.c.tenant_id == tenant_id).order_by(customer_fields.c.created_at, customer_fields.c.name_key)
    ).all()


def _mine(conn: Connection, tenant_id: Any, field_id: str) -> Any:
    key = _key(field_id, FieldNotFoundError, "ese campo")
    row = conn.execute(select(customer_fields).where(customer_fields.c.id == key, customer_fields.c.tenant_id == tenant_id)).first()
    if row is None:
        raise FieldNotFoundError("ese campo no existe o es de otro negocio")
    return row


def _taken(conn: Connection, tenant_id: Any, name: str, *, except_id: Any = None) -> bool:
    query = select(customer_fields.c.id).where(customer_fields.c.tenant_id == tenant_id, customer_fields.c.name_key == label_key(name))
    if except_id is not None:
        query = query.where(customer_fields.c.id != except_id)
    return conn.execute(query).first() is not None


def _filled(conn: Connection, tenant_id: Any) -> dict[Any, int]:
    """Cuántos clientes (de canales reales) tienen lleno cada campo."""
    return dict(
        conn.execute(
            select(customer_field_values.c.field_id, func.count())
            .join(conversations, conversations.c.id == customer_field_values.c.conversation_id)
            .where(*real_customers(tenant_id))
            .group_by(customer_field_values.c.field_id)
        ).all()
    )


def list_fields(engine: Engine, tenant_slug: str) -> list[CustomerField]:
    with engine.connect() as conn:
        tenant = tenant_of(conn, tenant_slug)
        filled = _filled(conn, tenant.id)
        return [_field(row, int(filled.get(row.id, 0))) for row in _catalog(conn, tenant.id)]


def create_field(engine: Engine, tenant_slug: str, new: NewField, *, created_by: str | None = None) -> CustomerField:
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        total = conn.execute(select(func.count()).select_from(customer_fields).where(customer_fields.c.tenant_id == tenant.id)).scalar_one()
        if total >= MAX_FIELDS:
            raise FieldError("name", f"Ya tienes {MAX_FIELDS} campos: borra alguno antes de crear otro.")
        if _taken(conn, tenant.id, new.name):
            raise FieldError("name", "Ya tienes un campo con ese nombre.")
        field_id = uuid.uuid4()
        conn.execute(
            insert(customer_fields).values(
                id=field_id, tenant_id=tenant.id, name=new.name, name_key=label_key(new.name), kind=new.kind, options=list(new.options),
                created_by=created_by, created_at=datetime.now(timezone.utc),
            )
        )
        return _field(conn.execute(select(customer_fields).where(customer_fields.c.id == field_id)).one())


def update_field(engine: Engine, tenant_slug: str, field_id: str, change: FieldChange) -> CustomerField:
    """Cambia el nombre y/o las opciones. Si una opción se quita, los clientes que la tenían quedan sin valor en ese campo."""
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        row = _mine(conn, tenant.id, field_id)
        values: dict[str, Any] = {}
        if change.name is not None:
            if _taken(conn, tenant.id, change.name, except_id=row.id):
                raise FieldError("name", "Ya tienes un campo con ese nombre.")
            values.update(name=change.name, name_key=label_key(change.name))
        if change.options is not None:
            if row.kind != CHOICE:
                raise FieldError("options", "Solo una lista tiene opciones.")
            values["options"] = list(change.options)
            renamed = {label_key(option): option for option in change.options}
            for value_row in conn.execute(select(customer_field_values).where(customer_field_values.c.field_id == row.id)).all():
                kept = renamed.get(label_key(value_row.value))
                where = (customer_field_values.c.field_id == row.id, customer_field_values.c.conversation_id == value_row.conversation_id)
                if kept is None:
                    conn.execute(delete(customer_field_values).where(*where))
                elif kept != value_row.value:
                    # La misma opción escrita de otra forma («vip» → «VIP»): el valor sigue, con la forma nueva.
                    conn.execute(update(customer_field_values).where(*where).values(value=kept))
        conn.execute(update(customer_fields).where(customer_fields.c.id == row.id).values(**values))
        return _field(conn.execute(select(customer_fields).where(customer_fields.c.id == row.id)).one(), _filled(conn, tenant.id).get(row.id, 0))


def delete_field(engine: Engine, tenant_slug: str, field_id: str) -> None:
    """Borra el campo y su valor en todos los clientes."""
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        row = _mine(conn, tenant.id, field_id)
        conn.execute(delete(customer_field_values).where(customer_field_values.c.field_id == row.id))
        conn.execute(delete(customer_fields).where(customer_fields.c.id == row.id))


def fields_of_customer(conn: Connection, tenant_id: Any, conversation_id: Any) -> list[FieldValue]:
    """Todos los campos del negocio con el valor de este cliente (o vacío), para su ficha."""
    filled = {
        row.field_id: row
        for row in conn.execute(select(customer_field_values).where(customer_field_values.c.conversation_id == conversation_id)).all()
    }
    found: list[FieldValue] = []
    for row in _catalog(conn, tenant_id):
        value = filled.get(row.id)
        found.append(
            FieldValue(
                field=_field(row), value=value.value if value else None, updated_by=value.updated_by if value else None,
                updated_at=utc(value.updated_at) if value else None,
            )
        )
    return found


def set_field_values(engine: Engine, tenant_slug: str, conversation_id: str, changes: FieldValues, *, by: str | None) -> list[FieldValue]:
    """Cambia solo los campos que llegan (None o en blanco lo deja vacío), todos o ninguno. Un valor igual al que tenía no cambia
    quién lo puso ni cuándo."""
    key = _key(conversation_id, ConversationNotFoundError, "ese cliente")
    for attempt in range(2):
        try:
            return _set_values(engine, tenant_slug, key, changes, by=by)
        except IntegrityError:
            # Dos personas llenaron el mismo campo vacío a la vez: el segundo intento encuentra el valor y lo cambia.
            if attempt:
                raise
    raise AssertionError("inalcanzable")


def _set_values(engine: Engine, tenant_slug: str, key: uuid.UUID, changes: FieldValues, *, by: str | None) -> list[FieldValue]:
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        tenant = tenant_of(conn, tenant_slug)
        if conn.execute(select(conversations.c.id).where(conversations.c.id == key, *real_customers(tenant.id))).first() is None:
            raise ConversationNotFoundError("ese cliente no existe o es de otro negocio")
        catalog = {str(row.id): row for row in _catalog(conn, tenant.id)}
        current = {
            str(row.field_id): row.value
            for row in conn.execute(select(customer_field_values).where(customer_field_values.c.conversation_id == key)).all()
        }
        checked: dict[str, str | None] = {}
        for field_id, raw in changes.values.items():
            row = catalog.get(field_id)
            if row is None:
                raise FieldError(f"values.{field_id}", "Ese campo ya no existe: vuelve a abrir la ficha.")
            checked[field_id] = checked_value(_field(row), raw)
        for field_id, value in checked.items():
            if value == current.get(field_id):
                continue
            where = (customer_field_values.c.conversation_id == key, customer_field_values.c.field_id == catalog[field_id].id)
            if value is None:
                conn.execute(delete(customer_field_values).where(*where))
            elif field_id in current:
                conn.execute(update(customer_field_values).where(*where).values(value=value, updated_by=by, updated_at=now))
            else:
                conn.execute(
                    insert(customer_field_values).values(
                        conversation_id=key, field_id=catalog[field_id].id, tenant_id=tenant.id, value=value, updated_by=by, updated_at=now,
                    )
                )
        return fields_of_customer(conn, tenant.id, key)
