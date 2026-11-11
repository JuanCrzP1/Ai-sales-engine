"""Elegir el modelo de la lista de OpenRouter, sin copiarlo a mano.

Solo se ofrecen los modelos que conversan en texto, tienen precio conocido y responden en JSON (el formato del motor). La lista
se guarda una hora; si OpenRouter no responde, se usa la anterior, y si nunca se cargó, el panel deja escribir el modelo.
"""
from __future__ import annotations

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.admin_api.main import create_app
from app.domain.business_config.ai_models import RECOMMENDED_MODELS, AIModel
from app.domain.business_config.errors import InvalidFieldsError, ModelCatalogUnavailableError
from app.infrastructure.ai.openrouter_models import CACHE_SECONDS, OpenRouterModelCatalog, parse_models
from app.infrastructure.business_config.database import (
    build_assistant_lab_service,
    build_business_config_service,
    create_business_config_engine,
    create_local_schema,
)
from app.infrastructure.business_config.example_businesses import import_example, load_example

KEY = "sk-or-v1-clave-ficticia-del-restaurante-0001"


def _item(model_id: str, name: str, *, prompt="0.00000015", completion="0.0000006", inputs=("text",), outputs=("text",), json=True) -> dict:
    return {
        "id": model_id,
        "name": name,
        "context_length": 128000,
        "architecture": {"input_modalities": list(inputs), "output_modalities": list(outputs)},
        "pricing": {"prompt": prompt, "completion": completion},
        "supported_parameters": ["temperature", "max_tokens"] + (["response_format"] if json else []),
    }


PAYLOAD = {
    "data": [
        _item("openai/gpt-4o-mini", "OpenAI: GPT-4o-mini"),
        _item("google/gemini-2.5-flash", "Google: Gemini 2.5 Flash", prompt="0.0000003", completion="0.0000025"),
        _item("acme/sin-json", "Acme: Sin JSON", json=False),
        _item("acme/imagenes", "Acme: Imágenes", outputs=("image",)),
        _item("openrouter/auto", "Auto Router", prompt="-1", completion="-1"),
        _item("~anthropic/claude-latest", "Anthropic: Claude (alias)"),
        _item("meta-llama/llama-3.3-70b-instruct:free", "Meta: Llama 3.3 70B (free)", prompt="0", completion="0"),
        _item("zeta/modelo-sin-proveedor", "Modelo sin proveedor en el nombre"),
    ]
}


def test_only_models_that_chat_in_json_with_a_known_price_are_offered():
    models = {model.id: model for model in parse_models(PAYLOAD)}
    assert set(models) == {"openai/gpt-4o-mini", "google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct:free", "zeta/modelo-sin-proveedor"}
    mini = models["openai/gpt-4o-mini"]
    assert (mini.provider, mini.name, mini.prompt_usd_per_million, mini.completion_usd_per_million) == ("OpenAI", "GPT-4o-mini", 0.15, 0.6)
    assert models["meta-llama/llama-3.3-70b-instruct:free"].free
    assert (models["zeta/modelo-sin-proveedor"].provider, models["zeta/modelo-sin-proveedor"].name) == ("zeta", "Modelo sin proveedor en el nombre")
    with pytest.raises(ValueError):
        parse_models({"data": []})


class _OpenRouter:
    """`httpx` de mentira: cuenta las consultas y puede fallar."""

    def __init__(self) -> None:
        self.calls = 0
        self.failing = False

    def get(self, url, timeout):
        self.calls += 1
        if self.failing:
            raise httpx.ConnectError("sin red")
        return httpx.Response(200, json=PAYLOAD, request=httpx.Request("GET", url))


def test_the_list_is_kept_an_hour_and_survives_an_outage():
    now = [1000.0]
    openrouter = _OpenRouter()
    catalog = OpenRouterModelCatalog(client=openrouter, clock=lambda: now[0])
    first = catalog.models()
    catalog.models()
    assert openrouter.calls == 1
    now[0] += CACHE_SECONDS
    openrouter.failing = True
    assert catalog.models() == first and openrouter.calls == 2  # OpenRouter no respondió: se usa la anterior


