"""Los casos del lector del saludo: primeros mensajes de clientes y si son solo un saludo.

Si el cliente solo saluda y el negocio escribió su saludo (Mensajes → Bienvenida), le llega ese saludo tal cual; si además pide,
pregunta o cuenta algo, responde la IA. Equivocarse hacia «solo saluda» es lo grave: el cliente que preguntó el precio recibiría un
saludo fijo en vez de su respuesta. Equivocarse hacia «no solo saluda» es leve: responde la IA, que también saluda.

Los saludos son de varios países a propósito: la lista de palabras que hubo hasta el 26 nov 2026 solo conocía los de Colombia.
`run_greeting_eval.py` corre estos casos con la IA real y, gratis, con esa lista, para comparar.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GreetingCase:
    message: str
    greets_only: bool
    # De dónde es (o qué prueba): para leer el informe.
    note: str = ""


CASES = (
    # Solo saluda: recibe el saludo del negocio.
    GreetingCase("hola", True, "Colombia y todos"),
    GreetingCase("Hola", True, "con mayúscula"),
    GreetingCase("holaaa", True, "alargado"),
    GreetingCase("buenas", True, "Colombia"),
    GreetingCase("Buenas tardes", True, "todos"),
    GreetingCase("Buenos días", True, "todos"),
    GreetingCase("buen día", True, "Argentina"),
    GreetingCase("qué más pues", True, "Colombia"),
    GreetingCase("quiubo", True, "Colombia"),
    GreetingCase("¿Qué onda?", True, "México"),
    GreetingCase("Hola, ¿qué tal?", True, "España y Argentina"),
    GreetingCase("Hola, buenas tardes, ¿cómo están?", True, "cortesía larga"),
    GreetingCase("Buenas noches", True, "todos"),
    GreetingCase("épale", True, "Venezuela"),
    GreetingCase("Hola, cómo estái", True, "Chile"),
    GreetingCase("👋", True, "solo un emoji"),
    GreetingCase("hola 😊", True, "con emoji"),
    GreetingCase("Saludos", True, "formal"),
    GreetingCase("hi", True, "en inglés"),
    GreetingCase("hey", True, "corto"),
    # Saluda y además pide, pregunta o cuenta algo: responde la IA.
    GreetingCase("hola, ¿cuánto cuesta?", False, "precio"),
    GreetingCase("Buenas, quiero hacer un pedido", False, "pedido"),
    GreetingCase("hola me interesa", False, "interés"),
    GreetingCase("hola precio", False, "sin signos"),
    GreetingCase("Qué onda, ¿tienen envíos a Monterrey?", False, "México, pregunta"),
    GreetingCase("Buenos días, necesito una cita para mañana", False, "cita"),
    GreetingCase("Hola, ¿están abiertos hoy?", False, "horario"),
    GreetingCase("Hola, soy Laura de la tienda Bella", False, "se presenta"),
    GreetingCase("hola vi su anuncio en Instagram", False, "cuenta de dónde viene"),
    GreetingCase("buenas tardes, ¿hacen domicilios?", False, "domicilio"),
    GreetingCase("Hola, ¿tienen Nequi?", False, "medio de pago"),
    GreetingCase("qué más parce, ¿cómo funciona eso?", False, "Colombia, pregunta"),
    # Sin saludo.
    GreetingCase("¿Cuánto cuesta el plan?", False, "pregunta directa"),
    GreetingCase("Quiero comprar", False, "compra"),
    GreetingCase("precio", False, "una palabra"),
    GreetingCase("me pasas el menú", False, "pide algo"),
)
