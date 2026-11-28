"""Confirmar un pago desde el chat: el equipo verificó que el dinero llegó y toca «Confirmar pago».

En un solo paso, y en este orden:
1. Se revisa todo lo que puede fallar antes de tocar nada: que el chat sea del usuario, que el canal permita escribirle al cliente y,
   si el equipo anotó la venta, que sus datos estén bien.
2. El pago deja de estar por confirmar (`claim_payment`) en una sola operación: un doble clic, o dos personas del equipo a la vez,
   no le envían el mensaje dos veces al cliente; el segundo recibe «este pago ya está confirmado».
3. Le llega al cliente el mensaje de pago confirmado del negocio (o el de la plataforma, con su trato y sus emojis:
   `domain/business_config/payment_confirmation.py`). Si el canal no lo entrega, el mensaje queda «no enviado», el pago vuelve a
   estar por confirmar tal como estaba y el panel lo dice: se puede intentar de nuevo.
4. El chat queda atendido y la IA vuelve a atenderlo, si esperaba a una persona solo por el pago (`finish_payment`).
5. La IA sabe que el pago quedó confirmado (`ContactMemory.payment_confirmed`): si el cliente vuelve a escribir, ya no le dice que el
   equipo lo está verificando.
6. Si el equipo anotó lo que compró y el valor, la venta queda registrada (Ventas y Reportes); si no, no se registra ninguna.

El mensaje ya salió cuando se hacen el 5 y el 6: si uno falla, la confirmación no se deshace; se registra y el panel avisa qué
falta (por ejemplo, registrar la venta en Ventas).

Las conversaciones de «Probar asistente» también se pueden confirmar, para ver cómo sigue la IA: el mensaje queda en la bandeja (no
hay canal al que enviarlo) y no se registran ventas.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from app.business_config_application.conversations import PLAYGROUND_CHANNEL, ConversationsService, ReplyNotSentError
from app.business_config_application.ports import CommerceStorage, ContactMemory, ConversationStorage, OutboundMessenger
from app.domain.business_config.access import Principal
from app.domain.business_config.channels import ChannelError
from app.domain.business_config.commerce import NewSale, Sale
from app.domain.business_config.contract import BusinessConfig
from app.domain.business_config.conversations import REPLYABLE_CHANNELS, ChatMessage, ConversationSummary, NewMessage
from app.domain.business_config.errors import BusinessConfigError, FieldIssue, InvalidFieldsError, PaymentNotPendingError
from app.domain.business_config.payment_confirmation import payment_confirmed_message, payment_pending

logger = logging.getLogger("payments")

ALREADY_CONFIRMED = "Este pago ya está confirmado: el cliente ya recibió el mensaje."
SALE_NOT_SAVED = "El cliente ya recibió la confirmación, pero la venta no se registró. Regístrala en Ventas."
MEMORY_NOT_SAVED = "El cliente ya recibió la confirmación, pero el asistente no alcanzó a enterarse. Si el cliente escribe, revisa su respuesta."
CHANNEL_NOT_REPLYABLE = "Desde aquí todavía no se puede escribirle al cliente por este canal."
NO_SALES_IN_TESTS = "En las pruebas no se registran ventas."


@dataclass(frozen=True)
class SaleDraft:
    """Lo que el equipo anotó de la venta al confirmar el pago (todo como lo escribió; se revisa con `NewSale.checked`)."""

    customer_name: str
    description: str
    amount: object
    currency: str


@dataclass(frozen=True)
class PaymentConfirmationPreview:
    """Lo que verá el equipo antes de confirmar: el mensaje que le llegará al cliente y si hay un pago por confirmar."""

    message: str
    pending: bool
    # Una prueba de «Probar asistente»: el mensaje queda en la bandeja y no se registran ventas.
    test: bool


@dataclass(frozen=True)
class PaymentConfirmed:
    """El mensaje que recibió el cliente, cómo quedó el chat, la venta registrada (si se anotó) y lo que quedó pendiente, dicho
    para el equipo."""

    message: ChatMessage
    conversation: ConversationSummary
    sale: Sale | None
    warnings: tuple[str, ...] = ()


class PaymentConfirmationService:
    def __init__(
        self,
        conversations: ConversationStorage,
        inbox: ConversationsService,
        published: Callable[[str], BusinessConfig],
        *,
        messenger: OutboundMessenger | None = None,
        commerce: CommerceStorage | None = None,
        memory: ContactMemory | None = None,
    ) -> None:
        self._conversations = conversations
        self._inbox = inbox
        self._published = published
        self._messenger = messenger
        self._commerce = commerce
        self._memory = memory

    def _business(self, principal: Principal, conversation_id: str) -> str:
        # Las mismas reglas que la bandeja: una conversación ajena responde igual que una inexistente.
        return self._inbox.business_of(principal, conversation_id)

    def _message(self, business: str) -> str:
        try:
            config = self._published(business)
        except BusinessConfigError:  # sin nada publicado: el mensaje de la plataforma
            config = None
        return payment_confirmed_message(config)

    def preview(self, principal: Principal, conversation_id: str) -> PaymentConfirmationPreview:
        business = self._business(principal, conversation_id)
        summary = self._conversations.thread(conversation_id)[0]
        return PaymentConfirmationPreview(self._message(business), payment_pending(summary), summary.channel == PLAYGROUND_CHANNEL)

    def confirm(self, principal: Principal, conversation_id: str, sale: SaleDraft | None = None) -> PaymentConfirmed:
        business = self._business(principal, conversation_id)
        target = self._conversations.target(conversation_id)
        test = target.channel == PLAYGROUND_CHANNEL
        if not test and (target.channel not in REPLYABLE_CHANNELS or self._messenger is None):
            raise InvalidFieldsError(CHANNEL_NOT_REPLYABLE, [FieldIssue("conversation", CHANNEL_NOT_REPLYABLE)])
        new_sale = self._checked_sale(sale, conversation_id, test=test)
        text = self._message(business)

        claim = self._conversations.claim_payment(conversation_id)
        if claim is None:
            raise PaymentNotPendingError(ALREADY_CONFIRMED)
        saved = self._conversations.append(
            business, channel=target.channel, contact_ref=target.contact_ref, contact_name=None,
            message=NewMessage("agent", text, status="sent" if test else "sending"),
        )
        if not test:
            try:
                provider_id = self._messenger.send_text(business, target.channel, target.contact_ref, text)
            except ChannelError as exc:
                self._conversations.update_entry(saved.entry_id, status="failed")
                self._conversations.release_payment(conversation_id, claim)
                logger.warning("pago_confirmado_no_enviado", extra={"tenant": business, "channel": target.channel})
                raise ReplyNotSentError(f"{exc} El pago sigue por confirmar: inténtalo de nuevo.") from exc
            self._conversations.update_entry(saved.entry_id, status="sent", provider_message_id=provider_id)
        self._conversations.finish_payment(conversation_id, claim)

        warnings = []
        if self._memory is not None:
            try:
                self._memory.payment_confirmed(business, target.contact_ref, playground=test)
            except Exception as exc:  # noqa: BLE001 - el mensaje ya salió; se registra el tipo, nunca el número del cliente
                logger.error("pago_confirmado_sin_memoria", extra={"tenant": business, "error": type(exc).__name__})
                warnings.append(MEMORY_NOT_SAVED)
        recorded = None
        if new_sale is not None and self._commerce is not None:
            try:
                recorded = self._commerce.record_sale(business, new_sale, created_by=principal.label)
            except Exception as exc:  # noqa: BLE001 - el mensaje ya salió: el equipo la registra en Ventas
                logger.error("pago_confirmado_sin_venta", extra={"tenant": business, "error": type(exc).__name__})
                warnings.append(SALE_NOT_SAVED)
        logger.info("pago_confirmado", extra={"tenant": business, "channel": target.channel, "sale": recorded is not None})
        summary, messages = self._conversations.thread(conversation_id)
        message = next(item for item in messages if item.id == saved.entry_id)
        return PaymentConfirmed(message, summary, recorded, tuple(warnings))

    def _checked_sale(self, sale: SaleDraft | None, conversation_id: str, *, test: bool) -> NewSale | None:
        if sale is None:
            return None
        if test:
            raise InvalidFieldsError(NO_SALES_IN_TESTS, [FieldIssue("sale", NO_SALES_IN_TESTS)])
        if self._commerce is None:
            raise InvalidFieldsError("Las ventas no están disponibles en este servidor.", [FieldIssue("sale", "Las ventas no están disponibles.")])
        return NewSale.checked(
            customer_name=sale.customer_name, description=sale.description, amount=sale.amount, currency=sale.currency,
            conversation_id=conversation_id,
        )
