"""Conversaciones de prueba: un cliente con guion, según cómo vende el negocio.

Cada guion prueba lo que un vendedor profesional debe hacer bien: saludar, explicar la oferta, dar precios reales, no inventar lo que
no sabe, manejar una objeción, cerrar, llevar al pago y responder cuando el cliente dice que ya pagó. Las preguntas usan productos y
medios de pago reales del negocio; la pregunta «trampa» pide algo que la ficha no tiene, para ver si el asistente lo inventa.
"""
from __future__ import annotations


def _first_offer(facts: dict) -> str:
    return facts["oferta"][0]["name"] if facts["oferta"] else "lo que ofrecen"


def _payment_choice(facts: dict) -> tuple[str, str]:
    """(cómo lo dice el cliente, método) con un medio de pago que el negocio sí tiene."""
    kinds = facts["pagos_disponibles"]
    for kind, said in (("nequi", "Nequi"), ("daviplata", "Daviplata"), ("bank", "transferencia bancaria"), ("breb", "Bre-B")):
        if kinds.get(kind):
            return said, kind
    return ("el link de pago", "link") if kinds.get("link") else ("transferencia", "")


def turns_for(facts: dict) -> list[dict]:
    """Los turnos del cliente, cada uno con lo que se espera comprobar en la respuesta."""
    offer = _first_offer(facts)
    said, _method = _payment_choice(facts)
    model = facts["modelo"]
    if model == "catalog":
        script = [
            ("Hola, buenas tardes", "saludo"),
            ("¿Qué tienen?", "oferta"),
            (f"¿Cuánto vale {offer}?", "precio"),
            ("¿Hacen envíos a España?", "trampa"),
            ("Mmm, está un poco caro", "objecion"),
            (f"Bueno, quiero pedir {offer}", "compra"),
            ("¿Cómo te pago?", "pago"),
            (f"Por {said}", "metodo"),
            ("Listo, ya te pagué", "pago_reportado"),
        ]
    elif model == "saas":
        script = [
            ("Hola", "saludo"),
            ("¿Qué es lo que ofrecen?", "oferta"),
            ("Tengo un negocio y no alcanzo a responder todos los mensajes", "dolor"),
            ("¿Cuánto cuesta?", "precio"),
            (f"¿Qué incluye el {offer}?", "detalle"),
            ("¿Funciona también con TikTok y con mi página web en Shopify?", "trampa"),
            ("Está caro para mí", "objecion"),
            (f"Ok, quiero empezar con el {offer}", "compra"),
            (f"Te pago por {said}", "metodo"),
            ("Listo, ya pagué", "pago_reportado"),
        ]
    else:
        script = [
            ("Hola, buen día", "saludo"),
            ("¿Qué servicios tienen?", "oferta"),
            ("¿Cuánto cuesta?", "precio"),
            ("¿Atienden los domingos en la noche?", "trampa"),
            ("Quiero agendar", "compra"),
            ("¿Cómo pago?", "pago"),
            (f"Por {said}", "metodo"),
            ("Ya pagué", "pago_reportado"),
        ]
    return [{"turn": number, "message": message, "kind": kind} for number, (message, kind) in enumerate(script, start=1)]
