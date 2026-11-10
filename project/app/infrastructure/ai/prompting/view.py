"""Lo que el prompt sabe de un mensaje: el runtime del negocio (lo publicado, ya compilado) y el estado de la conversación.

Los bloques de `sections/` leen de aquí en lugar de revisar a mano el tipo de cada valor del runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from app.infrastructure.ai.prompting.text import as_dict, as_text

# Lo que todo runtime debe traer para armar el prompt (`RuntimeYamlBuilder` ya lo exige al cargarlo).
REQUIRED_SECTIONS = ("sales", "business", "pricing", "inventory")


def validate_runtime_yaml(runtime_yaml: dict) -> None:
    payload = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    for key in REQUIRED_SECTIONS:
        if not isinstance(payload.get(key), dict):
            raise RuntimeError(f"{key} not loaded in runtime")


@dataclass(frozen=True)
class PromptView:
    runtime: dict
    user_message: str = ""

    def section(self, key: str) -> dict:
        return as_dict(self.runtime.get(key))

    @property
    def business(self) -> dict:
        return self.section("business")

    @property
    def sales(self) -> dict:
        return self.section("sales")

    @property
    def pricing(self) -> dict:
        return self.section("pricing")

    @property
    def inventory(self) -> dict:
        return self.section("inventory")

    @property
    def config(self) -> dict:
        return self.section("config")

    @property
    def memory(self) -> dict:
        return self.section("memory_context")

    @property
    def capabilities(self) -> dict:
        """Las capacidades en la raíz del runtime o, si no están, las de `config`."""
        return self.section("capabilities") or as_dict(self.config.get("capabilities"))

    @property
    def post_payment(self) -> dict:
        return self.section("post_payment") or as_dict(self.config.get("post_payment"))

    @property
    def features(self) -> dict:
        """Los interruptores de la oferta tal como los compiló el contrato (`config.features`)."""
        return as_dict(self.config.get("features"))

    @cached_property
    def state(self) -> str:
        """Estado de la conversación en minúsculas: new (por defecto), active, warm o cold."""
        return str(self.runtime.get("conversation_state") or "new").strip().lower() or "new"

    @property
    def state_label(self) -> str:
        """El estado tal como lo dejó la memoria, para mostrarlo en el prompt."""
        return as_text(self.runtime.get("conversation_state", "new")) or "new"

    @property
    def prior_ai_response(self) -> str:
        return str(self.memory.get("last_ai_response") or self.memory.get("last_response") or "").strip()

    @cached_property
    def presents_business(self) -> bool:
        """Si este mensaje presenta el negocio: en una conversación nueva o fría, o mientras el asistente no haya respondido.

        En una conversación en curso (activa o tibia) en la que el asistente ya habló, no se repite la presentación."""
        return not self.prior_ai_response or self.state in ("new", "cold")

    @property
    def relevance_query(self) -> str:
        """Lo que está buscando el cliente: su mensaje y el anterior. Elige qué parte de un catálogo grande va al prompt."""
        return f"{self.user_message} {as_text(self.runtime.get('previous_user_message'))}".strip()

    @property
    def tenant(self) -> str:
        return str(self.runtime.get("tenant_slug") or self.runtime.get("client_config_id") or "").strip().lower()

    @property
    def user_id(self) -> str:
        return str(self.memory.get("user_id") or self.runtime.get("user_id") or "").strip().lower()
