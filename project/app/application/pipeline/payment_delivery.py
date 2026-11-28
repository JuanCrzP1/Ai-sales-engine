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
3. **No envía datos que el cliente no pidió.** Si el asesor iba a enviar por su cuenta unos datos que el cliente no pidió (los que
   ya tiene, o los de un medio cuando el negocio tiene varios: preguntar «¿puedo transferir?» no es pedirlos), se le pide que responda
   otra vez, sabiendo por qué (`payment_problem`, en `answer_review.py`). Si insiste, no salen. Lo decide el lector de pagos, no
   las palabras del asesor.

Lo que dice el asesor no se revisa con reglas de palabras. Hasta el 20 nov 2026 había dos: si decía que no podía dar los datos o
que el negocio no recibía un medio que sí tenía, se le pedía otra respuesta y, si insistía, su mensaje se cambiaba por una frase
fija. La del medio negado no actuó nunca en 1377 turnos de la puerta de calidad desde el 16 nov; la de la negativa actuó 2 veces,
siempre ante un «cómo así» con los datos ya enviados, y la causa era una instrucción del prompt («el cliente no recibe datos de
pago», que la IA le repetía como «no puedo enviarlos»). Se corrigió la instrucción (`instructions.PAYMENT_HAS_DETAILS`) en vez de
tapar su efecto. Que no diga nada falso del pago lo mide la puerta («no dice nada falso del pago»).

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
from app.domain.business_config.formality import Phrase, formality_of
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
# El equipo confirmó el pago (`payment_outcome.remember_confirmed_payment`): ya no falta nada del cliente.
PAYMENT_CONFIRMED = "payment_confirmed"
PAYMENT_STATE_HOURS = 6
# Lo que queda en la memoria de la conversación cuando los datos salieron sin palabras del asesor, con el trato del negocio
# (`domain/business_config/formality.py`): la IA lo ve en su historial. Al cliente nunca le llega solo.
PAYMENT_SENT_MEMORY = Phrase(tu="Te dejo aquí los datos para pagar por {method}.", usted="Le dejo aquí los datos para pagar por {method}.")


def remembered_message(delivery: "PaymentDelivery", runtime_yaml: dict) -> str:
    """Lo que la IA verá en su historial de este mensaje: lo que dijo ella y, donde fueron los datos, su marcador («[dato de pago]»).
    No ve el mensaje con los datos (lo copiaría como si lo hubiera escrito) ni puede recordar un número (lo inventaría)."""
    lead = delivery.lead.strip() or PAYMENT_SENT_MEMORY.to(formality_of(runtime_yaml)).format(method=sent_label(runtime_yaml, delivery.method))
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


def confirmed_state(method: str, now: datetime | None = None) -> OperationalState:
    """El paso de la conversación cuando el equipo confirmó el pago: ya no falta que el cliente pague (reemplaza a `sent_state`)."""
    moment = now or datetime.now(timezone.utc)
    return OperationalState(
        active_process="payment", active_option=method, pending_action=PAYMENT_CONFIRMED, expires_at=moment + timedelta(hours=PAYMENT_STATE_HOURS)
    )


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


_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
# El marcador del dato solo en un renglón.
_MARKER_LINE = re.compile(rf"[ \t]*{re.escape(REDACTED_PAYMENT_VALUE)}[ \t.]*")
# Un marcador entre corchetes (el del dato u otro que escriba la IA: «[nombre del titular]»). Un enlace «[texto](url)» no lo es.
_PLACEHOLDER = re.compile(r"\[[^\[\]\n]{1,60}\](?!\()")


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


def payment_problem(
    response_text: str,
    runtime_yaml: dict,
    *,
    send_payment: str = "",
    asked: bool | None = None,
    state: OperationalState | None = None,
    remembered: str = "",
) -> dict:
    """Por qué la respuesta de la IA no puede salir así y se le pide otra (`answer_review.py`), o `{}` si está bien:

    - `{"repeated": medio}`: iba a enviarle otra vez unos datos que el cliente ya tiene y no pidió;
    - `{"unrequested": medio}`: iba a enviarle por su cuenta los datos de un medio, y el negocio tiene varios. El cliente no los
      pidió ni dijo que paga con ese medio (preguntar «¿puedo transferir?» no lo es): primero se le pregunta con cuál quiere pagar.

    `asked` es lo que entendió el lector de pagos de este mensaje (si el cliente debe recibir los datos); sin lectura (`asked` es
    None) no se revisan: se confía en la acción del asesor. Con un solo medio de pago, el asesor puede enviarlo por
    su cuenta (una vez).
    """
    offered = options(runtime_yaml)
    if not offered:
        return {}
    current = current_method(state, remembered, runtime_yaml)
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
