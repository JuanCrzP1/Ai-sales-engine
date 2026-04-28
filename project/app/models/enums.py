import enum


class LeadStatus(str, enum.Enum):
    frio = "frio"
    interesado = "interesado"
    caliente = "caliente"


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"
