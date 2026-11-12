"""Experimento de regresión comercial: BASELINE (un commit anterior) frente a CANDIDATE (el árbol de trabajo actual).

Reutiliza lo que ya tiene el laboratorio: la conversación dorada, las métricas del prompt y los evaluadores. Cada lado corre
en su propia copia del código, sin `.env`, con la memoria en RAM y la red bloqueada. Como el motor solo lee lo publicado, cada copia
arma su almacén temporal con los negocios de ejemplo importados de sus YAML, cada uno con una clave de IA ficticia, y el webhook de
WhatsApp se prueba con la firma de Meta. El motor no se toca: solo se sustituye el
transporte hacia el proveedor del modelo, así que se compara la petición exacta que saldría hacia él.

Sin `--live-model` no se llama a ningún modelo: cada turno recibe la respuesta real registrada en
`results/candidate_metrics.json`, la misma para los dos lados. Eso comprueba el motor, no la calidad de una respuesta nueva.
Con `--live-model` se usa el modelo real con la clave de la variable OPENROUTER_API_KEY, nunca la del `.env`. Tiene costo: solo
se ejecuta con autorización del dueño del proyecto.

    python experiments/pricing_lab/run_regression_experiment.py --experiment <id> --baseline <commit>
        [--baseline-python <python>] [--candidate-python <python>] [--tenant <slug>] [--live-model]

Los resultados van a `results/<id>/`. Un experimento existente nunca se sobrescribe.

Este archivo no importa `lab_common` al arrancar, porque ese módulo carga el `.env`: solo lo hacen las copias aisladas.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import io
import json
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from importlib import metadata as package_metadata
from pathlib import Path
from types import SimpleNamespace

LAB_DIR = Path(__file__).resolve().parent
REPO_ROOT = LAB_DIR.parents[1]
PROJECT_DIR = REPO_ROOT / "project"
RESULTS_DIR = LAB_DIR / "results"
REPLAY_SOURCE = RESULTS_DIR / "candidate_metrics.json"

DEFAULT_TENANT = "asesor_ai_prod"
DEFAULT_CHANNEL = "whatsapp"
LAB_USER_ID = "pricing-lab-user"
PROVIDER_HOSTS = {"openrouter.ai"}
PLACEHOLDER_KEY = "clave-ficticia-del-laboratorio"
# Secreto de la app de Meta solo para el laboratorio: el webhook exige la firma `X-Hub-Signature-256` y la sonda firma con este.
LAB_META_APP_SECRET = "secreto-de-meta-del-laboratorio"
SAFE_ENV_NAMES = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "COMSPEC", "PATHEXT", "HOME", "LANG")

# La secuencia de la orden del experimento: la conversación dorada con el punto final de los turnos 1, 2, 3 y 10.
EXPERIMENT_TURNS = [
    "Hola amigo.",
    "Dame más información de lo que venden.",
    "Yo recibo muchos mensajes y no alcanzo a responder.",
    "¿Cómo funciona eso?",
    "¿De verdad eso me puede ayudar a vender más?",
    "¿Por dónde funciona?",
    "¿Y qué precio tiene?",
    "¿Qué incluye?",
    "¿Qué no incluye?",
    "Está caro, pero si me sirve quiero empezar.",
]


def _scripted(text: str, intent: str = "info", **extra) -> dict:
    return {"response": text, "intent": intent, "metadata": extra}


# Tras la conversación dorada, cada negocio recorre estos turnos: objeción, medios de pago y pago reportado.
EXTRA_TURNS = [
    ("¿Esto funciona o es una estafa?", _scripted("Claro.")),
    ("¿Cómo funciona?", _scripted("Claro.")),
    ("Quiero pagar por nequi", _scripted("Listo.", "buy", payment_method="nequi")),
    ("Prefiero el link", _scripted("Listo.", "buy", payment_method="link")),
    ("Ya pagué", _scripted("Gracias.", "buy", payment_status="reportado")),
]

# Ruta apagada por defecto por la orden de seguridad del endpoint de simulación.
EXPECTED_ROUTE_CHANGES = {"POST /api/v1/simulate"}
# La API de administración del sistema anterior, retirada el 11 de noviembre de 2026 (el panel usa `app.admin_api`). Fuera de
# producción los commits anteriores la publicaban: compararse con uno de ellos la muestra como retirada.
EXPECTED_ROUTE_CHANGES |= {
    "POST /api/v1/auth/register", "POST /api/v1/auth/login",
    "GET /api/v1/bot-config/", "PUT /api/v1/bot-config/",
    "GET /api/v1/clients/", "POST /api/v1/clients/",
    "GET /api/v1/connectors/", "GET /api/v1/connectors/{channel}/{provider}", "PUT /api/v1/connectors/{channel}/{provider}",
    "GET /api/v1/conversations/clients/{client_id}", "POST /api/v1/conversations/messages",
    "GET /api/v1/dashboard/metrics",
}
# La raíz del motor lleva al panel (11 de noviembre de 2026): no responde mensajes ni toca a los negocios.
EXPECTED_ROUTE_CHANGES |= {"GET /"}
# La revisión periódica de la atención humana (11 de noviembre de 2026): la IA retoma los chats que nadie atendió. Protegida con
# `CRON_SECRET`; no toca las respuestas.
EXPECTED_ROUTE_CHANGES |= {"GET /api/v1/internal/attention/run", "POST /api/v1/internal/attention/run"}
# La API del asistente (12 de noviembre de 2026): otro sistema conversa con el asistente con una clave de API del negocio.
EXPECTED_ROUTE_CHANGES |= {"POST /api/v1/assistant/messages"}

# Zonas del repositorio, de la más específica a la más general, para clasificar las diferencias de Git.
CHANGE_ZONES = [
    ("Prompts y cliente del modelo", r"project/app/(infrastructure/ai|services/ai_runtime|services/ai|domain/ai)/"),
    ("YAML de los negocios", r"project/config/tenants/[^/]+/[^/]+\.ya?ml$"),
    ("YAML de sistema", r"project/config/system/"),
    ("Dependencias", r"project/requirements"),
    ("Integraciones: conectores y webhook", r"project/app/(connectors/|api/controllers/whatsapp_webhook\.py)"),
    (
        "BusinessConfig y API del panel",
        r"project/(app/(admin_api|business_config_application|domain/business_config|infrastructure/business_config)/"
        r"|app/infrastructure/config/(business_config|legacy_|payment_)"
        r"|config/contracts/|config/tenants/[^/]+/(business-config|engine-settings|payment-values)\.json$|db/migrations/)",
    ),
    ("Flujo de conversación del motor", r"project/app/(application|services|domain|infrastructure)/"),
    ("API del motor", r"project/app/api/"),
    ("Ajustes del motor", r"project/app/config/"),
    ("Documentación y esquemas", r"project/"),
]


def digest(value: object) -> str:
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_no_env(tree: Path) -> None:
    for path in (tree / ".env", tree / "project" / ".env"):
        if path.exists():
            raise SystemExit(f"Se detiene: {path} existe. Esta parte solo corre sobre una copia sin .env.")


# ---------------------------------------------------------------------------
# Orquestación: prepara las copias y lanza cada lado en su propio proceso
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout


def export_commit(commit: str, destination: Path) -> None:
    archive = subprocess.run(["git", "archive", "--format=tar", commit, "project", "experiments/pricing_lab"], cwd=REPO_ROOT, capture_output=True, check=True).stdout
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")


def export_worktree(destination: Path) -> None:
    listed = _git("ls-files", "-co", "--exclude-standard", "-z", "--", "project", "experiments/pricing_lab")
    for relative in filter(None, listed.split("\0")):
        source = REPO_ROOT / relative
        if source.is_file():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def install_script(tree: Path) -> Path:
    ensure_no_env(tree)
    target = tree / "experiments" / "pricing_lab" / Path(__file__).name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, target)
    return target


def child_env(api_key: str, *, live: bool) -> dict[str, str]:
    env = {name: os.environ[name] for name in SAFE_ENV_NAMES if name in os.environ}
    if live:
        env.update({name: os.environ[name] for name in ("OPENROUTER_MODEL", "OPENROUTER_BASE_URL") if os.environ.get(name)})
    env.update(
        {
            "MODE": "test",
            "DATABASE_URL": "sqlite:///:memory:",
            "ENABLE_FILE_LOGS": "0",
            "OPENROUTER_API_KEY": api_key,
            "META_APP_SECRET": LAB_META_APP_SECRET,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return env


def run_child(python: str, script: Path, flag: str, settings: dict, settings_path: Path, env: dict[str, str]) -> None:
    settings_path.write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")
    completed = subprocess.run(
        [python, "-B", str(script), flag, str(settings_path)],
        cwd=script.parents[2],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        # La salida normal puede contener respuestas del motor: solo se muestra el final del error.
        tail = "\n".join(completed.stderr.strip().splitlines()[-12:])
        raise SystemExit(f"Falló {flag} ({settings.get('label', 'informe')}), código {completed.returncode}:\n{tail}")


def replay_replies() -> dict[str, dict]:
    """Respuestas reales ya registradas por el laboratorio, con su intención. No se llama a ningún modelo."""
    recorded = json.loads(REPLAY_SOURCE.read_text(encoding="utf-8"))
    return {
        str(row["turn"]): {"response": row["assistant_reply"], "intent": (row.get("metadata") or {}).get("intent") or "info"}
        for row in recorded.get("conversation") or []
    } | {"_source": {"label": recorded.get("label"), "commit": recorded.get("commit"), "run_at": recorded.get("run_at")}}


def git_changes(baseline: str) -> list[dict]:
    rows = []
    for line in _git("diff", "--name-status", baseline, "--", "project").splitlines():
        status, *paths = line.split("\t")
        rows.append({"status": status[0], "path": paths[-1]})
    untracked = _git("ls-files", "-o", "--exclude-standard", "--", "project").splitlines()
    rows += [{"status": "A", "path": path} for path in untracked]
    uncommitted = set(untracked) | set(_git("diff", "--name-only", "HEAD", "--", "project").splitlines())
    for row in rows:
        last_commit = "" if row["path"] in uncommitted else _git("log", "-1", "--format=%h", f"{baseline}..HEAD", "--", row["path"]).strip()
        row["commit"] = last_commit or "sin commit"
    return sorted(rows, key=lambda row: row["path"])


def orchestrate(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[a-z0-9_]+", args.experiment):
        raise SystemExit("El identificador del experimento solo admite minúsculas, números y guion bajo.")
    output = Path(args.output).resolve() if args.output else RESULTS_DIR / args.experiment
    if output.exists():
        raise SystemExit(f"{output} ya existe: un experimento no se sobrescribe.")

    api_key = PLACEHOLDER_KEY
    if args.live_model:
        api_key = str(os.environ.get("OPENROUTER_API_KEY") or "").strip()
        if not api_key:
            raise SystemExit("--live-model necesita la clave en la variable OPENROUTER_API_KEY. El .env no se lee.")
    env = child_env(api_key, live=bool(args.live_model))

    head = _git("rev-parse", "--short", "HEAD").strip()
    baseline_commit = _git("rev-parse", "--short", args.baseline).strip()
    pending = len(_git("status", "--porcelain").splitlines())
    candidate_ref = f"{head} + cambios sin commit" if pending else head
    replies = replay_replies()

    keep = Path(args.work_dir).resolve() if args.work_dir else None
    temporary = None if keep else tempfile.TemporaryDirectory(prefix="lab-regresion-")
    work = keep or Path(temporary.name)
    try:
        baseline_tree, candidate_tree = work / "baseline", work / "candidate"
        export_commit(baseline_commit, baseline_tree)
        export_worktree(candidate_tree)
        if args.tamper:
            # Solo para el control negativo: una copia alterada a propósito debe aparecer como diferencia.
            tamper = json.loads(args.tamper)
            target = candidate_tree / tamper["path"]
            original = target.read_text(encoding="utf-8")
            if tamper["old"] not in original:
                raise SystemExit(f"Control negativo: no se encontró el texto a alterar en {tamper['path']}.")
            target.write_text(original.replace(tamper["old"], tamper["new"], 1), encoding="utf-8")

        common = {"tenant": args.tenant, "channel": DEFAULT_CHANNEL, "user_id": LAB_USER_ID, "turns": EXPERIMENT_TURNS, "replies": replies, "live": bool(args.live_model)}
        sides = (("baseline", baseline_tree, baseline_commit, args.baseline_python), ("candidate", candidate_tree, candidate_ref, args.candidate_python))
        for label, tree, reference, python in sides:
            print(f"[{label}] {reference} | {python}")
            run_child(python, install_script(tree), "--internal-capture", {**common, "label": label, "commit": reference, "output": str(work / f"{label}.json")}, work / f"{label}.settings.json", env)

        run_child(
            args.candidate_python,
            install_script(candidate_tree),
            "--internal-report",
            {
                "experiment": args.experiment,
                "baseline_commit": baseline_commit,
                "baseline_note": args.baseline_note,
                "output": str(output),
                "baseline_raw": str(work / "baseline.json"),
                "candidate_raw": str(work / "candidate.json"),
                "changes": git_changes(baseline_commit),
                "replay_source": replies["_source"],
                "live": bool(args.live_model),
                "tenant": args.tenant,
            },
            work / "report.settings.json",
            env,
        )
    finally:
        if temporary is not None:
            temporary.cleanup()
    print((output / "summary.txt").read_text(encoding="utf-8"))
    (output / "summary.txt").unlink()
    return 0


# ---------------------------------------------------------------------------
# Captura: corre dentro de una copia aislada, con el código de ese lado
# ---------------------------------------------------------------------------


def install_network_guard(allowed_hosts: set[str]) -> list[str]:
    """Bloquea toda conexión fuera de este equipo salvo el proveedor autorizado; registra cada intento."""
    attempts: list[str] = []
    loopback = {"127.0.0.1", "::1", "localhost"}
    allowed_addresses = set(loopback)
    real_connect, real_lookup = socket.socket.connect, socket.getaddrinfo

    def lookup(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else str(host)
        if name in loopback or name in allowed_hosts:
            found = real_lookup(host, *args, **kwargs)
            allowed_addresses.update(item[4][0] for item in found)
            return found
        attempts.append(name)
        raise OSError("red bloqueada por el laboratorio")

    def connect(self, address):
        host = str(address[0]) if isinstance(address, tuple) else "socket"
        if host in allowed_addresses:
            return real_connect(self, address)
        attempts.append(host)
        raise OSError("red bloqueada por el laboratorio")

    socket.getaddrinfo = lookup
    socket.socket.connect = connect
    return attempts


class _RecordedResponse:
    status_code = 200

    def __init__(self, content: str) -> None:
        self._body = {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        self.text = json.dumps(self._body, ensure_ascii=False)

    def json(self) -> dict:
        return self._body

    def raise_for_status(self) -> None:
        return None


class ModelTransport:
    """Reemplaza `requests.post` en el cliente del modelo: registra la petición y responde lo preparado, o la deja pasar en modo real."""

    def __init__(self, real_post=None) -> None:
        self.real_post = real_post
        self.calls: list[dict] = []
        self.reply: dict | None = None

    def start_turn(self, reply: dict | None) -> None:
        self.calls = []
        self.reply = reply

    def post(self, url, headers=None, json=None, timeout=None, **kwargs):  # noqa: A002 - misma firma que requests.post
        call = {"url": url, "payload": json}
        self.calls.append(call)
        if self.real_post is not None:
            response = self.real_post(url, headers=headers, json=json, timeout=timeout, **kwargs)
            call["provider_status"] = response.status_code
            return response
        if self.reply is None:
            raise RuntimeError("El motor pidió al modelo un turno sin respuesta preparada.")
        return _RecordedResponse(_dumps(self.reply))


def _dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _request_record(call: dict, build_prompt_metrics) -> dict:
    payload = call["payload"] if isinstance(call.get("payload"), dict) else {}
    messages = payload.get("messages") or []
    prompt = "\n".join(str(item.get("content") or "") for item in messages if item.get("role") == "system")
    return {
        "url": call.get("url"),
        "model": payload.get("model"),
        "temperature": payload.get("temperature"),
        "max_tokens": payload.get("max_tokens"),
        "top_p": payload.get("top_p"),
        "roles": [item.get("role") for item in messages],
        "user_content": "\n".join(str(item.get("content") or "") for item in messages if item.get("role") == "user"),
        "prompt": prompt,
        "prompt_sha256": digest(prompt),
        "prompt_metrics": build_prompt_metrics(prompt),
    }


def run_conversation(*, service, model, load_runtime, tenant, channel: str, user_id: str, turns: list[tuple[str, dict | None]], build_prompt_metrics) -> list[dict]:
    """Los mismos pasos de `run_golden_conversations.py`: el contexto de cada turno sale de la memoria del motor, como en producción."""
    rows = []
    for number, (message, reply) in enumerate(turns, start=1):
        model.start_turn(reply)
        runtime_yaml = load_runtime(tenant.slug, channel=channel)
        response, ai_used, metadata = service.generate_business_reply(
            tenant=tenant,
            bot_config=None,
            user_message=message,
            conversation_history=[],
            faq_results=[],
            yaml_config=runtime_yaml,
            user_id=user_id,
            include_metadata=True,
        )
        metadata = metadata if isinstance(metadata, dict) else {}
        rows.append(
            {
                "turn": number,
                "user_message": message,
                "assistant_reply": str(response or ""),
                "ai_used": bool(ai_used),
                "intent": metadata.get("intent"),
                "source": metadata.get("source"),
                "conversation_state": metadata.get("conversation_state"),
                "memory_sha256": digest(metadata.get("memory_state")),
                "metadata_sha256": digest(metadata),
                "requests": [_request_record(call, build_prompt_metrics) for call in model.calls],
            }
        )
    return rows


def _probe_application() -> tuple[object, dict, str]:
    from fastapi.testclient import TestClient

    from app.config import settings as app_settings
    from app.main import app as application

    client = TestClient(application)
    health = client.get("/health")
    routes = sorted(
        f"{method} {route.path}"
        for route in application.routes
        for method in (getattr(route, "methods", None) or ())
        if method not in {"HEAD", "OPTIONS"}
    )
    return client, {"health_status": health.status_code, "health": health.json(), "routes": routes}, app_settings.api_prefix


def _probe_webhook(client, model, api_prefix: str, tenant_slug: str) -> dict:
    """Mensaje entrante con un número ficticio hasta la respuesta que se enviaría. El envío a WhatsApp se intercepta: nada sale."""
    import app.api.controllers.whatsapp_webhook as webhook

    sent: list[str] = []
    webhook.get_tenant_by_phone_number_id = lambda _phone_number_id: {"slug": tenant_slug, "id": tenant_slug, "status": "active"}
    webhook.WhatsAppService = lambda: SimpleNamespace(send_message=lambda **kwargs: sent.append(str(kwargs.get("message") or "")))
    rows = []
    for text, reply in (("Hola", None), ("¿Y qué precio tiene?", _scripted("Respuesta de prueba del webhook."))):
        model.start_turn(reply)
        payload = {
            "entry": [{"changes": [{"value": {"metadata": {"phone_number_id": "000000000000000"}, "messages": [{"from": "570000000000", "id": "wamid.laboratorio", "type": "text", "text": {"body": text}}]}}]}]
        }
        # Firmado como lo firma Meta: sin firma válida, el webhook rechaza el mensaje antes de llegar al motor.
        body = json.dumps(payload).encode("utf-8")
        signature = "sha256=" + hmac.new(LAB_META_APP_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
        response = client.post(f"{api_prefix}/whatsapp/webhook", content=body, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature})
        rows.append({"message": text, "status": response.status_code, "body": response.json(), "model_calls": len(model.calls), "prompt_sha256": [digest(str((call["payload"].get("messages") or [{}])[0].get("content") or "")) for call in model.calls]})
    return {"turns": rows, "sent": sent}


def _prepare_platform_store() -> str:
    """El almacén de esta copia, como en producción: los negocios de ejemplo importados y publicados (desde sus JSON; una copia
    anterior al 11 de noviembre de 2026, desde sus YAML).

    El motor solo lee lo publicado (desde la Fase 1), así que cada lado necesita su almacén. Se crea dentro de la copia, con su
    propio código y su propia clave, antes de que nada importe la configuración del motor. Devuelve cómo se armó."""
    from cryptography.fernet import Fernet

    path = REPO_ROOT / ".almacen-laboratorio" / "negocios.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path.as_posix()}"
    os.environ["BUSINESS_CONFIG_DATABASE_URL"] = url
    os.environ["BUSINESS_CONFIG_SECRETS_KEY"] = Fernet.generate_key().decode()
    try:
        from app.infrastructure.business_config.database import (
            build_business_config_service,
            create_business_config_engine,
            create_local_schema,
        )
    except ImportError:
        return "YAML (código anterior al almacén)"
    source = "sus JSON"
    try:
        from app.infrastructure.business_config.example_businesses import import_examples as importer
    except ImportError:
        # Código anterior al retiro de los YAML: los ejemplos se importan de sus YAML.
        from app.infrastructure.config.config_service import ConfigService
        from app.infrastructure.config.legacy_store_migration import import_all

        source = "sus YAML"

        def importer(service):
            return import_all(service, ConfigService())

    engine = create_business_config_engine(url)
    create_local_schema(engine)
    report = importer(build_business_config_service(engine, secrets_key=os.environ["BUSINESS_CONFIG_SECRETS_KEY"]))
    # Cada negocio responde con su propia clave de IA (la plataforma no tiene ninguna). Aquí todos reciben la del laboratorio: la
    # ficticia, que nunca sale porque la red está bloqueada, o la real con `--live-model`.
    from app.infrastructure.business_config.ai_settings_store import AISettingsStore

    keys = AISettingsStore(engine, os.environ["BUSINESS_CONFIG_SECRETS_KEY"])
    for slug in report.created:
        keys.save_ai_settings(slug, model=None, api_key=os.environ["OPENROUTER_API_KEY"], clear_key=False)
    engine.dispose()
    return f"lo publicado en un almacén temporal ({len(report.created)} negocios importados de {source}, cada uno con su clave)"


def capture(settings: dict) -> int:
    ensure_no_env(REPO_ROOT)
    live = bool(settings["live"])
    attempts = install_network_guard(PROVIDER_HOSTS if live else set())
    logging.disable(logging.CRITICAL)
    for path in (str(LAB_DIR), str(PROJECT_DIR)):
        sys.path.insert(0, path)
    config_source = _prepare_platform_store()

    import requests

    model = ModelTransport(requests.post if live else None)
    requests.post = model.post

    from lab_common import build_prompt_metrics, tenant_handle
    from lab_config import GOLDEN_TURNS

    if [turn.rstrip(".") for turn in settings["turns"]] != GOLDEN_TURNS:
        raise SystemExit("La secuencia del experimento ya no coincide con GOLDEN_TURNS.")

    from app.application.runtime import load_tenant_runtime_yaml
    from app.infrastructure.ai.prompting.builder.prompt_builder import PromptBuilderService

    subscription_stubbed = False
    try:
        # Solo existe en commits anteriores a su retiro: se da por activa la suscripción, que no influye en la respuesta.
        from app.application.pipeline.saas_guard import SaaSGuard

        SaaSGuard.check_access = lambda self, _key: (True, None)
        SaaSGuard.record_usage = lambda self, _key: None
        subscription_stubbed = True
    except ImportError:
        pass

    from app.services.ai_service import GLOBAL_MEMORY_REPOSITORY, AIService

    service = AIService()
    tenant_slug, channel, user_id = settings["tenant"], settings["channel"], settings["user_id"]
    replies = settings["replies"]
    turns = [(message, None if live else replies.get(str(number))) for number, message in enumerate(settings["turns"], start=1)]
    conversation = run_conversation(service=service, model=model, load_runtime=load_tenant_runtime_yaml, tenant=tenant_handle(tenant_slug), channel=channel, user_id=user_id, turns=turns, build_prompt_metrics=build_prompt_metrics)

    def snapshot(slug: str) -> tuple[str, dict]:
        runtime_yaml = load_tenant_runtime_yaml(slug, channel=channel)
        runtime_yaml["user_id"] = LAB_USER_ID
        prompt_text, _metadata, _context = PromptBuilderService().build(client_config_id=slug, user_message=GOLDEN_TURNS[0], yaml_config=runtime_yaml, faq_results=[], progression_rules=None)
        return str(prompt_text or ""), build_prompt_metrics(str(prompt_text or ""))

    prompt_text, prompt_metrics = snapshot(tenant_slug)

    tenants: dict[str, dict] = {}
    if not live:
        scenario = [(message, _scripted("Respuesta simulada.")) for message in GOLDEN_TURNS] + EXTRA_TURNS
        # Cada negocio de ejemplo: su `business-config.json` o, en commits anteriores al retiro de los YAML, su `pricing.yaml`.
        examples = (PROJECT_DIR / "config" / "tenants").iterdir()
        for directory in sorted(path for path in examples if (path / "business-config.json").is_file() or (path / "pricing.yaml").is_file()):
            slug = directory.name
            runtime = load_tenant_runtime_yaml(slug, channel=channel)
            rows = run_conversation(service=service, model=model, load_runtime=load_tenant_runtime_yaml, tenant=tenant_handle(slug), channel=channel, user_id=f"regresion-{slug}", turns=scenario, build_prompt_metrics=build_prompt_metrics)
            tenants[slug] = {
                "runtime_sha256": digest(runtime),
                "snapshot_sha256": digest(snapshot(slug)[0]),
                "turns": [
                    {
                        "turn": row["turn"],
                        "reply_sha256": digest(row["assistant_reply"]),
                        "ai_used": row["ai_used"],
                        "intent": row["intent"],
                        "source": row["source"],
                        "metadata_sha256": row["metadata_sha256"],
                        "prompt_sha256": [item["prompt_sha256"] for item in row["requests"]],
                        "models": [item["model"] for item in row["requests"]],
                    }
                    for row in rows
                ],
            }

    client, application, api_prefix = _probe_application()
    webhook = _probe_webhook(client, model, api_prefix, tenant_slug) if not live else {}

    payload = {
        "label": settings["label"],
        "storage_slot": settings["label"],
        "tenant_slug": tenant_slug,
        "channel": channel,
        "user_id": user_id,
        "run_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "commit": settings["commit"],
        "seed_message": GOLDEN_TURNS[0],
        "prompt": prompt_text,
        "prompt_sha256": digest(prompt_text),
        "prompt_metrics": prompt_metrics,
        "conversation": conversation,
        "tenants": tenants,
        "application": application,
        "webhook": webhook,
        "environment": {
            "python": platform.python_version(),
            "dependencies": {name: package_metadata.version(name) for name in ("cryptography", "pydantic-settings", "requests", "fastapi", "pydantic", "SQLAlchemy", "PyYAML", "httpx")},
            "config_source": config_source,
            "memory_repository": type(GLOBAL_MEMORY_REPOSITORY).__name__,
            "subscription_guard_stubbed": subscription_stubbed,
            "env_file_present": False,
        },
        "network_attempts": attempts,
    }
    Path(settings["output"]).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return 0


# ---------------------------------------------------------------------------
# Informe: corre en la copia del candidato; usa los evaluadores del laboratorio y redacta los datos de pago
# ---------------------------------------------------------------------------


def _delta_line(name: str, base: int, candidate: int) -> str:
    delta = candidate - base
    return f"- {name}: baseline={base}, candidate={candidate}, delta={'+' if delta > 0 else ''}{delta}"


def _yes(value: bool) -> str:
    return "Sí" if value else "No"


REQUEST_FIELDS = ("url", "model", "temperature", "max_tokens", "top_p", "roles", "user_content", "prompt_sha256")
TURN_FIELDS = ("assistant_reply", "ai_used", "intent", "source", "conversation_state", "memory_sha256", "metadata_sha256")


def turn_differences(base: dict, candidate: dict) -> list[str]:
    found = [field for field in TURN_FIELDS if base.get(field) != candidate.get(field)]
    base_requests, candidate_requests = base.get("requests") or [], candidate.get("requests") or []
    if len(base_requests) != len(candidate_requests):
        found.append("número de llamadas al modelo")
    for left, right in zip(base_requests, candidate_requests):
        found += [f"petición.{field}" for field in REQUEST_FIELDS if left.get(field) != right.get(field)]
    return found


def tenant_differences(base: dict, candidate: dict) -> list[str]:
    found = [field for field in ("runtime_sha256", "snapshot_sha256") if base.get(field) != candidate.get(field)]
    base_turns, candidate_turns = base.get("turns") or [], candidate.get("turns") or []
    if len(base_turns) != len(candidate_turns):
        found.append("número de turnos")
    for left, right in zip(base_turns, candidate_turns):
        found += [f"turno {left['turn']}: {key}" for key in left if left[key] != right.get(key)]
    return found


def classify_changes(changes: list[dict]) -> list[tuple[str, list[dict]]]:
    zones: dict[str, list[dict]] = {name: [] for name, _pattern in CHANGE_ZONES}
    for change in changes:
        for name, pattern in CHANGE_ZONES:
            if re.match(pattern, change["path"]):
                zones[name].append(change)
                break
    return list(zones.items())


def report(settings: dict) -> int:
    ensure_no_env(REPO_ROOT)
    logging.disable(logging.CRITICAL)
    for path in (str(LAB_DIR), str(PROJECT_DIR)):
        sys.path.insert(0, path)

    from evaluate_conversations import enrich_metrics_payload

    from app.domain.business_config.payment_data import REDACTED_PAYMENT_VALUE
    from app.infrastructure.business_config.example_businesses import example_slugs, load_example

    # Los datos de pago de los negocios de ejemplo (los mismos que tenían sus YAML) no se escriben en el informe.
    secrets: set[str] = {value for slug in example_slugs() for value in load_example(slug).payment_values.values() if value}
    ordered_secrets = sorted(secrets, key=len, reverse=True)

    def redact(value):
        if isinstance(value, str):
            for secret in ordered_secrets:
                value = value.replace(secret, REDACTED_PAYMENT_VALUE)
            return value
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    baseline = json.loads(Path(settings["baseline_raw"]).read_text(encoding="utf-8"))
    candidate = json.loads(Path(settings["candidate_raw"]).read_text(encoding="utf-8"))
    live = bool(settings["live"])
    for side in (baseline, candidate):
        enrich_metrics_payload(side)

    # --- Comparación, sobre los datos sin redactar
    # Con un modelo real el texto varía entre ejecuciones, y el prompt de cada turno incluye las respuestas anteriores: en cuanto
    # dos respuestas difieren, los prompts siguientes ya no son comparables. Eso no es una diferencia del motor.
    turn_rows = []
    diverged = False
    for left, right in zip(baseline["conversation"], candidate["conversation"]):
        differences = turn_differences(left, right)
        comparable = not (live and diverged)
        if live:
            differences = [item for item in differences if comparable and (item == "número de llamadas al modelo" or item.startswith("petición."))]
            diverged = diverged or left["assistant_reply"] != right["assistant_reply"]
        turn_rows.append({"turn": left["turn"], "differences": differences, "comparable": comparable})
    conversation_identical = all(not row["differences"] for row in turn_rows) and len(baseline["conversation"]) == len(candidate["conversation"])

    calls_base = sum(len(row["requests"]) for row in baseline["conversation"])
    compared_calls = prompts_equal = 0
    for row, left, right in zip(turn_rows, baseline["conversation"], candidate["conversation"]):
        for one, other in zip(left["requests"], right["requests"]) if row["comparable"] else ():
            compared_calls += 1
            prompts_equal += one["prompt_sha256"] == other["prompt_sha256"]
    replies_equal = sum(1 for left, right in zip(baseline["conversation"], candidate["conversation"]) if left["assistant_reply"] == right["assistant_reply"])
    snapshot_identical = baseline["prompt_sha256"] == candidate["prompt_sha256"]

    tenant_rows = []
    for slug in sorted(set(baseline["tenants"]) | set(candidate["tenants"])):
        left, right = baseline["tenants"].get(slug, {}), candidate["tenants"].get(slug, {})
        tenant_rows.append({"slug": slug, "turns": len(right.get("turns") or []), "calls": sum(len(item["prompt_sha256"]) for item in right.get("turns") or []), "runtime": left.get("runtime_sha256") == right.get("runtime_sha256"), "snapshot": left.get("snapshot_sha256") == right.get("snapshot_sha256"), "differences": tenant_differences(left, right)})
    tenants_identical = all(not row["differences"] for row in tenant_rows)

    webhook_identical = baseline["webhook"] == candidate["webhook"]
    base_routes, candidate_routes = set(baseline["application"]["routes"]), set(candidate["application"]["routes"])
    routes_removed, routes_added = sorted(base_routes - candidate_routes), sorted(candidate_routes - base_routes)
    unexpected_routes = (set(routes_removed) | set(routes_added)) - EXPECTED_ROUTE_CHANGES
    health_identical = baseline["application"]["health"] == candidate["application"]["health"] and candidate["application"]["health_status"] == 200
    network_attempts = baseline["network_attempts"] + candidate["network_attempts"]
    engine_identical = conversation_identical and snapshot_identical and tenants_identical and webhook_identical and not unexpected_routes and health_identical and not network_attempts

    zones = classify_changes(settings["changes"])
    zone_count = {name: len(items) for name, items in zones}

    # --- Archivos del experimento, siempre redactados
    output = Path(settings["output"])
    output.mkdir(parents=True)
    for label, side in (("baseline", baseline), ("candidate", candidate)):
        (output / f"{label}_prompt.txt").write_text(redact(side["prompt"]) + "\n", encoding="utf-8")
        stored = redact({key: value for key, value in side.items() if key != "prompt"})
        stored["reply_mode"] = "modelo_real" if live else "reproducida"
        stored["score_is_control"] = not live
        (output / f"{label}_metrics.json").write_text(json.dumps(stored, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    source = settings["replay_source"]
    first_request = next((item for row in candidate["conversation"] for item in row["requests"]), {})
    status = "COMPLETO" if live else "PARCIAL: faltan las respuestas nuevas del modelo real, que necesitan autorización"
    base_env, candidate_env = baseline["environment"], candidate["environment"]
    changed_dependencies = [f"{name} {base_env['dependencies'][name]} → {candidate_env['dependencies'][name]}" for name in base_env["dependencies"] if base_env["dependencies"][name] != candidate_env["dependencies"][name]]

    def identical_text(flag: bool, ending: str = "o") -> str:
        return f"idéntic{ending}" if flag else "**DISTINTO**"

    def count_text(count: int, singular: str, plural: str) -> str:
        return f"{count} {singular if count == 1 else plural}"


    lines = [
        f"# Experimento {settings['experiment']}",
        "",
        f"- fecha: {candidate['run_at']}",
        f"- estado: {status}",
        f"- baseline: `{baseline['commit']}`{', ' + settings['baseline_note'] if settings['baseline_note'] else ''}",
        f"- candidate: `{candidate['commit']}`, estado actual",
        f"- negocio: {settings['tenant']} | canal: {candidate['channel']}",
        "",
        "## Resultado global",
        "",
        "| Comprobación | Resultado |",
        "|---|---|",
        f"| Prompt de referencia del laboratorio | {identical_text(snapshot_identical)} |",
        f"| Prompts de la conversación de 10 turnos | {prompts_equal} de {compared_calls} idénticos |",
        f"| Peticiones al proveedor (modelo, temperatura, límite, mensajes) | {identical_text(conversation_identical, "as")} |",
    ]
    if not live:
        lines += [
            f"| Respuestas finales tras los filtros del motor | {replies_equal} de {len(baseline['conversation'])} idénticas |",
            f"| Configuración, prompts y respuestas de {len(tenant_rows)} negocios ({sum(row['turns'] for row in tenant_rows)} turnos) | {sum(1 for row in tenant_rows if not row['differences'])} de {len(tenant_rows)} idénticos |",
            f"| Webhook de WhatsApp con número ficticio, sin envío real | {identical_text(webhook_identical)} |",
        ]
    lines += [
        f"| Arranque del motor y `/health` | {'correcto e idéntico' if health_identical else '**DISTINTO**'} |",
        f"| Rutas del motor | {count_text(len(routes_removed), 'retirada', 'retiradas')}, {count_text(len(routes_added), 'nueva', 'nuevas')}, {len(unexpected_routes)} sin explicar |",
        f"| Intentos de salir a la red | {len(network_attempts)} |",
        "",
        "## Configuración",
        "",
        "| | Baseline | Candidate |",
        "|---|---|---|",
        f"| Código | `{baseline['commit']}` | `{candidate['commit']}` |",
        f"| Python | {base_env['python']} | {candidate_env['python']} |",
    ]
    lines += [f"| {name} | {base_env['dependencies'][name]} | {candidate_env['dependencies'][name]} |" for name in base_env["dependencies"]]
    lines += [
        f"| Modelo pedido | {next((item['model'] for row in baseline['conversation'] for item in row['requests']), '-')} | {first_request.get('model', '-')} |",
        f"| Temperatura y límite de tokens | {next((item['temperature'] for row in baseline['conversation'] for item in row['requests']), '-')} y {next((item['max_tokens'] for row in baseline['conversation'] for item in row['requests']), '-')} | {first_request.get('temperature', '-')} y {first_request.get('max_tokens', '-')} |",
        f"| Fuente de configuración | {base_env.get('config_source', 'YAML')} | {candidate_env.get('config_source', 'YAML')} |",
        f"| Memoria | {base_env['memory_repository']}, en RAM sin PostgreSQL | {candidate_env['memory_repository']}, en RAM sin PostgreSQL |",
        f"| Control de suscripción | {'existe; se da por activa para poder conversar' if base_env['subscription_guard_stubbed'] else 'no existe'} | {'existe; se da por activa para poder conversar' if candidate_env['subscription_guard_stubbed'] else 'retirado'} |",
        f"| `.env` | no existe en la copia | no existe en la copia |",
        "",
        "El modelo pedido sale de la configuración de sistema del repositorio, porque el `.env` no se leyó. Si el `.env` real define otro, se aplica igual a los dos lados.",
        "",
        "## Diferencias detectadas",
        "",
        "### En el código, según Git",
        "",
        "| Zona | Archivos distintos |",
        "|---|---|",
    ]
    lines += [f"| {name} | {count} |" for name, count in zone_count.items()]
    lines += ["", "Archivos que pueden afectar al motor:", ""]
    for name, items in zones:
        if items and name not in {"BusinessConfig y API del panel", "Documentación y esquemas"}:
            lines += [f"- {name}:"] + [f"  - `{item['path']}` ({item['status']}, {item['commit']})" for item in items]
    lines += [
        "",
        "(A: nuevo, M: modificado, D: eliminado; entre paréntesis, el último commit que lo tocó.)",
        "",
        "### En el comportamiento",
        "",
    ]
    behaviour: list[str] = []
    for row in turn_rows:
        if row["differences"]:
            behaviour.append(f"- Turno {row['turn']}: {', '.join(row['differences'])}.")
    for row in tenant_rows:
        if row["differences"]:
            behaviour.append(f"- {row['slug']}: {', '.join(row['differences'][:6])}.")
    if not snapshot_identical:
        behaviour.append("- El prompt de referencia del laboratorio es distinto.")
    if not webhook_identical:
        behaviour.append("- El webhook de WhatsApp se comporta distinto.")
    behaviour += [f"- Ruta retirada: `{route}`{' (apagada por defecto por la orden de seguridad del endpoint de simulación)' if route in EXPECTED_ROUTE_CHANGES else ''}." for route in routes_removed]
    behaviour += [f"- Ruta nueva: `{route}`." for route in routes_added]
    if changed_dependencies:
        behaviour.append(f"- Dependencias con otra versión, sin efecto medido en lo anterior: {', '.join(changed_dependencies)}.")
    lines += behaviour or ["- Ninguna."]
    lines += [
        "",
        "## Métricas del prompt",
        "",
        "Prompt de referencia, medido como en `generate_prompt_snapshot.py`.",
        "",
    ]
    for key, name in (("chars", "chars"), ("lines", "lines"), ("estimated_tokens", "estimated_tokens"), ("pricing_block_chars", "pricing_block_chars")):
        lines.append(_delta_line(name, int(baseline["prompt_metrics"][key]), int(candidate["prompt_metrics"][key])))
    lines += ["", "## Score comercial", ""]
    if not live:
        lines += [
            f"**Score de control.** Respuestas reales grabadas por el laboratorio ({source.get('label')}, {source.get('run_at')}, commit {source.get('commit')}), "
            "reproducidas en los dos lados. Sirve para comprobar que el motor las trata igual. No evalúa una respuesta nueva ni sustituye la evaluación humana.",
            "",
        ]
    lines.append(_delta_line("commercial_score", int(baseline["commercial_score"]), int(candidate["commercial_score"])))
    for key in ("price_turns", "includes_turns", "not_includes_turns", "roi_turns", "cta_turns", "objection_turns", "closing_progress_turns"):
        lines.append(_delta_line(key, int(baseline["behavior_metrics"][key]), int(candidate["behavior_metrics"][key])))
    lines.append("")

    evaluations = (("Precio", "price"), ("Incluye", "includes"), ("No incluye", "not_includes"), ("ROI", "roi"), ("CTA", "cta"), ("Manejo de objeciones", "objection_handling"), ("Avance al cierre", "closing_progress"))
    for index, (left, right) in enumerate(zip(baseline["conversation"], candidate["conversation"])):
        left_eval, right_eval = baseline["turn_evaluations"][index], candidate["turn_evaluations"][index]
        lines += [
            f"# Turno {left['turn']} — {left['user_message']}",
            "",
            "## Baseline",
            redact(left["assistant_reply"]).strip() or "Sin respuesta.",
            "",
            "## Candidate",
            redact(right["assistant_reply"]).strip() or "Sin respuesta.",
            "",
            "### Métricas del prompt",
        ]
        if not left["requests"] and not right["requests"]:
            lines.append("- Sin llamada al modelo: es el saludo configurado del negocio.")
        for one, other in zip(left["requests"], right["requests"]):
            for key in ("chars", "lines", "estimated_tokens", "pricing_block_chars"):
                lines.append(_delta_line(key, int(one["prompt_metrics"][key]), int(other["prompt_metrics"][key])))
            if turn_rows[index]["comparable"]:
                lines.append(f"- Prompt idéntico: {_yes(one['prompt_sha256'] == other['prompt_sha256'])} (sha256 {other['prompt_sha256'][:12]})")
            else:
                lines.append("- Prompt no comparable: incluye respuestas anteriores del modelo, que ya son distintas.")
        lines += ["", "### Evaluación automática"]
        lines += [f"- {name}: baseline={_yes(bool(left_eval[key]))}, candidate={_yes(bool(right_eval[key]))}" for name, key in evaluations]
        lines += [
            f"- Intención: baseline={left['intent']}, candidate={right['intent']}",
            f"- Origen: baseline={left['source']}, candidate={right['source']}",
            f"- Diferencias del motor: {', '.join(turn_rows[index]['differences']) or 'ninguna'}",
            "",
            "### Veredicto Manual",
            "- [ ] Mejoró",
            "- [ ] Igual",
            "- [ ] Empeoró",
            "",
        ]

    if not live:
        lines += [
            "# Regresión del motor en todos los negocios",
            "",
            "Cada negocio recorre la conversación dorada más objeción, medios de pago y pago reportado, con respuestas simuladas. Se comparan huellas: este archivo no guarda sus datos.",
            "",
            "| Negocio | Configuración | Prompt de referencia | Turnos | Llamadas al modelo | Resultado |",
            "|---|---|---|---|---|---|",
        ]
        lines += [f"| {row['slug']} | {identical_text(row['runtime'])} | {identical_text(row['snapshot'])} | {row['turns']} | {row['calls']} | {'sin diferencias' if not row['differences'] else '**con diferencias**'} |" for row in tenant_rows]
        lines.append("")

    lines += [
        "# Observaciones y limitaciones",
        "",
    ]
    if not live:
        lines += [
            "- **No se llamó a ningún modelo.** Las respuestas de los turnos 2 a 10 son reales pero grabadas: no muestran lo que el modelo contestaría hoy.",
            "- Lo que se puede afirmar: a igual respuesta del modelo, el motor actual y el anterior construyen los mismos prompts, guardan el mismo estado y entregan el mismo texto.",
            "- Lo que queda sin medir: el texto nuevo del modelo. Además, varía de una ejecución a otra aunque el prompt sea idéntico, así que por sí solo no probaría una regresión.",
            f"- Para completarlo: `--live-model`, con autorización, hace hasta {calls_base * 2} llamadas por lado. El primer prompt no pide JSON, así que con un modelo real el motor suele repetir cada turno.",
        ]
    else:
        lines += ["- El modelo es real: el texto varía entre ejecuciones aunque el prompt sea idéntico. Esa variación no es una diferencia del motor."]
    lines += [
        "- Los turnos 1, 2, 3 y 10 llevan el punto final de la orden del experimento. La tabla de negocios usa `GOLDEN_TURNS`, sin ese punto.",
        "- La memoria corre en RAM, sin PostgreSQL: el contexto se conserva entre turnos con el mismo repositorio, sin su almacenamiento real.",
        "- Los evaluadores automáticos buscan palabras: no sustituyen el veredicto manual de cada turno, que queda sin marcar.",
        "- El motor se ejecutó con `MODE=test` y SQLite en memoria en los dos lados. Los datos de pago están redactados en todos los archivos del experimento.",
        "",
        "# Veredicto",
        "",
    ]
    if engine_identical:
        lines.append("**Sin regresión del motor en lo medido.** " + ("Falta la comparación con respuestas nuevas del modelo real." if not live else "Falta el veredicto manual de cada turno."))
    else:
        lines.append("**Hay diferencias que revisar.** Están listadas en «Diferencias detectadas».")
    lines += [
        "",
        "# Cómo repetirlo",
        "",
        "```",
        f"python experiments/pricing_lab/run_regression_experiment.py --experiment <id nuevo> --baseline {settings['baseline_commit']} \\",
        "    --baseline-python <python con los requisitos de ese commit> --candidate-python <python con los requisitos actuales>",
        "```",
        "",
        "Con respuestas nuevas del modelo, solo con autorización: añade `--live-model` y define `OPENROUTER_API_KEY` y `OPENROUTER_MODEL` en la consola.",
        "",
    ]

    (output / "comparison_baseline_vs_candidate.md").write_text("\n".join(lines), encoding="utf-8")

    # Comprobación final: ningún dato de pago en lo escrito.
    for path in output.iterdir():
        content = path.read_text(encoding="utf-8")
        if any(secret in content for secret in ordered_secrets):
            shutil.rmtree(output)
            raise SystemExit("Un archivo del experimento contenía un dato de pago: se borró el experimento.")

    summary = [
        f"experimento: {settings['experiment']}",
        f"prompts idénticos: {prompts_equal}/{compared_calls} | referencia: {snapshot_identical} | negocios sin diferencias: {sum(1 for row in tenant_rows if not row['differences'])}/{len(tenant_rows)}",
        f"respuestas idénticas: {replies_equal}/{len(baseline['conversation'])} | webhook: {webhook_identical} | health: {health_identical}",
        f"rutas retiradas: {routes_removed} | nuevas: {routes_added}",
        f"intentos de red: {network_attempts}",
        f"motor sin diferencias: {engine_identical}",
        f"resultados: {output}",
    ]
    (output / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experiment", help="Identificador del experimento, con su fecha")
    parser.add_argument("--baseline", help="Commit del estado anterior")
    parser.add_argument("--baseline-note", default="", help="Qué representa ese commit, para el informe")
    parser.add_argument("--baseline-python", default=sys.executable, help="Python con las dependencias del commit anterior")
    parser.add_argument("--candidate-python", default=sys.executable, help="Python con las dependencias actuales")
    parser.add_argument("--tenant", default=DEFAULT_TENANT)
    parser.add_argument("--live-model", action="store_true", help="Usa el modelo real. Tiene costo: requiere autorización")
    parser.add_argument("--output", help="Otra carpeta de resultados (para los controles)")
    parser.add_argument("--work-dir", help="Carpeta de trabajo que se conserva (para los controles)")
    parser.add_argument("--tamper", help='Control negativo: altera solo la copia del candidato. JSON con "path", "old" y "new"')
    parser.add_argument("--internal-capture", help=argparse.SUPPRESS)
    parser.add_argument("--internal-report", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.internal_capture:
        return capture(json.loads(Path(args.internal_capture).read_text(encoding="utf-8")))
    if args.internal_report:
        return report(json.loads(Path(args.internal_report).read_text(encoding="utf-8")))
    if not args.experiment or not args.baseline:
        parser.error("Faltan --experiment y --baseline.")
    return orchestrate(args)


if __name__ == "__main__":
    raise SystemExit(main())
