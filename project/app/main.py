import os

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.api.routes import router
from app.config import get_environment_status, settings, validate_database_url
from app.utils.logger import configure_logger, configure_audit_logger


logger = configure_logger("assistant-api")
audit_logger = configure_audit_logger()


def prepare_application() -> None:
	validate_database_url()
	env_status = get_environment_status()
	logger.info('env_check', extra=env_status)
	logger.info('prompt_runtime_check', extra={'prompt_source': 'single_contract_blocks'})


prepare_application()

app = FastAPI(title=settings.app_name, version=settings.app_version)

# El motor no tiene pantallas: quien abre su dirección (por ejemplo, desde Vercel o GitHub) llega al panel.
PUBLIC_PANEL_URL = "https://ai-sales-engine-panel.vercel.app"


@app.get("/", include_in_schema=False)
def open_the_panel() -> RedirectResponse:
	return RedirectResponse(str(os.getenv("PANEL_URL") or PUBLIC_PANEL_URL).strip(), status_code=307)


@app.get("/health")
def healthcheck() -> dict[str, str]:
	# La plataforma atiende a muchos negocios: lo público no nombra ninguno.
	return {"status": "ok"}


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


def mount_cloud_panel(application: FastAPI) -> None:
	"""En la nube, la API del panel vive bajo `/panel`, con las cuentas de Neon Auth. Sin `NEON_AUTH_URL` no se publica."""
	auth_url = str(os.getenv("NEON_AUTH_URL") or "").strip()
	if not auth_url:
		return
	from app.cloud_panel import build_cloud_panel_api

	application.mount("/panel", build_cloud_panel_api(auth_url))


mount_cloud_panel(app)
