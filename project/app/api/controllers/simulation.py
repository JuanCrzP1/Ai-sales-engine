from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_tenant_by_slug_public
from app.api.schemas.simulation import SimulationRequest, SimulationResponse
from app.application.runtime import load_tenant_runtime_yaml
from app.config import settings
from app.infrastructure.db.repository import DBRepository
from app.models import Tenant
from app.services.ai_service import AIService

router = APIRouter(prefix="/simulate", tags=["Simulation"])


@router.post("", response_model=SimulationResponse)
def simulate_message(
    payload: SimulationRequest,
    tenant: Tenant = Depends(get_tenant_by_slug_public),
) -> SimulationResponse:
    if not bool(getattr(settings, "enable_simulation_endpoint", True)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint no disponible")

    repo = DBRepository()
    tenant_db = repo.get_tenant_by_slug(tenant.slug)

    if tenant_db is None:
        return SimulationResponse(
            reply="Este servicio no está disponible.",
            ai_used=False,
            metadata={}
        )

    if tenant_db.get("status") != "active":
        return SimulationResponse(
            reply="Tu servicio está inactivo. Escríbenos para activarlo.",
            ai_used=False,
            metadata={}
        )

    service = AIService()
    runtime_yaml = load_tenant_runtime_yaml(
        str(getattr(tenant, "slug", "") or ""),
        extra_yaml=payload.yaml_config,
    )
    print("YAML ENTRANTE:", runtime_yaml.keys())
    result = service.generate_business_reply(
        tenant=tenant,
        bot_config=None,
        user_message=payload.user_message,
        conversation_history=[],
        faq_results=payload.faq_results,
        yaml_config=runtime_yaml,
        user_id=payload.user_id,
        include_metadata=True,
    )

    if isinstance(result, tuple) and len(result) == 3:
        reply, ai_used, metadata = result
    else:
        reply, ai_used = result
        metadata = {}

    return SimulationResponse(
        reply=str(reply or ""),
        ai_used=bool(ai_used),
        metadata=dict(metadata or {}),
    )
