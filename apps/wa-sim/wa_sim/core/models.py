"""El estado del WhatsApp falso: números del negocio (instancias de uazapi), clientes de prueba y mensajes. Solo datos."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

# Lo que salió del negocio: enviado (✓), entregado (✓✓) y leído (azul).
SENT, DELIVERED, READ = "sent", "delivered", "read"


@dataclass
class Instance:
    """Un número del negocio, como una instancia de uazapi: su token, su estado y adónde avisa."""

    token: str
    name: str
    status: str = "disconnected"  # disconnected | connecting | connected
    phone: str = ""
    profile_name: str = ""
    webhook_url: str = ""
    events: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass
class Client:
    """Un cliente de prueba: alguien que le escribe al negocio desde «su» WhatsApp."""

    phone: str
    name: str


@dataclass
class Media:
    mime_type: str
    base64: str
    file_name: str = ""


@dataclass
class Message:
    """Un mensaje del chat entre un número del negocio y un cliente."""

    id: str
    instance: str
    phone: str
    # customer: lo escribió el cliente; business: lo envió el sistema (la API); phone: el negocio desde su celular.
    author: str
    kind: str
    text: str = ""
    media: Media | None = None
    status: str = SENT
    at: float = 0.0


@dataclass
class State:
    instances: dict[str, Instance] = field(default_factory=dict)
    clients: dict[str, Client] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    # «Escribiendo…» por chat (instancia:teléfono) hasta esa hora.
    typing: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(raw: dict) -> "State":
        def message(item: dict) -> Message:
            media = item.get("media")
            return Message(**{**item, "media": Media(**media) if media else None})

        return State(
            instances={key: Instance(**value) for key, value in (raw.get("instances") or {}).items()},
            clients={key: Client(**value) for key, value in (raw.get("clients") or {}).items()},
            messages=[message(item) for item in raw.get("messages") or []],
            typing=dict(raw.get("typing") or {}),
        )
