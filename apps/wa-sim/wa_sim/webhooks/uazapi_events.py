"""Lo que pasa en el simulador, en el formato de los avisos de uazapi (`connection`, `messages`, `messages_update`), tal como los lee
el motor (`project/app/infrastructure/channels/uazapi.py`). Si uazapi cambia su formato, se ajustan juntos este archivo y los
lectores del motor: lo vigila `tests/test_wa_simulator_contract.py`.
"""
from __future__ import annotations

from wa_sim.core.models import DELIVERED, Instance, Message
from wa_sim.webhooks.qr import QR_DATA

# El tipo de mensaje de WhatsApp de cada cosa que se puede enviar.
_MESSAGE_TYPES = {
    "text": "Conversation",
    "image": "ImageMessage",
    "audio": "AudioMessage",
    "ptt": "AudioMessage",
    "video": "VideoMessage",
    "document": "DocumentMessage",
    "sticker": "StickerMessage",
    "location": "LocationMessage",
}


def jid(phone: str) -> str:
    return f"{phone}@s.whatsapp.net"


def instance_status(instance: Instance) -> dict:
    """Lo que responde `/instance/status` y lo que trae el aviso `connection`."""
    connected = instance.status == "connected"
    return {
        "instance": {
            "status": instance.status,
            "qrcode": QR_DATA if instance.status == "connecting" else "",
            "paircode": "SIMU-LADO" if instance.status == "connecting" else "",
            "profileName": instance.profile_name if connected else "",
            "name": instance.name,
        },
        "status": {"connected": connected, "loggedIn": connected, "jid": {"user": instance.phone} if connected else None},
    }


def connection_event(instance: Instance) -> dict:
    return {"EventType": "connection", "token": instance.token, **instance_status(instance)}


def message_event(instance: Instance, message: Message, sender_name: str) -> dict:
    """Un mensaje que llega al negocio: del cliente, o del propio negocio escrito desde su celular (`fromMe`)."""
    from_me = message.author == "phone"
    content: dict = {}
    if message.media is not None:
        content = {"mimetype": message.media.mime_type, "fileName": message.media.file_name, "caption": message.text}
    elif message.text:
        content = {"text": message.text}
    message_type = _MESSAGE_TYPES.get(message.kind, "Conversation")
    if message.kind == "audio":
        message_type = "AudioMessage (ptt)"  # nota de voz
    return {
        "EventType": "messages",
        "token": instance.token,
        "message": {
            "messageid": message.id,
            "id": message.id,
            "chatid": jid(message.phone),
            "sender": jid(instance.phone if from_me else message.phone),
            "senderName": "" if from_me else sender_name,
            "fromMe": from_me,
            "wasSentByApi": False,
            "isGroup": False,
            "messageType": message_type,
            "text": message.text,
            "content": content,
            "mimetype": message.media.mime_type if message.media else "",
            "messageTimestamp": int(message.at * 1000),
        },
    }


def receipt_event(instance: Instance, message_ids: list[str], status: str, phone: str) -> dict:
    """El ✓✓ (entregado) o el azul (leído) de lo que envió el negocio."""
    state = "Delivered" if status == DELIVERED else "Read"
    return {
        "EventType": "messages_update",
        "token": instance.token,
        "state": state,
        "event": {"Chat": jid(phone), "chatid": jid(phone), "IsGroup": False, "MessageIDs": list(message_ids), "Type": state},
    }