def test_without_any_list_it_says_so():
    openrouter = _OpenRouter()
    openrouter.failing = True
    with pytest.raises(ModelCatalogUnavailableError):
        OpenRouterModelCatalog(client=openrouter).models()


class _Catalog:
    def __init__(self, models: list[AIModel] | None = None, *, failing: bool = False) -> None:
        self._models = models or parse_models(PAYLOAD)
        self.failing = failing

    def models(self) -> list[AIModel]:
        if self.failing:
            raise ModelCatalogUnavailableError("sin lista")
        return list(self._models)


@pytest.fixture
def platform(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'modelos.sqlite3').as_posix()}")
    create_local_schema(engine)
    key = Fernet.generate_key().decode()
    service = build_business_config_service(engine, secrets_key=key)
    import_example(service, load_example("restaurant"))
    catalog = _Catalog()
    lab = build_assistant_lab_service(engine, service, secrets_key=key, catalog=catalog, default_model="openai/gpt-4o-mini")
    client = TestClient(create_app(service, lab), base_url="http://127.0.0.1:8010", client=("127.0.0.1", 50000))
    yield lab, catalog, client
    engine.dispose()


def test_the_panel_receives_the_list_with_the_recommended_first(platform):
    _lab, _catalog, client = platform
    body = client.get("/api/businesses/restaurant/ai/models").json()
    assert body["default_model"] == "openai/gpt-4o-mini"
    ids = [model["id"] for model in body["models"]]
    assert ids[:2] == [model_id for model_id in RECOMMENDED_MODELS if model_id in ids][:2] == ["openai/gpt-4o-mini", "google/gemini-2.5-flash"]
    first = body["models"][0]
    assert first == {
        "id": "openai/gpt-4o-mini", "name": "GPT-4o-mini", "provider": "OpenAI", "prompt_usd_per_million": 0.15,
        "completion_usd_per_million": 0.6, "context_length": 128000, "recommended": True, "free": False,
    }
    assert client.get("/api/businesses/no_existe/ai/models").status_code == 404


def test_a_model_outside_the_list_is_not_saved(platform):
    lab, catalog, client = platform
    saved = client.put("/api/businesses/restaurant/ai", json={"model": "google/gemini-2.5-flash", "api_key": KEY})
    assert saved.status_code == 200 and saved.json()["model"] == "google/gemini-2.5-flash"
    rejected = client.put("/api/businesses/restaurant/ai", json={"model": "acme/sin-json"})
    assert rejected.status_code == 422
    assert rejected.json()["issues"] == [{"path": "model", "message": "Ese modelo no está disponible en OpenRouter para el asistente. Elígelo de la lista."}]
    # Si OpenRouter no responde, no se bloquea el guardado: el proveedor rechazará un modelo que no exista.
    catalog.failing = True
    assert client.put("/api/businesses/restaurant/ai", json={"model": "acme/otro"}).status_code == 200


def test_the_model_a_business_already_had_is_kept_even_if_it_left_the_list(platform):
    lab, catalog, _client = platform
    catalog.failing = True
    lab.save_ai_settings("restaurant", model="acme/retirado", api_key=KEY)
    catalog.failing = False
    assert lab.save_ai_settings("restaurant", model="acme/retirado").model == "acme/retirado"
    with pytest.raises(InvalidFieldsError):
        lab.save_ai_settings("restaurant", model="acme/otro-retirado")


def test_without_the_list_the_panel_is_told_to_write_it(platform):
    _lab, catalog, client = platform
    catalog.failing = True
    response = client.get("/api/businesses/restaurant/ai/models")
    assert (response.status_code, response.json()["code"]) == (503, "unavailable")
