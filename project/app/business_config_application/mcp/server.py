"""El servidor MCP armado: reconoce la clave con la que llega el agente y responde con las herramientas que esa clave permite.

Agregar herramientas = un archivo en `tools/` (con su permiso en `domain/business_config/key_permissions.py`) y sumarlo aquí. Ver
`docs/mcp.md`.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.business_config_application.access import BusinessAccess
from app.business_config_application.assistant_lab import AssistantLabService
from app.business_config_application.attention import AttentionService
from app.business_config_application.commerce import CommerceService
from app.business_config_application.conversations import ConversationsService
from app.business_config_application.mcp.access import McpAccess
from app.business_config_application.mcp.oauth import McpOAuthService
from app.business_config_application.mcp.protocol import McpProtocol, ToolCallReport
from app.business_config_application.mcp.tools.ai import ai_tools
from app.business_config_application.mcp.tools.attention import attention_tools
from app.business_config_application.mcp.tools.businesses import business_tools
from app.business_config_application.mcp.tools.commerce import commerce_tools
from app.business_config_application.mcp.tools.config import config_tools
from app.business_config_application.mcp.tools.conversations import conversation_tools
from app.business_config_application.mcp.tools.guide import guide_tools
from app.business_config_application.ports import ApiKeyStorage
from app.business_config_application.service import BusinessConfigService
from app.domain.business_config.access import LOCAL_OPERATOR, Principal
from app.domain.business_config.oauth import ACCESS_TOKEN_PREFIX
from app.domain.business_config.templates import BusinessTemplate

# La guía viaja con el motor (en Vercel solo se publica `project/`).
GUIDE_PATH = Path(__file__).resolve().parents[3] / "config" / "agents" / "guia-para-agentes.md"


def read_guide(path: Path = GUIDE_PATH) -> str:
    return path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class McpServer:
    protocol: McpProtocol
    keys: ApiKeyStorage
    # En este equipo, sin cuentas: las claves son del operador local.
    local: bool = False
    # Conectar con inicio de sesión (Claude web y app, ChatGPT). Sin él, solo con clave.
    oauth: McpOAuthService | None = None

    def authenticate(self, token: str) -> McpAccess | None:
        """El acceso de quien llama con una clave activa o un token de acceso vigente, o None. Una clave de la nube sin dueño
        (anterior a las de cuenta) no llega a ningún negocio: solo ve la guía."""
        if self.oauth is not None and token.startswith(ACCESS_TOKEN_PREFIX):
            identity = self.oauth.authenticate(token)
        else:
            identity = self.keys.authenticate(token)
        if identity is None:
            return None
        if self.local:
            principal = LOCAL_OPERATOR
        elif identity.owner_user_id:
            principal = Principal(user_id=identity.owner_user_id, email=identity.owner_label)
        else:
            principal = Principal(user_id=f"clave-sin-dueno:{identity.key_id}")
        return McpAccess(principal=principal, key_id=identity.key_id, key_name=identity.name, scopes=frozenset(identity.scopes), reach=identity.reach)


def build_mcp_server(
    configs: BusinessConfigService,
    access: BusinessAccess,
    keys: ApiKeyStorage,
    *,
    templates: Callable[[], Sequence[BusinessTemplate]],
    schema: dict,
    lab: AssistantLabService | None = None,
    conversations: ConversationsService | None = None,
    commerce: CommerceService | None = None,
    attention: AttentionService | None = None,
    guide: Callable[[], str] = read_guide,
    local: bool = False,
    oauth: McpOAuthService | None = None,
    before_test: Callable[[McpAccess, str], None] = lambda caller, business: None,
    before_reply: Callable[[McpAccess], None] = lambda caller: None,
    on_created: Callable[[McpAccess, str], None] = lambda caller, business: None,
    on_tool_call: Callable[[McpAccess, ToolCallReport], None] = lambda caller, report: None,
) -> McpServer:
    tools = [
        *guide_tools(guide, schema, templates),
        *business_tools(configs, access, templates, on_created),
        *config_tools(configs, access, lab, before_test),
        # Lo que el servidor no tiene (por ejemplo, sin base de conversaciones) no aparece: nunca una herramienta que siempre falla.
        *(ai_tools(lab, access) if lab is not None else []),
        *(conversation_tools(conversations, configs, access, before_reply) if conversations is not None else []),
        *(commerce_tools(commerce, access) if commerce is not None else []),
        *(attention_tools(attention, access) if attention is not None else []),
    ]
    return McpServer(McpProtocol(tools, on_tool_call=on_tool_call), keys, local, oauth)
