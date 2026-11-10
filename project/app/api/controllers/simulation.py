"""Simulación de conversaciones para pruebas internas.

Apagada por defecto. Usa la autenticación de las rutas de administración, una memoria propia que nunca toca la de los
clientes, una configuración sin datos de pago y una respuesta construida campo por campo.
"""
import re
from collections import OrderedDict
from threading import Lock
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_tenant, get_current_user
from app.api.schemas.simulation import SimulationMetadata, SimulationRequest, SimulationResponse
from app.application.ai_pipeline import AIPipeline
from app.application.runtime import BusinessUnavailableError, load_tenant_runtime_yaml
from app.config import settings
from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE, payment_values, redact_payment_values
from app.domain.conversation.memory import MemoryDomainService
from app.infrastructure.persistence.memory_repository import MemoryRepository
from app.models import AdminUser, Tenant
from app.services.ai_service import AIService
from app.utils.logger import logger

router = APIRouter(prefix="/simulate", tags=["Simulation"])

MAX_SIMULATION_SESSIONS = 200
_BUSINESS_SLUG = re.compile(r"[a-z0-9][a-z0-9_-]*")
_METADATA_LABEL = re.compile(r"[A-Za-z0-9_.:-]{1,64}")
_sessions: OrderedDict[tuple[int, str], MemoryDomainService] = OrderedDict()
_sessions_lock = Lock()


def simulation_enabled() -> bool:
    """La ruta solo se registra con la bandera activa y un `JWT_SECRET` propio.

    El secreto por defecto está publicado en el repositorio: con él cualquiera podría firmar un token válido.
    """
    if not settings.enable_simulation_endpoint:
        return False
    secret = str(settings.jwt_secret or "").strip()
    if secret and secret != type(settings).model_fields["jwt_secret"].default:
        return True
    logger.warning(
        "simulation_endpoint_disabled",
        extra={"event": "simulation_endpoint_disabled", "reason": "jwt_secret_not_configured"},
    )
    return False


class _SimulationService(AIService):
    """`AIService` sobre la memoria de la simulación; nunca se construye con la memoria real de los clientes."""

    def __init__(self, memory: MemoryDomainService) -> None:
        self.pipeline = AIPipeline(memory_service=memory)


def _session_memory(admin_id: int, label: str | None) -> MemoryDomainService:
    """Memoria en RAM de una conversación simulada: solo la alcanza quien la creó y desaparece con el proceso."""
    key = (admin_id, str(label or "").strip().lower())
    with _sessions_lock:
        memory = _sessions.get(key)
        if memory is None:
            memory = _sessions[key] = MemoryDomainService(MemoryRepository())
        _sessions.move_to_end(key)
        while len(_sessions) > MAX_SIMULATION_SESSIONS:
            _sessions.popitem(last=False)
    return memory


def _without_payment_values(node: Any, runtime_yaml: dict) -> Any:
    """Copia de la configuración sin datos de pago: el modelo no puede repetir lo que no recibe."""
    if isinstance(node, dict):
        return {key: _without_payment_values(value, runtime_yaml) for key, value in node.items()}
    if isinstance(node, list):
        return [_without_payment_values(value, runtime_yaml) for value in node]
    if isinstance(node, str):
        return redact_payment_values(node, runtime_yaml)
    # Un número sin comillas en un YAML también es un dato de pago.
    if isinstance(node, (int, float)) and str(node) in payment_values(runtime_yaml):
        return REDACTED_PAYMENT_VALUE
    return node


def _metadata_label(value: Any) -> str | None:
    """Solo pasan etiquetas cortas: un objeto o un texto libre en estos campos no sale de la simulación."""
    return value if isinstance(value, str) and _METADATA_LABEL.fullmatch(value) else None


@router.post("", response_model=SimulationResponse)
def simulate_message(
    payload: SimulationRequest,
    current_user: AdminUser = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
) -> SimulationResponse:
    unknown_business = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    slug = str(getattr(tenant, "slug", "") or "")
    # `/auth/register` no valida el identificador: "../tenants/otro" abriría la carpeta de otro negocio.
    if not _BUSINESS_SLUG.fullmatch(slug):
        raise unknown_business
    try:
        runtime_yaml = load_tenant_runtime_yaml(slug)
    except BusinessUnavailableError as exc:
        raise unknown_business from exc

    service = _SimulationService(_session_memory(current_user.id, payload.user_id))
    result = service.generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=payload.user_message,
        conversation_history=[],
        faq_results=payload.faq_results,
        yaml_config=_without_payment_values(runtime_yaml, runtime_yaml),
        user_id=f"simulacion-{current_user.id}",
        include_metadata=True,
    )

    if isinstance(result, tuple) and len(result) == 3:
        reply, ai_used, metadata = result
    else:
        reply, ai_used = result
        metadata = {}

    return SimulationResponse(
        reply=redact_payment_values(str(reply or ""), runtime_yaml),
        ai_used=bool(ai_used),
        metadata=SimulationMetadata(
            source=_metadata_label(metadata.get("source")),
            intent=_metadata_label(metadata.get("intent")),
            conversation_state=_metadata_label(metadata.get("conversation_state")),
            tenant_slug=_metadata_label(metadata.get("tenant_slug")),
        ),
    )
