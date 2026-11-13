"""Qué medio de pago nombra o pide el cliente (o la IA), con cualquier medio que tenga el negocio.

Lo usa `payment_delivery.py` para no depender de que la IA marque bien su acción: si el cliente pide los datos con todas las letras
(«envíame el Yape», «pásame la cuenta de Davivienda», «se me borró, ¿me lo envías de nuevo?»), se sabe de qué medio son. Se reconoce
cada medio por su nombre en el catálogo (`payment_catalog.py`), cada banco por su nombre y cada «otro medio» por el nombre que le
puso el negocio.
"""
from __future__ import annotations

import re

from app.domain.business_config.payment_accounts import accounts, option_of, options
from app.domain.business_config.payment_catalog import method_kind

# Cómo se nombra el enlace de pago en un mensaje.
_LINK = r"\blink\b|\benlace\b|\bpago en l[ií]nea\b|\bpse\b|\btarjeta de cr[eé]dito\b"
# Pedir algo: «envíame», «pásame», «dame», «¿cuál es…?», «se me borró», «no me llegó», «otra vez»…
_REQUEST = re.compile(
    r"\b(env[ií]a(me|melo|mela|los)?|m[aá]nda(me|melo|mela)?|p[aá]sa(me|melo|mela)?|da(me|melo|mela)|reenv[ií]a(me|melo)?|"
    r"rep[ií]te(me|melo)?|comp[aá]rte(me|melo)?|cu[aá]l es|me (das|pasas|env[ií]as|mandas|compartes|repites|regalas)|necesito|"
    r"reg[aá]la(me|melo|mela)?|a d[oó]nde (te |le )?(consigno|transfiero|pago|mando|env[ií]o|deposito)|a qu[eé] (n[uú]mero|cuenta)|"
    r"c[oó]mo (te |le )?(pago|consigno|transfiero)|"
    r"me lo (env[ií]as|mandas|pasas|das|repites)|se me borr[oó]|no me lleg[oó]|no lo (tengo|encuentro|veo)|otra vez|de nuevo)\b"
)
# Lo que pide son los datos de pago, sin nombrar el medio: «el número», «la cuenta», «los datos para pagar», «el link de pago».
_PAYMENT_DATA = re.compile(
    r"\b(datos (de|para) pag\w*|los datos|n[uú]mero (de|para) (pag\w*|la cuenta|cuenta)|n[uú]mero|la cuenta|cuenta (de|para) pag\w*|"
    r"link (de|para) pag\w*|enlace (de|para) pag\w*|la llave|el alias|la clabe|el iban|a d[oó]nde|a qu[eé] (n[uú]mero|cuenta))\b"
)
# Lo que no es un pedido de datos de pago aunque lo parezca: el número o la cuenta de otra cosa.
_NOT_PAYMENT = re.compile(
    r"\b(whatsapp|contacto|direcci[oó]n|horario|p[aá]gina|web|instagram|pedido|gu[ií]a|tienda|local|asesor|vendedor|domicilio|"
    r"informaci[oó]n|info|cat[aá]logo|foto|precio|plan)\b"
)
# «Me lo envías de nuevo», «se me borró»: un pedido corto que solo puede ser lo último que se le envió.
_AGAIN = re.compile(r"\b(otra vez|de nuevo|se me borr[oó]|no me lleg[oó]|me lo (env[ií]as|mandas|pasas|das|repites))\b")
# Hasta aquí es un pedido corto («Pero se me borró, ¿me lo envías de nuevo porfa?»); uno más largo habla de otra cosa.
_SHORT_REQUEST_WORDS = 12
# Elegir un medio: «te pago por Nu», «¿y si pago con PayPal?», «mejor en efectivo», «prefiero Yape».
_CHOICE = re.compile(
    r"\b((te |le )?(pag(o|ar[ée]?|amos|aría)|consign(o|ar[ée]?|amos)|transfier(o|e)|transferir[ée]?|deposit(o|ar[ée]?))|prefiero|mejor|"
    r"quiero pagar|voy a pagar|ser[aá])\b"
)
# «No puedo pagar por Nequi», «no tengo Yape»: no es elegirlo.
_REFUSAL = re.compile(r"\bno (puedo|tengo|quiero|uso|me sirve|me funciona|acepto)\b")
# Pedir una persona con todas las letras.
_ASKS_FOR_PERSON = re.compile(r"\b(una persona|un humano|alguien (del equipo|real)|un asesor|hablar con|que me (llamen|atienda))\b")


def _word(name: str) -> str:
    return rf"\b{re.escape(name.lower())}\b"


def named_option(text: str, runtime_yaml: dict) -> str:
    """El único medio o cuenta del negocio que nombra el texto, o "": `nequi`, `bank:davivienda` (si nombra el banco), `bank` (si
    habla de transferencia bancaria sin decir cuál), `custom:nu`…"""
    lowered = str(text or "").lower()
    offered = options(runtime_yaml)
    found: list[str] = []
    banks = {account.key: account.own_name for account in accounts(runtime_yaml) if account.option == "bank" and account.own_name}
    named_banks = [key for key, bank in banks.items() if re.search(_word(bank), lowered)]
    for option in offered:
        if option == "link":
            hit = bool(re.search(_LINK, lowered))
        elif option == "bank":
            if len(named_banks) == 1:
                found.append(named_banks[0])
                continue
            kind = method_kind("bank")
            hit = bool(named_banks) or bool(kind and re.search(kind.aliases, lowered))
        elif option.startswith("custom:"):
            name = next((account.own_name for account in accounts(runtime_yaml) if account.option == option), "")
            hit = bool(name) and bool(re.search(_word(name), lowered))
        else:
            kind = method_kind(option)
            hit = bool(kind and re.search(kind.aliases, lowered))
        if hit:
            found.append(option)
    return found[0] if len(found) == 1 else ""


