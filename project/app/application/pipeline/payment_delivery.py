"""Los datos de pago: el asesor (la IA) habla y el sistema pone los datos reales debajo de su mensaje.

La IA nunca ve los números, cuentas, llaves ni enlaces de pago (se equivocaría en un dígito, o se los daría a quien no debe). Solo
conoce el nombre de cada medio («Nequi», «Yape», «transferencia a Davivienda»).

Este sistema es AI-first: entender al cliente es trabajo de la IA. Aquí no se adivina por palabras lo que quiso decir el cliente ni
se cambia lo que dijo el asesor. El código hace solo tres cosas:

1. **Entrega los datos.** Cuando el cliente debe recibirlos (lo entiende el lector de pagos, otra llamada a la IA:
   `payment_reading.py`), el mensaje con los datos (la plantilla del negocio) va debajo de lo que dijo el asesor, o donde él puso el
   marcador del dato. Si no, sale lo que dijo el asesor, tal cual. El asesor también puede enviarlos por su cuenta con su acción
   (`metadata.send_payment`), una vez, cuando el negocio tiene un solo medio de pago o cuando no hubo lectura.
2. **Cuida el dato.** El marcador con el que la IA ve los datos («[dato de pago]») nunca le llega al cliente. Si la IA lo escribe, le
   está dando los datos: van en ese lugar de su mensaje (o dentro de su frase, si el cliente ya los tenía). Si no se sabe de qué
   medio, se le pregunta al cliente con cuál quiere pagar.
3. **No deja salir algo falso sobre los pagos.** Se le pide a la IA que responda otra vez, sabiendo por qué (`payment_problem`, en
   `ai_execution.py`), si su respuesta:
   - dice que no puede dar los datos (sí puede). Si insiste, su mensaje no sale: van los datos con una frase corta encima si el
     cliente debía recibirlos; si no los pidió, se le recuerda que ya los tiene o se le ofrecen. El mensaje con los datos nunca va solo;
   - dice que el negocio no recibe un medio que sí tiene. Si insiste, sale la verdad («Sí, claro: también recibimos Nequi»);
   - iba a enviar por su cuenta unos datos que el cliente no pidió: los que ya tiene, o los de un medio cuando el negocio tiene
     varios (preguntar «¿puedo transferir?» no es pedirlos). Si insiste, no salen.

Las piezas: `domain/business_config/payment_accounts.py` (las cuentas del negocio y el mensaje con sus datos) y `payment_names.py`
(cómo se reconoce el medio que escribe la IA). Cada vez que actúa un cuidado (2 o 3) queda registrado (`pago_red_de_seguridad`,
`pago_segunda_respuesta`), para ver si la IA falla antes de que un cliente se queje. Cómo responde la IA se mide con la IA real
(`experiments/quality_lab`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.application.pipeline.payment_names import named_option, refine, resolve
from app.domain.business_config.payment_accounts import (
    inline_details,
    option_label,
    option_of,
    options,
    payment_message,
    same_payment,
    which_method_question,
)
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE
from app.domain.operations.operational_state import OperationalState
from app.utils.logger import logger

# El paso de la conversación después de enviar los datos: el cliente paga y envía el comprobante.
AWAITING_PAYMENT = "report_payment"
PAYMENT_STATE_HOURS = 6
# La IA dijo que no podía enviar los datos (dos veces): su mensaje no sale; sale una de estas frases, que sí es verdad.
REFUSED = "la_ia_dijo_que_no_podia"
# El cliente ya tiene los datos y no los pidió: no se repiten (un «cómo así» recibía el bloque otra vez, sin palabras; 13 nov 2026).
ALREADY_HAS_DETAILS = "Arriba te dejé los datos para pagar por {method}. Si quieres, te los envío otra vez."
# El cliente no los pidió y todavía no los tiene: se le ofrecen.
OFFER_METHOD_DETAILS = "Claro, puedes pagar por {method}. ¿Quieres que te envíe los datos?"
# Si la IA insiste (dos veces) en que el negocio no recibe un medio que sí tiene, esa respuesta falsa no sale: sale esta.
METHOD_AVAILABLE = "Sí, claro: también recibimos {method}."
OFFER_DETAILS = "¿Quieres que te envíe los datos para pagar?"
# Lo que dice el asesor encima de los datos cuando su mensaje no puede salir (dijo que no podía enviarlos), y lo que queda en la
# memoria de la conversación cuando los datos salieron sin palabras suyas. El mensaje con los datos nunca va solo.
PAYMENT_SENT_MEMORY = "Te dejo aquí los datos para pagar por {method}."


def remembered_message(delivery: "PaymentDelivery", runtime_yaml: dict) -> str:
    """Lo que la IA verá en su historial de este mensaje: lo que dijo ella y, donde fueron los datos, su marcador («[dato de pago]»).
    No ve el mensaje con los datos (lo copiaría como si lo hubiera escrito) ni puede recordar un número (lo inventaría)."""
    lead = delivery.lead.strip() or PAYMENT_SENT_MEMORY.format(method=sent_label(runtime_yaml, delivery.method))
    return compose(lead, REDACTED_PAYMENT_VALUE, delivery.tail)


def compose(*parts: str) -> str:
    """Lo que dice el asesor, el mensaje con los datos de pago y lo que dijo después, cada parte en su párrafo."""
    return "\n\n".join(text for part in parts if (text := str(part or "").strip()))


@dataclass(frozen=True)
class PaymentDelivery:
    """Lo que se le responde al cliente: lo que dice el asesor (`lead`), si salieron, el mensaje con los datos (`details`) y de qué
    medio o cuenta son (`method`), y lo que dijo el asesor después del lugar donde puso los datos (`tail`). `rescue` dice qué cuidado
    actuó."""

    lead: str
    details: str = ""
    method: str = ""
    rescue: str = ""
    tail: str = ""

    @property
    def text(self) -> str:
        return compose(self.lead, self.details, self.tail)


def _template(runtime_yaml: dict) -> str | None:
    """La plantilla del negocio para los datos de pago (Mensajes → «Cómo le llegan los datos de pago»), o None: la de la plataforma."""
    config = runtime_yaml.get("config") if isinstance(runtime_yaml.get("config"), dict) else {}
    return str(config.get("payment_details_message") or "").strip() or None


def ejecutar_pago(runtime_yaml: dict, payment_method: str) -> str:
    """El mensaje con los datos reales de ese medio o cuenta (con la plantilla del negocio), o "" si no lo tiene activo."""
    return payment_message(runtime_yaml, resolve(payment_method, runtime_yaml), _template(runtime_yaml))


def sent_state(method: str, now: datetime | None = None) -> OperationalState:
    """El paso de la conversación después de enviar los datos de `method`: falta que el cliente pague y envíe el comprobante."""
    moment = now or datetime.now(timezone.utc)
    return OperationalState(active_process="payment", active_option=method, pending_action=AWAITING_PAYMENT, expires_at=moment + timedelta(hours=PAYMENT_STATE_HOURS))


def already_sent(state: OperationalState | None, method: str) -> bool:
    """Si ya se le enviaron al cliente los datos de ese medio (o de esa misma cuenta) y falta que pague."""
    return bool(
        state and state.is_active() and state.active_process == "payment" and state.pending_action == AWAITING_PAYMENT
        and same_payment(state.active_option, method)
    )


def current_method(state: OperationalState | None, remembered: str, runtime_yaml: dict) -> str:
    """El medio del pago en curso o, si no, el que el cliente ya había elegido en la conversación (lo guarda la memoria)."""
    in_payment = state.active_option if state and state.is_active() and state.active_process == "payment" else ""
    return in_payment or resolve(remembered, runtime_yaml)


def sent_label(runtime_yaml: dict, method: str) -> str:
    """Cómo se nombra en una frase el medio cuyos datos salieron: «Nequi», «transferencia a Bancolombia»."""
    return option_label(runtime_yaml, option_of(method))


def _log(rescue: str, key: str, tenant: str) -> None:
    if rescue:
        logger.warning("pago_red_de_seguridad", extra={"tenant": tenant, "how": rescue, "method": key})


def _send(runtime_yaml: dict, key: str, response_text: str, rescue: str = "", tenant: str = "") -> PaymentDelivery:
    """El mensaje con los datos de `key` debajo de lo que dice el asesor (o donde él puso el marcador del dato)."""
    details = payment_message(runtime_yaml, key, _template(runtime_yaml))
    lead, tail = _around_marker(response_text)
    if not details:
        return PaymentDelivery(compose(lead, tail))
    _log(rescue, key, tenant)
    return PaymentDelivery(lead, details, key, rescue, tail)


def deliver(
    response_text: str,
    runtime_yaml: dict,
    *,
    send_payment: str = "",
    payment_method: str = "",
    asked: bool | None = None,
    asked_method: str = "",
    hold: bool = False,
    state: OperationalState | None = None,
    remembered: str = "",
    tenant: str = "",
) -> PaymentDelivery:
    """Qué recibe el cliente: lo que dice el asesor y, debajo, los datos de pago si el cliente los pidió o el asesor lo decidió con
    su acción. `asked` y `asked_method` son lo que entendió el lector de pagos del mensaje del cliente (`payment_reading.py`): si
    debe recibir los datos y de qué medio; `asked` es None si no hubo lectura. `hold`: el asesor insistió en enviar unos datos que el
    cliente no pidió (`payment_problem`): no salen. `remembered` es el medio que el cliente ya había elegido en la conversación:
    sirve para saber de qué medio habla la IA cuando nombra «los datos»."""
    offered = options(runtime_yaml)
    if not offered:
        return PaymentDelivery(response_text)
    # La IA dice el medio («bank», «Nequi»); si en su mensaje nombra uno de los bancos del negocio, va esa cuenta.
    action = refine(resolve(send_payment, runtime_yaml), response_text, runtime_yaml=runtime_yaml)
    chosen = refine(resolve(payment_method, runtime_yaml), response_text, runtime_yaml=runtime_yaml)
    current = current_method(state, remembered, runtime_yaml)

    # 3. Una negativa falsa no sale. En su lugar va una frase corta que sí es verdad, según lo que entendió el lector de pagos: si el
    # cliente debe recibir los datos (o no hubo lectura), van debajo de esa frase; si no los pidió, no se le envían (se le recuerda que
    # ya los tiene, o se le ofrecen). Sin saber el medio, se le pregunta con cuál quiere pagar.
    if says_it_cannot_send(response_text, paying=bool(current)):
        # De qué medio: el que pide el cliente, el de la acción de la IA, el elegido, el del pago en curso, el que nombra la IA en su
        # negativa («no puedo enviarte el número de Nequi») o el único que tiene el negocio.
        known = ((asked_method if asked else "") or action or chosen or current or named_option(response_text, runtime_yaml)
                 or (offered[0] if len(offered) == 1 else ""))
        _log(REFUSED, known, tenant)
        if not known:
            return PaymentDelivery(which_method_question(runtime_yaml), rescue=REFUSED)
        label = sent_label(runtime_yaml, known)
        if asked is False:
            line = ALREADY_HAS_DETAILS if already_sent(state, known) else OFFER_METHOD_DETAILS
            return PaymentDelivery(line.format(method=label), rescue=REFUSED)
        return _send(runtime_yaml, known, PAYMENT_SENT_MEMORY.format(method=label), REFUSED)

    if hold:
        return PaymentDelivery(_clean(response_text))
    # 1. El cliente pidió los datos (lo entendió el lector): le llegan, debajo de lo que dijo el asesor.
    if asked and asked_method:
        return _send(runtime_yaml, asked_method, response_text)
    # La acción del asesor: los datos van debajo de lo que dijo. Una vez por medio: los que ya salieron no se repiten si el cliente
    # no los pidió. Sin lectura (`asked` es None) no se sabe si los pidió: se confía en la acción.
    if action and (asked is not False or not already_sent(state, action)):
        return _send(runtime_yaml, action, response_text)
    if REDACTED_PAYMENT_VALUE not in response_text:
        return PaymentDelivery(response_text)

    # 2. La IA escribió el marcador del dato: está dando los datos. Solo en un renglón (así lo ve en su historial, donde fueron los
    # datos), van debajo de su mensaje; dentro de una frase, también, o el dato va en la frase si el cliente ya los tenía. El medio
    # se sabe por su acción, por lo que eligió el cliente, por el que nombra ella, por el pago en curso o porque hay uno solo.
    candidates = (
        ("accion_de_la_ia", action),
        ("medio_elegido", chosen),
        ("respuesta_de_la_ia", named_option(response_text, runtime_yaml)),
        ("medio_en_curso", current if option_of(current) in offered else ""),
        ("unico_medio", offered[0] if len(offered) == 1 else ""),
    )
    how, method = next(((how, method) for how, method in candidates if method), ("pregunta", ""))
    in_a_sentence = not any(_MARKER_LINE.fullmatch(line) for line in response_text.splitlines())
    if method and in_a_sentence and already_sent(state, method):
        # Ya tiene los datos y la IA los nombra al explicar («te envié el Nequi [dato]…»): el dato real va dentro de su frase.
        _log(f"{how}_en_la_frase", method, tenant)
        return PaymentDelivery(response_text.replace(REDACTED_PAYMENT_VALUE, inline_details(runtime_yaml, method)), method=method, rescue=how)
    if method:
        return _send(runtime_yaml, method, response_text, how, tenant)
    _log(how, "", tenant)
    return PaymentDelivery(which_method_question(runtime_yaml), rescue=how)


# «No puedo darte el número de cuenta», «no puedo enviarte el Nequi directamente»: lo que un modelo pequeño a veces dice, y es falso.
_REFUSES_DATA = re.compile(
    r"\bno (puedo|podemos|me es posible|est[aá] permitido)( \w+)? "
    r"(darte|enviarte|reenviarte|compartirte|pasarte|mandarte|dar|enviar|reenviar|compartir|pasar|mandar)"
    r"( \w+)? (el |los |la |tu |ese |esos )?(n[uú]mero|datos|cuenta|dato|link|enlace|llave|nequi|daviplata|informaci[oó]n de pago)"
)
# «No tengo acceso a los datos», «no puedo ver el número»: otra forma de la misma negativa (medido con la IA real, 13 nov 2026).
_NO_ACCESS = re.compile(
    r"\bno (tengo acceso|puedo ver|puedo acceder|cuento con acceso)( \w+)? (a |al )?(el |los |la |las |tus |esos |ese )?"
    r"(n[uú]meros?|datos|cuentas?|dato|link|enlace|informaci[oó]n de pago)"
)
# «No puedo enviarlo de nuevo»: sin decir qué, solo es una negativa de pago si ya están pagando (podría ser un domicilio).
_REFUSES_IT = re.compile(r"\bno (puedo|podemos) (envi[aá]rtelo|d[aá]rtelo|pas[aá]rtelo|enviarlo|darlo|reenviarlo)\b")
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
# El marcador del dato solo en un renglón.
_MARKER_LINE = re.compile(rf"[ \t]*{re.escape(REDACTED_PAYMENT_VALUE)}[ \t.]*")
# Un marcador entre corchetes (el del dato u otro que escriba la IA: «[nombre del titular]»). Un enlace «[texto](url)» no lo es.
_PLACEHOLDER = re.compile(r"\[[^\[\]\n]{1,60}\](?!\()")


def says_it_cannot_send(response_text: str, *, paying: bool) -> bool:
    """Si la IA dice que no puede dar los datos de pago. Es falso: los envía el sistema cuando ella marca su acción."""
    text = str(response_text or "").lower()
    return bool(_REFUSES_DATA.search(text)) or (paying and bool(_REFUSES_IT.search(text) or _NO_ACCESS.search(text)))


def _clean(text: str) -> str:
    """Lo que dijo el asesor, sin lo que nunca le llega al cliente: las frases y los renglones donde escribió el marcador del dato o
    un marcador suyo entre corchetes («Número de cuenta: [número]»). El dato real va en el mensaje con los datos."""
    lines = []
    for line in str(text or "").splitlines():
        if line.strip().startswith("```"):
            continue
        if _PLACEHOLDER.search(line):
            line = " ".join(part.strip() for part in _SENTENCE_END.split(line) if part.strip() and not _PLACEHOLDER.search(part))
            if not line:
                continue
        lines.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _around_marker(response_text: str) -> tuple[str, str]:
    """Lo que dijo el asesor antes y después del lugar de los datos. Si escribió el marcador solo en un renglón (así lo ve en su
    historial), ese es el lugar: lo de antes va encima de los datos y lo de después, debajo. Si no, todo va encima."""
    lines = str(response_text or "").strip().splitlines()
    place = next((index for index, line in enumerate(lines) if _MARKER_LINE.fullmatch(line)), None)
    if place is None:
        return _clean("\n".join(lines)), ""
    return _clean("\n".join(lines[:place])), _clean("\n".join(lines[place + 1:]))


# «No ofrecemos Nequi», «Daviplata no lo manejamos»: si el negocio sí lo tiene, es falso. Se mira cada parte de la frase («No
# ofrecemos Nequi, pero puedes pagar por Daviplata»: solo la primera parte niega).
_DENIES = re.compile(
    r"\bno\b[^,.;:!?]{0,30}\b(ofrecemos|aceptamos|recibimos|manejamos|tenemos|trabajamos con|contamos con)\b|"
    r"\bno (est[aá]|es)\b[^,.;:!?]{0,20}\b(disponible|una opci[oó]n|un medio)\b"
)
_CLAUSES = re.compile(r"[.;!?]+|,?\s*\bpero\b|,?\s*\bsin embargo\b|,?\s*\bsolo\b")


def denied_method(response_text: str, runtime_yaml: dict) -> str:
    """El medio de pago del negocio que la IA dice que el negocio no recibe (es falso: lo tiene activo), como se nombra en una frase, o ""."""
    for clause in _CLAUSES.split(str(response_text or "").lower()):
        if _DENIES.search(clause):
            named = named_option(clause, runtime_yaml)
            if named:
                return sent_label(runtime_yaml, named)
    return ""


def payment_problem(
    response_text: str,
    runtime_yaml: dict,
    *,
    send_payment: str = "",
    asked: bool | None = None,
    state: OperationalState | None = None,
    remembered: str = "",
) -> dict:
    """Por qué la respuesta de la IA no puede salir así y se le pide otra (`ai_execution.py`), o `{}` si está bien:

    - `{"refused": True}`: dice que no puede dar los datos de pago (sí puede);
    - `{"denied": medio}`: dice que el negocio no recibe un medio que sí tiene;
    - `{"repeated": medio}`: iba a enviarle otra vez unos datos que el cliente ya tiene y no pidió;
    - `{"unrequested": medio}`: iba a enviarle por su cuenta los datos de un medio, y el negocio tiene varios. El cliente no los
      pidió ni dijo que paga con ese medio (preguntar «¿puedo transferir?» no lo es): primero se le pregunta con cuál quiere pagar.

    `asked` es lo que entendió el lector de pagos de este mensaje (si el cliente debe recibir los datos); sin lectura (`asked` es
    None) las dos últimas no se revisan: se confía en la acción del asesor. Con un solo medio de pago, el asesor puede enviarlo por
    su cuenta (una vez).
    """
    offered = options(runtime_yaml)
    if not offered:
        return {}
    current = current_method(state, remembered, runtime_yaml)
    if says_it_cannot_send(response_text, paying=bool(current)):
        return {"refused": True}
    denied = denied_method(response_text, runtime_yaml)
    if denied:
        return {"denied": denied}
    action = refine(resolve(send_payment, runtime_yaml), response_text, runtime_yaml=runtime_yaml)
    if not action and any(_MARKER_LINE.fullmatch(line) for line in str(response_text or "").splitlines()):
        # Escribió el marcador del dato solo en un renglón (donde van los datos): también es enviarlos por su cuenta.
        action = named_option(response_text, runtime_yaml) or (current if option_of(current) in offered else "") or (offered[0] if len(offered) == 1 else "")
    if not action or asked is not False:
        return {}
    if already_sent(state, action):
        return {"repeated": sent_label(runtime_yaml, action)}
    return {"unrequested": sent_label(runtime_yaml, action)} if len(offered) > 1 else {}


def without_payment_placeholder(response_text: str, runtime_yaml: dict, payment_method: str) -> str:
    """El marcador nunca le llega al cliente: con el medio, los datos reales; sin él, el medio que se deduzca o la pregunta."""
    if REDACTED_PAYMENT_VALUE not in response_text:
        return response_text
    return deliver(response_text, runtime_yaml, payment_method=payment_method).text


def keeps_handoff(delivery: PaymentDelivery) -> bool:
    """Si la IA pasó el chat a una persona porque creía que no podía enviar los datos y el sistema los envió, el chat no pasa por eso."""
    return delivery.rescue != REFUSED
