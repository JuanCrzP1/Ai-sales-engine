from fastapi import FastAPI
from fastapi import Request

from app.api.routes import router
from app.config import ACTIVE_TENANT_SLUG, ensure_ai_runtime_ready, get_environment_status, settings
from app.utils.logger import alert_on_audit_event
from app.utils.logger import configure_logger, configure_audit_logger


logger = configure_logger("assistant-api")
audit_logger = configure_audit_logger()


def prepare_application() -> None:
	env_status = get_environment_status()
	logger.info('env_check', extra=env_status)
	if not env_status.get('openrouter_api_key_present') and str(settings.llm_provider or '').strip().lower() == 'openrouter' and bool(settings.enable_ai_responses):
		alert_on_audit_event('ai_runtime_not_ready', **env_status)
	ensure_ai_runtime_ready()
	logger.info('prompt_runtime_check', extra={'prompt_source': 'single_contract_blocks'})
	logger.info('runtime_tenant_profile', extra={'active_tenant': ACTIVE_TENANT_SLUG, 'status': 'active'})


prepare_application()

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.get("/health")
def healthcheck() -> dict[str, str]:
	return {"status": "ok", "tenant": ACTIVE_TENANT_SLUG}


@app.middleware("http")
async def log_requests(request: Request, call_next):
	response = await call_next(request)
	is_production = str(getattr(settings, 'mode', getattr(settings, 'environment', 'development'))).strip().lower() == 'production'
	if response.status_code >= 400:
		logger.warning("%s %s -> %s", request.method, request.url.path, response.status_code)
	elif not is_production:
		logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
	return response


app.include_router(router, prefix=settings.api_prefix)
