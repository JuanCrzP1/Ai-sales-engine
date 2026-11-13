"""Las respuestas rápidas de cada negocio en la base (migración 0015, tabla `quick_replies`) y sus archivos (migración 0017,
`quick_reply_files`).

Cada operación recibe el negocio y solo alcanza sus filas: una respuesta (o un archivo) de otro negocio responde igual que una que no
existe. En `pieces`, un texto se guarda como cadena (como desde el principio) y un archivo como {"kind": "file", "file_id", "text"}.
Los archivos que ninguna respuesta usa se borran solos pasada una hora (el tiempo de subir uno y guardar la respuesta).
"""
from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, insert, select, true, update
from sqlalchemy.engine import Engine, Row
from sqlalchemy.exc import IntegrityError

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError, QuickReplyNotFoundError
from app.domain.business_config.conversations import MediaFile
from app.domain.business_config.quick_replies import MAX_QUICK_REPLIES, MAX_QUICK_REPLY_FILES, Piece, QuickReply, QuickReplyDraft, QuickReplyFile
from app.infrastructure.business_config.tables import quick_replies, quick_reply_files
from app.infrastructure.business_config.tenancy import tenant_of

_TAKEN = "Ya tienes una respuesta rápida con ese atajo. Usa otro."
_MISSING_FILE = "Ese archivo ya no está guardado: vuelve a subirlo."
# Lo que tarda, como mucho, alguien entre subir un archivo y guardar la respuesta: después, si nadie lo usa, se borra.
ORPHAN_AFTER = timedelta(hours=1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
    except ValueError:
        return False
    return True


def _key(reply_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(reply_id))
    except ValueError as exc:
        raise QuickReplyNotFoundError("respuesta rápida no válida") from exc


def _stored(draft: QuickReplyDraft) -> list:
    return [piece.text if piece.kind == "text" else {"kind": "file", "file_id": piece.file_id, "text": piece.text} for piece in draft.pieces]


def _file_ids(raw: Iterable) -> set[str]:
    return {str(item.get("file_id")) for item in raw or [] if isinstance(item, dict) and item.get("kind") == "file" and item.get("file_id")}


def _file(row: Row) -> QuickReplyFile:
    return QuickReplyFile(id=str(row.id), mime_type=row.mime_type, size_bytes=int(row.size_bytes), file_name=row.file_name)


def _reply(row: Row, files: dict[str, QuickReplyFile]) -> QuickReply:
    pieces: list[Piece] = []
    for item in row.pieces or []:
        if isinstance(item, str):
            pieces.append(Piece("text", item))
        elif isinstance(item, dict) and item.get("kind") == "file" and str(item.get("file_id")) in files:
            file_id = str(item["file_id"])
            pieces.append(Piece("file", str(item.get("text") or ""), file_id, files[file_id]))
    return QuickReply(
        id=str(row.id), shortcut=row.shortcut, category=row.category, pieces=tuple(pieces), use_count=int(row.use_count or 0),
        last_used_at=_utc(row.last_used_at), created_at=_utc(row.created_at), updated_at=_utc(row.updated_at),
    )


class QuickReplyStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------------------------------------------------ archivos

    def _files(self, conn, tenant_id, ids: set[str]) -> dict[str, QuickReplyFile]:
        keys = [uuid.UUID(value) for value in ids if _is_uuid(value)]
        if not keys:
            return {}
        query = select(quick_reply_files.c.id, quick_reply_files.c.mime_type, quick_reply_files.c.size_bytes, quick_reply_files.c.file_name).where(
            quick_reply_files.c.tenant_id == tenant_id, quick_reply_files.c.id.in_(keys)
        )
        return {str(row.id): _file(row) for row in conn.execute(query)}

    def _check_files(self, conn, tenant_id, draft: QuickReplyDraft) -> None:
        """Cada archivo de la respuesta debe estar guardado en este negocio."""
        known = self._files(conn, tenant_id, set(draft.file_ids))
        issues = [FieldIssue(f"pieces[{index}].file", _MISSING_FILE) for index, piece in enumerate(draft.pieces) if piece.file_id and piece.file_id not in known]
        if issues:
            raise InvalidFieldsError(_MISSING_FILE, issues)

    def _purge(self, conn, tenant_id) -> None:
        """Borra los archivos del negocio que ninguna respuesta usa y que se subieron hace más de una hora."""
        used: set[str] = set()
        for row in conn.execute(select(quick_replies.c.pieces).where(quick_replies.c.tenant_id == tenant_id)):
            used |= _file_ids(row.pieces)
        stale = (quick_reply_files.c.tenant_id == tenant_id) & (quick_reply_files.c.created_at < _now() - ORPHAN_AFTER)
        keep = [uuid.UUID(value) for value in used if _is_uuid(value)]
        conn.execute(delete(quick_reply_files).where(stale, quick_reply_files.c.id.not_in(keep) if keep else true()))

    def save_file(self, tenant_slug: str, media: MediaFile, *, created_by: str | None) -> QuickReplyFile:
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            self._purge(conn, tenant.id)
            count = conn.execute(select(func.count()).select_from(quick_reply_files).where(quick_reply_files.c.tenant_id == tenant.id)).scalar_one()
            if count >= MAX_QUICK_REPLY_FILES:
                full = f"Llegaste al máximo de {MAX_QUICK_REPLY_FILES} archivos en tus respuestas rápidas. Quita los que ya no uses."
                raise InvalidFieldsError(full, [FieldIssue("file", full)])
            file_id = uuid.uuid4()
            conn.execute(
                insert(quick_reply_files).values(
                    id=file_id, tenant_id=tenant.id, mime_type=media.mime_type, size_bytes=len(media.content), file_name=media.file_name,
                    content=media.content, created_by=created_by, created_at=_now(),
                )
            )
        return QuickReplyFile(id=str(file_id), mime_type=media.mime_type, size_bytes=len(media.content), file_name=media.file_name)

    def file(self, tenant_slug: str, file_id: str) -> MediaFile:
        """El archivo con su contenido, para verlo en el panel o enviarlo a un chat."""
        if not _is_uuid(file_id):
            raise QuickReplyNotFoundError("archivo no válido")
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            row = conn.execute(
                select(quick_reply_files).where(quick_reply_files.c.id == uuid.UUID(file_id), quick_reply_files.c.tenant_id == tenant.id)
            ).first()
        if row is None:
            raise QuickReplyNotFoundError("el archivo no existe")
        return MediaFile(row.mime_type, bytes(row.content), row.file_name)

    def _with_files(self, conn, tenant_id, rows) -> list[QuickReply]:
        ids: set[str] = set()
        for row in rows:
            ids |= _file_ids(row.pieces)
        files = self._files(conn, tenant_id, ids)
        return [_reply(row, files) for row in rows]

    # ------------------------------------------------------------------------------------------------------------ respuestas

    def list(self, tenant_slug: str) -> list[QuickReply]:
        """Todas las del negocio: las más usadas primero y, entre iguales, por atajo."""
        with self._engine.connect() as conn:
            tenant = tenant_of(conn, tenant_slug)
            rows = conn.execute(
                select(quick_replies)
                .where(quick_replies.c.tenant_id == tenant.id)
                .order_by(quick_replies.c.use_count.desc(), quick_replies.c.shortcut)
            ).all()
            return self._with_files(conn, tenant.id, rows)

    def create(self, tenant_slug: str, draft: QuickReplyDraft, *, created_by: str | None) -> QuickReply:
        now = _now()
        try:
            with self._engine.begin() as conn:
                tenant = tenant_of(conn, tenant_slug)
                count = conn.execute(select(func.count()).select_from(quick_replies).where(quick_replies.c.tenant_id == tenant.id)).scalar_one()
                if count >= MAX_QUICK_REPLIES:
                    full = f"Llegaste al máximo de {MAX_QUICK_REPLIES} respuestas rápidas. Borra las que ya no uses."
                    raise InvalidFieldsError(full, [FieldIssue("quick_replies", full)])
                self._check_files(conn, tenant.id, draft)
                reply_id = uuid.uuid4()
                conn.execute(
                    insert(quick_replies).values(
                        id=reply_id, tenant_id=tenant.id, shortcut=draft.shortcut, category=draft.category, pieces=_stored(draft),
                        use_count=0, created_by=created_by, created_at=now, updated_at=now,
                    )
                )
                row = conn.execute(select(quick_replies).where(quick_replies.c.id == reply_id)).one()
                return self._with_files(conn, tenant.id, [row])[0]
        except IntegrityError:
            raise InvalidFieldsError(_TAKEN, [FieldIssue("shortcut", _TAKEN)]) from None

    def update(self, tenant_slug: str, reply_id: str, draft: QuickReplyDraft) -> QuickReply:
        key = _key(reply_id)
        try:
            with self._engine.begin() as conn:
                tenant = tenant_of(conn, tenant_slug)
                mine = (quick_replies.c.id == key) & (quick_replies.c.tenant_id == tenant.id)
                self._check_files(conn, tenant.id, draft)
                result = conn.execute(
                    update(quick_replies).where(mine).values(
                        shortcut=draft.shortcut, category=draft.category, pieces=_stored(draft), updated_at=_now()
                    )
                )
                if result.rowcount == 0:
                    raise QuickReplyNotFoundError("la respuesta rápida no existe")
                row = conn.execute(select(quick_replies).where(mine)).one()
                self._purge(conn, tenant.id)
                return self._with_files(conn, tenant.id, [row])[0]
        except IntegrityError:
            raise InvalidFieldsError(_TAKEN, [FieldIssue("shortcut", _TAKEN)]) from None

    def delete(self, tenant_slug: str, reply_id: str) -> None:
        key = _key(reply_id)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            result = conn.execute(delete(quick_replies).where(quick_replies.c.id == key, quick_replies.c.tenant_id == tenant.id))
            self._purge(conn, tenant.id)
        if result.rowcount == 0:
            raise QuickReplyNotFoundError("la respuesta rápida no existe")

    def mark_used(self, tenant_slug: str, reply_id: str) -> QuickReply:
        """Suma un uso (en la base, sin leer antes: dos usos a la vez cuentan los dos)."""
        key = _key(reply_id)
        with self._engine.begin() as conn:
            tenant = tenant_of(conn, tenant_slug)
            mine = (quick_replies.c.id == key) & (quick_replies.c.tenant_id == tenant.id)
            result = conn.execute(update(quick_replies).where(mine).values(use_count=quick_replies.c.use_count + 1, last_used_at=_now()))
            if result.rowcount == 0:
                raise QuickReplyNotFoundError("la respuesta rápida no existe")
            row = conn.execute(select(quick_replies).where(mine)).one()
            return self._with_files(conn, tenant.id, [row])[0]
