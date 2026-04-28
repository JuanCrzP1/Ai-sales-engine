from __future__ import annotations

import json
import os
from pathlib import Path
import time
from urllib import error, request

from dotenv import load_dotenv

from app.connectors.tenant_guard import resolve_connector_tenant
from app.connectors.telegram.telegram_service import TelegramService


def _load_env_files() -> None:
    project_dir = Path(__file__).resolve().parents[3]
    workspace_root = project_dir.parent
    for candidate in (workspace_root / ".env", project_dir / ".env"):
        if candidate.exists():
            load_dotenv(dotenv_path=candidate, override=False)


def _resolve_token() -> str:
    token = str(os.getenv("TELEGRAM_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN is required to run telegram polling")
    return token


def _telegram_api(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with request.urlopen(req, timeout=60) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def _extract_message(update_payload: dict) -> tuple[str, str, str] | None:
    message = update_payload.get("message") if isinstance(update_payload.get("message"), dict) else None
    if not message:
        return None
    text = str(message.get("text") or "").strip()
    if not text:
        return None
    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    sender = message.get("from") if isinstance(message.get("from"), dict) else {}
    chat_id = str(chat.get("id") or "").strip()
    user_id = str(sender.get("id") or chat_id or "telegram-user").strip()
    if not chat_id:
        return
    return chat_id, text, user_id


def _send_message(token: str, chat_id: str, text: str) -> None:
    _telegram_api(
        token,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": str(text or ""),
        },
    )


def main() -> None:
    _load_env_files()
    token = _resolve_token()
    tenant_slug = resolve_connector_tenant(os.getenv("TENANT_SLUG"))

    service = TelegramService(tenant_slug=tenant_slug)
    offset = 0

    print("Telegram polling started.")
    while True:
        try:
            updates = _telegram_api(
                token,
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 30,
                    "allowed_updates": ["message"],
                },
            )
            results = updates.get("result") if isinstance(updates.get("result"), list) else []
            for update_payload in results:
                update_id = int(update_payload.get("update_id") or 0)
                if update_id >= offset:
                    offset = update_id + 1

                parsed = _extract_message(update_payload)
                if not parsed:
                    continue
                chat_id, text, user_id = parsed

                if text.startswith("/start"):
                    reply = "Bot activo. Escribeme y te respondo por el mismo flujo de produccion."
                else:
                    reply = service.handle_message(text, user_id)

                _send_message(token, chat_id, reply)
        except KeyboardInterrupt:
            print("Telegram polling stopped.")
            break
        except error.URLError as exc:
            print(f"Telegram connection error: {exc}")
            time.sleep(2)
        except Exception as exc:
            print(f"Telegram polling error: {exc}")
            time.sleep(2)


if __name__ == "__main__":
    main()
