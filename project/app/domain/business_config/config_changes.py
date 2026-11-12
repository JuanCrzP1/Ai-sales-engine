"""Lo que cambia al publicar: la diferencia entre lo publicado (lo que responde hoy a los clientes) y la versión que se va a publicar.

Compara contenido, no números de versión. Las listas de elementos se emparejan por su id (o su pregunta, su nombre...) para decir
qué se agregó, se quitó o cambió. Un dato de pago se informa como «protegido»: nunca su valor ni su referencia. El panel tiene la
misma comparación para la pantalla (`apps/admin-web/src/domain/config/publishChanges.ts`); esta es la del servidor MCP.

Todo aquí es puro.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

ChangeKind = Literal["added", "removed", "changed"]
MAX_TEXT = 120
_IGNORED_ROOTS = {"schema_version", "tenant_slug"}
_TITLE_KEYS = ("name", "question", "topic", "title", "label", "motivation", "when", "text", "bank", "type", "id")
_MATCH_KEYS = ("id", "question", "name", "topic")


@dataclass(frozen=True)
class ConfigChange:
    path: str
    kind: ChangeKind
    before: str | None
    after: str | None
    protected: bool = False


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return any(_present(item) for item in (value.values() if isinstance(value, dict) else value))
    return True


def _canonical(value: Any) -> str:
    def clean(node: Any) -> Any:
        if isinstance(node, dict):
            return {key: clean(item) for key, item in sorted(node.items()) if _present(item)}
        if isinstance(node, list):
            return [clean(item) for item in node]
        return node if _present(node) else None

    return json.dumps(clean(value), ensure_ascii=False, sort_keys=True)


def _short(value: Any) -> str | None:
    if not _present(value):
        return None
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, (int, float, str)):
        text = " ".join(str(value).split())
        return text if len(text) <= MAX_TEXT else f"{text[: MAX_TEXT - 1]}…"
    if isinstance(value, list) and all(not isinstance(item, (dict, list)) for item in value):
        return _short(", ".join(str(item) for item in value))
    if isinstance(value, dict):
        title = _title(value)
        if title:
            return title
    return f"{len(value)} elementos" if isinstance(value, list) else "(objeto)"


def _title(item: Any) -> str | None:
    if isinstance(item, dict):
        for key in _TITLE_KEYS:
            if isinstance(item.get(key), str) and item[key].strip():
                return _short(item[key])
    return None


def _key(item: Any, index: int) -> str:
    if isinstance(item, dict):
        for key in _MATCH_KEYS:
            if isinstance(item.get(key), str) and item[key].strip():
                return f"{key}:{item[key].strip().lower()}"
    return f"#{index}"


def _secret(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("secret_ref"), str)


def config_changes(published: dict[str, Any] | None, draft: dict[str, Any]) -> list[ConfigChange]:
    """Los cambios de `draft` frente a `published`. Sin nada publicado, [] (todo es nuevo)."""
    if published is None:
        return []
    changes: list[ConfigChange] = []

    def push(path: str, before: Any, after: Any) -> None:
        kind: ChangeKind = "changed" if _present(before) and _present(after) else "added" if _present(after) else "removed"
        protected = _secret(before) or _secret(after)
        changes.append(ConfigChange(path, kind, None if protected else _short(before), None if protected else _short(after), protected))

    def walk(before: Any, after: Any, path: str) -> None:
        if _canonical(before) == _canonical(after):
            return
        if _secret(before) or _secret(after):
            push(path, before, after)
            return
        if isinstance(before, dict) or isinstance(after, dict):
            if (before is not None and not isinstance(before, dict)) or (after is not None and not isinstance(after, dict)):
                push(path, before, after)
                return
            a, b = before or {}, after or {}
            for key in list(dict.fromkeys([*b.keys(), *a.keys()])):
                if not path and key in _IGNORED_ROOTS:
                    continue
                walk(a.get(key), b.get(key), f"{path}.{key}" if path else key)
            return
        if isinstance(before, list) or isinstance(after, list):
            items = [*(before or []), *(after or [])]
            if not any(isinstance(item, dict) for item in items):
                push(path, before, after)
                return
            old = {_key(item, index): item for index, item in enumerate(before or [])}
            new = {_key(item, index): item for index, item in enumerate(after or [])}
            for key, item in new.items():
                label = f"{path}[{_title(item) or key}]"
                if key not in old:
                    push(label, None, item)
                else:
                    walk(old[key], item, label)
            for key, item in old.items():
                if key not in new:
                    push(f"{path}[{_title(item) or key}]", item, None)
            return
        push(path, before, after)

    walk(published, draft, "")
    return changes
