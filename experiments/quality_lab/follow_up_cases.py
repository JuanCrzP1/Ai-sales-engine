"""Los casos del lector del seguimiento: finales de conversación y si conviene escribirle al cliente que dejó de responder.

Equivocarse hacia «enviar» es lo grave: le llega «¿seguimos?» a quien dijo que no le interesa o que ya compró en otro lado (así se ve
como spam). Equivocarse hacia «no enviar» es leve: ese cliente no recibe el seguimiento y el equipo lo puede reanudar.
`run_follow_up_eval.py` corre estos casos con la IA real.
"""
from __future__ import annotations

from dataclasses import dataclass

C, N = "customer", "assistant"
SEGUIMIENTO = "Hola de nuevo 👋 ¿Seguimos con lo que estabas viendo? Cuando quieras te ayudo a terminar."


@dataclass(frozen=True)
class FollowUpCase:
    messages: tuple[tuple[str, str], ...]
    send: bool
    note: str
    message: str = SEGUIMIENTO


CASES = (
    # Dejó la conversación abierta: conviene escribirle.
    FollowUpCase(((C, "¿Cuánto vale el plan Pro?"), (N, "El plan Pro vale $210.000 al mes e incluye WhatsApp y reportes.")), True, "preguntó el precio y no respondió"),
    FollowUpCase(((C, "Hola, quiero información"), (N, "¡Claro! ¿Qué te gustaría saber: precios, cómo funciona o tiempos?")), True, "pidió información"),
    FollowUpCase(((C, "Me interesa, déjame lo pienso"), (N, "¡Con gusto! Aquí estoy cuando quieras.")), True, "lo va a pensar"),
    FollowUpCase(((C, "Lo hablo con mi socio y te cuento"), (N, "Perfecto, quedo atento.")), True, "lo consulta"),
    FollowUpCase(((C, "Quiero 2 hamburguesas"), (N, "¡Listo! ¿Me compartes la dirección para el domicilio?")), True, "pedido a mitad de camino"),
    FollowUpCase(((C, "¿Tienen la talla M en negro?"), (N, "Sí, la tenemos. ¿Te la separo?")), True, "le ofrecieron separarla"),
    FollowUpCase(((C, "Voy a pagar ahorita"), (N, "Perfecto, cuando pagues envíame el comprobante.")), True, "iba a pagar"),
    FollowUpCase(((C, "ok"), (N, "¿Quieres que te envíe los datos para pagar?")), True, "dijo ok y no siguió"),
    FollowUpCase(((C, "Mañana te escribo"), (N, "¡Claro! Aquí estaré.")), True, "escribe después"),
    FollowUpCase(((C, "¿Hacen envíos a Medellín?"), (N, "Sí, el envío a Medellín tarda 2 días. ¿Te ayudo con el pedido?")), True, "preguntó por envío"),
    FollowUpCase(((C, "está un poco caro"), (N, "Entiendo. Tenemos el plan Básico por $120.000. ¿Te cuento qué incluye?")), True, "objeción de precio, sigue abierta"),
    FollowUpCase(((C, "¿Me agendas una cita?"), (N, "¡Claro! ¿Qué día te queda mejor?")), True, "cita a mitad de camino"),
    FollowUpCase(((C, "Gracias, lo reviso"), (N, "¡Con gusto! Cualquier duda me escribes.")), True, "lo revisa"),
    FollowUpCase(((N, "¡Hola! ¿En qué te puedo ayudar?"),), True, "nunca respondió al saludo"),
    FollowUpCase(((C, "suena bien"), (N, "¡Genial! ¿Empezamos con el plan Básico o el Pro?")), True, "le gustó"),
    # La cerró: no conviene escribirle.
    FollowUpCase(((C, "¿Cuánto vale?"), (N, "Vale $210.000."), (C, "No gracias, no me interesa")), False, "no le interesa"),
    FollowUpCase(((C, "¿Tienen domicilio?"), (N, "Sí."), (C, "Ya compré en otro lado, gracias")), False, "compró en otro lado"),
    FollowUpCase(((C, "Por favor no me escriban más"),), False, "que no le escriban"),
    FollowUpCase(((C, "¿A qué hora abren?"), (N, "Abrimos a las 8 a. m."), (C, "Perfecto, gracias, era solo eso")), False, "resuelto y se despidió"),
    FollowUpCase(((C, "Muy mal servicio, el pedido llegó frío"), (N, "Lo siento mucho, lo reviso con el equipo.")), False, "reclamo"),
    FollowUpCase(((C, "Muy caro, no gracias"), (N, "Entiendo, aquí estaremos si cambias de opinión.")), False, "no por precio"),
    FollowUpCase(((C, "Ya lo resolví, gracias"), (N, "¡Qué bien! Aquí estamos para lo que necesites.")), False, "ya lo resolvió"),
    FollowUpCase(((C, "Me equivoqué de número"), (N, "No hay problema, ¡que estés bien!")), False, "número equivocado"),
    FollowUpCase(((C, "No estoy interesado, quiten mi número"),), False, "que lo quiten"),
    FollowUpCase(((C, "Ya no lo necesito"), (N, "Entendido, gracias por avisar.")), False, "ya no lo necesita"),
    FollowUpCase(((C, "¿Venden repuestos de moto?"), (N, "No, solo vendemos ropa."), (C, "Ah ok, gracias")), False, "no venden lo que busca"),
    FollowUpCase(((C, "deja así"), (N, "Listo, cualquier cosa me escribes.")), False, "deja así (Colombia)"),
    FollowUpCase(((C, "Qué fastidio, ya les dije que no"),), False, "molesto"),
)
