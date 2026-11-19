"""Los casos del lector de pagos: mensajes de clientes con lo último que les dijo el asesor y la lectura correcta.

El lector (`application/pipeline/payment_reading.py`) dice, antes de que responda el asesor, si con este mensaje el cliente debe
recibir los datos para pagar, de qué medio, y si dice que ya pagó. `run_reader_eval.py` corre estos casos con la IA real.

Los casos salen de sus instrucciones (`prompting/payment_reader.PAYMENT_READER`) y de lo que se vio con la IA real:
- 19 nov 2026, puerta del panel: ante «Me convence, lo quiero» el lector dijo en 3 de 3 conversaciones que el cliente pedía los
  datos, y el motor le indicó al asesor «pregúntale con qué medio paga» en un negocio que solo capta datos. Querer comprar no es
  pedir los datos; aceptar cuando el asesor ofrece justo enviárselos, sí.

Los medios son los del negocio de ejemplo `asesor_ai_prod` (Nequi, Daviplata, transferencia a Bancolombia, Bre-B y link de pago).
"""
from __future__ import annotations

from dataclasses import dataclass

# Lo que le dijo el asesor antes, en los casos que lo necesitan.
OFFERS_DETAILS = "Con gusto. ¿Quiere que le envíe los datos para pagar?"
ASKS_METHOD = "¡Perfecto! ¿Con cuál medio prefiere pagar: Nequi, Daviplata, transferencia, Bre-B o link de pago?"
OFFERS_TO_START = "El Plan Básico cuesta COP 210.000 el primer mes y luego COP 110.000 mensuales. ¿Le gustaría avanzar con la activación?"
GIVES_PRICE = "El Plan Básico cuesta COP 210.000 el primer mes, con la configuración incluida, y luego COP 110.000 al mes."


@dataclass(frozen=True)
class ReaderCase:
    name: str
    message: str
    wants_details: bool
    # El medio (clave del negocio: nequi, daviplata, link…) cuando el cliente lo nombra; "" si no nombra ninguno.
    method: str = ""
    says_paid: bool = False
    last_reply: str = ""
    # Si al cliente ya le llegaron los datos de ese medio antes (entonces el lector lo sabe).
    sent: str = ""


CASES = (
    # Pide los datos o dice con qué paga: los recibe.
    ReaderCase("pide el número", "pásame el número para pagar", True),
    ReaderCase("pregunta a qué cuenta consigna", "¿A qué cuenta te consigno?", True),
    ReaderCase("se le borraron", "se me borró, envíamelo de nuevo", True, method="nequi", sent="nequi"),
    ReaderCase("dice con qué paga", "Te pago por Nequi", True, method="nequi"),
    ReaderCase("prefiere el link", "prefiero el link", True, method="link"),
    ReaderCase("responde el medio que le preguntan", "Daviplata", True, method="daviplata", last_reply=ASKS_METHOD),
    ReaderCase("pide los datos de un medio", "listo, mándame los datos para pagar por Bre-B", True, method="breb"),
    # Acepta cuando el asesor le ofrece enviarle los datos: los recibe.
    ReaderCase("acepta que se los envíen", "sí, envíamelos", True, last_reply=OFFERS_DETAILS),
    ReaderCase("acepta con un dale", "dale", True, last_reply=OFFERS_DETAILS),
    ReaderCase("acepta diciendo que lo quiere", "sí, lo quiero", True, last_reply=OFFERS_DETAILS),
    # Pregunta, duda o habla de otra cosa: no los recibe.
    ReaderCase("pregunta si puede transferir", "y puedo transferir", False),
    ReaderCase("pregunta cómo paga", "¿cómo pago?", False),
    ReaderCase("pregunta si tienen un medio", "¿Tienen Nequi?", False),
    ReaderCase("avisa que va a pagar", "ya voy a pagar", False),
    ReaderCase("no entiende", "cómo así", False, last_reply=GIVES_PRICE),
    ReaderCase("pregunta el precio", "¿cuánto cuesta?", False),
    # Quiere comprar o avanzar, sin pedir los datos ni aceptar que se los envíen: no los recibe (19 nov 2026).
    ReaderCase("decide después del precio", "Me convence, lo quiero", False, last_reply=GIVES_PRICE),
    ReaderCase("acepta avanzar", "Me convence, lo quiero", False, last_reply=OFFERS_TO_START),
    ReaderCase("lo quiere sin contexto", "Me convence, lo quiero", False),
    ReaderCase("quiere empezar", "sí, quiero empezar", False, last_reply=OFFERS_TO_START),
    ReaderCase("dice que avancen", "listo, avancemos", False, last_reply=OFFERS_TO_START),
    ReaderCase("lo toma", "dale, lo tomo", False, last_reply=OFFERS_TO_START),
    ReaderCase("quiere comprarlo", "quiero comprarlo, ¿cómo seguimos?", False, last_reply=GIVES_PRICE),
    # Con frases que no están en los ejemplos del lector: que entienda la idea, no que reconozca la frase.
    ReaderCase("se lo lleva", "perfecto, me lo llevo", False, last_reply=GIVES_PRICE),
    ReaderCase("le dice que le hagan", "hágale pues, de una", False, last_reply=OFFERS_TO_START),
    ReaderCase("lo compra", "va, lo compro", False, last_reply=GIVES_PRICE),
    ReaderCase("quiere el plan", "sí, quiero el plan básico", False, last_reply=OFFERS_TO_START),
    ReaderCase("acepta que se los pasen", "bueno, pásalos", True, last_reply=OFFERS_DETAILS),
    ReaderCase("acepta con un ok", "ok, mándamelos", True, last_reply=OFFERS_DETAILS),
    # Dice que ya pagó, o que va a pagar.
    ReaderCase("ya consignó", "ya te consigné", False, says_paid=True, sent="nequi"),
    ReaderCase("envía el comprobante", "ahí te mando el comprobante del pago", False, says_paid=True, sent="nequi"),
    ReaderCase("paga mañana", "mañana te pago", False, sent="nequi"),
)