def resolve(value: str, runtime_yaml: dict) -> str:
    """Lo que la IA puso como medio («nequi», «Nequi», «transferencia a Bancolombia», «Nu»), como clave del negocio, o ""."""
    text = str(value or "").strip().lower()
    if not text:
        return ""
    offered = options(runtime_yaml)
    keys = {account.key for account in accounts(runtime_yaml)}
    if text in offered or text in keys:
        return text
    return named_option(text, runtime_yaml)


def refine(key: str, *texts: str, runtime_yaml: dict) -> str:
    """Si se sabe el medio pero no la cuenta («bank») y el cliente o la IA nombran uno de los bancos, esa cuenta."""
    if key != "bank":
        return key
    for text in texts:
        named = named_option(text, runtime_yaml)
        if named.startswith("bank:"):
            return named
    return key


def asked_for_payment_details(message: str, runtime_yaml: dict, *, current: str = "") -> str:
    """El medio o la cuenta cuyos datos pide el cliente con todas las letras, o "". Hace falta un pedido y saber de qué medio: el que
    nombra, o el que venían usando si pide «el número» o «de nuevo»."""
    text = str(message or "").lower()
    offered = options(runtime_yaml)
    if not offered or not _REQUEST.search(text) or _NOT_PAYMENT.search(text):
        return ""
    named = named_option(text, runtime_yaml)
    if named:
        return named
    if _PAYMENT_DATA.search(text) or (_AGAIN.search(text) and len(text.split()) <= _SHORT_REQUEST_WORDS):
        if option_of(current) in offered:
            return current
        return offered[0] if len(offered) == 1 else ""
    return ""


def asks_for_person(message: str) -> bool:
    return bool(_ASKS_FOR_PERSON.search(str(message or "").lower()))


def chose_payment_method(message: str, runtime_yaml: dict) -> str:
    """El medio que el cliente elige con todas las letras («te pago por Nu», «mejor en efectivo»), o "". Hace falta nombrar uno solo
    de los medios del negocio y decir que paga con él; preguntar si lo aceptan («¿tienen Daviplata?») no es elegirlo."""
    text = str(message or "").lower().strip(" ¿?¡!.")
    # Una respuesta corta a «¿con qué medio?»: «Por Yape», «Con Nequi», «En efectivo».
    short_answer = len(text.split()) <= 4 and re.match(r"(por|con|en|a trav[eé]s de)\b", text)
    if not (_CHOICE.search(text) or short_answer) or _REFUSAL.search(text):
        return ""
    return named_option(text, runtime_yaml)


# Preguntar por otro medio cuando ya están pagando: «¿Y Nequi no?», «¿y por Daviplata?», «¿o con PayPal?».
_OTHER_METHOD = re.compile(r"^(y|o|pero)\b")
_OTHER_METHOD_WORDS = 6


def asks_about_another_method(message: str, runtime_yaml: dict, *, current: str = "") -> str:
    """Si ya venían pagando por un medio y el cliente pregunta corto por otro de los del negocio («¿Y Nequi no?»), ese otro, o ""."""
    text = str(message or "").lower().strip(" ¿?¡!.")
    if not current or len(text.split()) > _OTHER_METHOD_WORDS or not _OTHER_METHOD.match(text) or _REFUSAL.search(text):
        return ""
    named = named_option(text, runtime_yaml)
    return named if named and option_of(named) != option_of(current) else ""


# Avisar que ya pagó, como lo dice la gente: «ya te consigné», «ya hice la transferencia», «te mando el pantallazo».
_REPORTED = re.compile(
    r"\bya (te |le )?(pagu[eé]|consign[eé]|transfer[ií]|deposit[eé]|envi[eé] (la plata|el dinero|el pago|la transferencia))\b|"
    r"\bya (hice|realic[eé]|mand[eé]) (el pago|la transferencia|la consignaci[oó]n|la plata|el dep[oó]sito)\b|"
    r"\bya (est[aá]|qued[oó]) (pago|pagado)\b|\b(te |le )?(mando|env[ií]o|paso|adjunto) (el|la) (comprobante|pantallazo|soporte|captura)\b|"
    r"\bah[ií] (te )?va el (comprobante|pantallazo|soporte)\b"
)
_NOT_YET = re.compile(r"\b(no|todav[ií]a no|a[uú]n no) (he |te |le )?(pagad|pagu|consign|transfer|hecho)")


def reported_payment(message: str) -> bool:
    """Si el cliente dice que ya pagó (o envía el soporte), con sus palabras. «Ya voy a pagar» o «todavía no he pagado» no cuentan."""
    text = str(message or "").lower()
    return bool(_REPORTED.search(text)) and not _NOT_YET.search(text)
