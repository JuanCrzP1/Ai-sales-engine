from __future__ import annotations

from app.domain.ai.prompt_context import build_prompt_context
from app.infrastructure.config.config_service import ConfigService

IDENTITY_BLOCK = """
Estás hablando con una persona real por chat.

Tu trabajo es guiarle a una decisión y hacer avanzar la conversación según lo que necesita en este momento.
"""


GROUNDING_BLOCK = """
REGLA CRÍTICA:
Responde SOLO con información que esté en el contexto proporcionado.
NO inventes funcionalidades, canales o características que no estén explícitamente mencionadas.
Si el usuario pregunta por algo que no aparece en el contexto: dilo y redirige a lo que sí está disponible.
Responde directo y toca un solo tema por mensaje.
""".strip()

COMMERCIAL_BEHAVIOR_BLOCK = """
COMPORTAMIENTO COMERCIAL
Tu objetivo es ayudar al cliente a avanzar en la conversación hacia una decisión.
Flujo: dolor -> impacto -> dinero -> solución -> acción.
Si el usuario muestra intención de avanzar, lleva a acción directa sin preguntas abiertas.
Habla como una persona real vendiendo por chat.
""".strip()

CLOSING_METHODS_BLOCK = """
MÉTODOS DE CIERRE DISPONIBLES:
Métodos activos en este negocio:
{closing_methods}
""".strip()


DATA_COLLECTION_BLOCK = """
Campos definidos para pedir al cliente:
{data_collection_fields}
""".strip()


POST_PAYMENT_BLOCK = """
POST-PAGO:
ON_USER_REPORT_MESSAGE: {on_user_report_message}
ON_PAYMENT_CONFIRMED_MESSAGE: {on_payment_confirmed_message}
- Si el usuario reporta pago, responde EXACTAMENTE con ON_USER_REPORT_MESSAGE.
- NO confirmes el pago.
""".strip()


MEMORY_BEHAVIOR_BLOCK = """
COMPORTAMIENTO CON MEMORIA:
INTENT_DETECTADO_PREVIO: {intent_detectado}
METODO_PAGO_ELEGIDO_PREVIO: {metodo_pago_elegido}
ESTADO_PAGO_PREVIO: {estado_pago}
- Usa esta memoria solo para continuar mejor la conversación.
- Para pago y post-pago manda SOLO el mensaje actual del usuario.
- No inventes confirmaciones ni acciones no confirmadas.
""".strip()




def validate_runtime_yaml(runtime_yaml: dict) -> None:
    required = ["sales", "business", "pricing", "inventory"]
    payload = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    for key in required:
        value = payload.get(key)
        if not isinstance(value, dict):
            raise RuntimeError(f"{key} not loaded in runtime")


def resolve_business_model(business, pricing, inventory) -> str:
    """
    Retorna: 'saas' | 'service' | 'catalog'
    """
    del business
    safe_pricing = pricing if isinstance(pricing, dict) else {}
    safe_inventory = inventory if isinstance(inventory, dict) else {}

    catalog = safe_pricing.get("catalog") if isinstance(safe_pricing.get("catalog"), dict) else {}
    catalog_items = catalog.get("items")
    plans = safe_pricing.get("plans")

    items = safe_inventory.get("items")
    if isinstance(items, list) and items:
        return "catalog"

    if isinstance(catalog_items, list) and catalog_items:
        return "catalog"

    if isinstance(plans, list) and plans:
        return "saas"

    return "service"


def detect_business_model(runtime_yaml: dict) -> str:
    payload = runtime_yaml if isinstance(runtime_yaml, dict) else {}
    business = payload.get("business") if isinstance(payload.get("business"), dict) else {}
    pricing = payload.get("pricing") if isinstance(payload.get("pricing"), dict) else {}
    inventory = payload.get("inventory") if isinstance(payload.get("inventory"), dict) else {}

    return resolve_business_model(business, pricing, inventory)


class PromptBuilderService:
    def __init__(self, *, prompt_path: str | None = None) -> None:
        del prompt_path
        self.config = ConfigService()

    @staticmethod
    def _as_dict(value: object) -> dict:
        return value if isinstance(value, dict) else {}

    def _prompt_metadata(self, *, client_config_id: str | None = None) -> dict:
        del client_config_id
        return {
            "prompt_path": "",
            "prompt_text": "",
            "prompt_hash": "",
            "prompt_version": "single-source-v1",
            "prompt_source": "single_contract_blocks",
        }

    @staticmethod
    def _as_text(value: object) -> str:
        if isinstance(value, str):
            return value.strip()
        if value is None:
            return ""
        if isinstance(value, (int, float, bool)):
            return str(value).strip()
        return ""

    @staticmethod
    def _shorten_text(value: object, *, max_words: int) -> str:
        text = PromptBuilderService._as_text(value)
        if not text:
            return ""
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words])

    @staticmethod
    def build_business_context(yaml_config: dict) -> str:
        business = yaml_config.get("business", {}) if isinstance(yaml_config.get("business"), dict) else {}
        pricing = yaml_config.get("pricing", {}) if isinstance(yaml_config.get("pricing"), dict) else {}
        inventory = yaml_config.get("inventory", {}) if isinstance(yaml_config.get("inventory"), dict) else {}
        plans = pricing.get("plans", []) if isinstance(pricing.get("plans"), list) else []
        catalog = pricing.get("catalog", {}) if isinstance(pricing.get("catalog"), dict) else {}
        catalog_items = catalog.get("items", []) if isinstance(catalog.get("items"), list) else []
        inventory_items = inventory.get("items", []) if isinstance(inventory.get("items"), list) else []

        offer_names = [
            PromptBuilderService._as_text(plan.get("name") or plan.get("id"))
            for plan in plans[:2]
            if isinstance(plan, dict) and PromptBuilderService._as_text(plan.get("name") or plan.get("id"))
        ]
        if not offer_names:
            offer_names = [
                PromptBuilderService._as_text(item.get("name") or item.get("id"))
                for item in catalog_items[:2]
                if isinstance(item, dict) and PromptBuilderService._as_text(item.get("name") or item.get("id"))
            ]
        if not offer_names:
            offer_names = [
                PromptBuilderService._as_text(item.get("name") or item.get("id"))
                for item in inventory_items[:2]
                if isinstance(item, dict) and PromptBuilderService._as_text(item.get("name") or item.get("id"))
            ]

        industry = PromptBuilderService._shorten_text(business.get("industry", ""), max_words=8)
        promise = PromptBuilderService._shorten_text(business.get("promise", ""), max_words=30)
        offer_text = ", ".join(offer_names) or industry or "oferta definida en YAML"

        return "\n".join(
            [
                f"Industria del negocio: {industry or offer_text}.",
                f"Qué vende: {offer_text}.",
                f"Promesa comercial: {promise or 'resultado comercial definido en YAML'}.",
            ]
        )

    @staticmethod
    def build_customer_context(yaml_config: dict) -> str:
        del yaml_config
        return ""

    @staticmethod
    def build_capabilities_context(yaml_config: dict) -> str:
        capabilities = yaml_config.get("capabilities") if isinstance(yaml_config.get("capabilities"), dict) else {}
        if not capabilities:
            config_section = yaml_config.get("config") if isinstance(yaml_config.get("config"), dict) else {}
            capabilities = config_section.get("capabilities") if isinstance(config_section.get("capabilities"), dict) else {}

        def _collect_channels(raw_value: object) -> list[str]:
            if isinstance(raw_value, dict):
                raw_value = raw_value.get("allowed", [])
            if isinstance(raw_value, str):
                raw_items = [raw_value]
            elif isinstance(raw_value, list):
                raw_items = raw_value
            else:
                raw_items = []

            return [
                channel
                for item in raw_items
                if (channel := PromptBuilderService._as_text(item))
            ]

        def _dedupe(values: list[str]) -> list[str]:
            ordered = []
            for value in values:
                if value and value not in ordered:
                    ordered.append(value)
            return ordered

        legacy_channels = []
        business_channels = []
        system_channels = []
        if isinstance(capabilities, dict):
            legacy_channels = _dedupe(_collect_channels(capabilities.get("channels", [])))
            business_channels = _dedupe(_collect_channels(capabilities.get("business_channels", [])))
            system_channels = _dedupe(_collect_channels(capabilities.get("system_channels", [])))

        # Compatibilidad: si solo existe estructura legacy, usarla como atencion.
        if not business_channels and not system_channels and legacy_channels:
            business_channels = list(legacy_channels)

        business_channels_text = ", ".join(business_channels) or "sin canales de atencion definidos"
        system_channels_text = ", ".join(system_channels) or "sin canales de sistema definidos"

        raw_actions = capabilities.get("actions", []) if isinstance(capabilities, dict) else []
        if isinstance(raw_actions, dict):
            ordered_actions = []
            for key in ("primary", "support"):
                values = raw_actions.get(key, []) if isinstance(raw_actions.get(key), list) else []
                for item in values:
                    action = PromptBuilderService._as_text(item)
                    if action and action not in ordered_actions:
                        ordered_actions.append(action)
            raw_actions = ordered_actions
        actions = ", ".join(
            PromptBuilderService._as_text(item)
            for item in raw_actions
            if PromptBuilderService._as_text(item)
        ) or "sin acciones definidas"

        raw_closing_methods = capabilities.get("closing_methods") if isinstance(capabilities, dict) else {}
        closing_method_names = []
        if isinstance(raw_closing_methods, dict):
            for method_name in ("link_payment", "human_handoff", "data_collection"):
                raw_method = raw_closing_methods.get(method_name)
                is_enabled = False
                if isinstance(raw_method, dict):
                    is_enabled = bool(raw_method.get("enabled", False))
                elif isinstance(raw_method, bool):
                    is_enabled = raw_method
                if is_enabled:
                    closing_method_names.append(method_name)

        closing_methods_text = ", ".join(closing_method_names) or "sin métodos de cierre activos"

        raw_data_collection = capabilities.get("data_collection") if isinstance(capabilities, dict) else {}
        data_collection_enabled = False
        raw_data_fields = []
        if isinstance(raw_data_collection, dict):
            data_collection_enabled = bool(raw_data_collection.get("enabled", False))
            raw_data_fields = raw_data_collection.get("fields", [])
        elif isinstance(raw_data_collection, bool):
            data_collection_enabled = raw_data_collection

        if isinstance(raw_data_fields, str):
            raw_data_fields = [raw_data_fields]
        elif not isinstance(raw_data_fields, list):
            raw_data_fields = []

        data_collection_fields = _dedupe(
            [
                field
                for item in raw_data_fields
                if (field := PromptBuilderService._as_text(item))
            ]
        )
        data_collection_status = "activo" if data_collection_enabled else "inactivo"
        data_collection_fields_text = ", ".join(data_collection_fields) or "sin campos definidos"
        del data_collection_status

        return "\n".join(
            [
                "TIPOS DE CANALES:",
                f"CANALES DE ATENCION (business_channels): {business_channels_text}",
                f"CANALES DEL SISTEMA (system_channels): {system_channels_text}",
                "Si hablas de como funciona el sistema, usa system_channels.",
                CLOSING_METHODS_BLOCK.format(closing_methods=closing_methods_text),
                DATA_COLLECTION_BLOCK.format(data_collection_status="", data_collection_fields=data_collection_fields_text),
                f"Acciones disponibles: {actions}",
            ]
        )

    @staticmethod
    def build_post_payment_context(yaml_config: dict) -> str:
        post_payment = yaml_config.get("post_payment") if isinstance(yaml_config.get("post_payment"), dict) else {}
        if not post_payment:
            config_section = yaml_config.get("config") if isinstance(yaml_config.get("config"), dict) else {}
            post_payment = config_section.get("post_payment") if isinstance(config_section.get("post_payment"), dict) else {}

        on_user_report = post_payment.get("on_user_report") if isinstance(post_payment.get("on_user_report"), dict) else {}
        on_payment_confirmed = post_payment.get("on_payment_confirmed") if isinstance(post_payment.get("on_payment_confirmed"), dict) else {}

        on_user_report_message = PromptBuilderService._as_text(on_user_report.get("message", "")) or "sin mensaje configurado"
        on_payment_confirmed_message = PromptBuilderService._as_text(on_payment_confirmed.get("message", "")) or "sin mensaje configurado"

        return POST_PAYMENT_BLOCK.format(
            on_user_report_available="true" if PromptBuilderService._as_text(on_user_report.get("message", "")) else "false",
            on_payment_confirmed_available="true" if PromptBuilderService._as_text(on_payment_confirmed.get("message", "")) else "false",
            on_user_report_message=on_user_report_message,
            on_payment_confirmed_message=on_payment_confirmed_message,
        )

    @staticmethod
    def build_pricing_context(yaml_config: dict) -> str:
        pricing = yaml_config.get("pricing", {})
        features = yaml_config.get("features", {}) if isinstance(yaml_config.get("features"), dict) else {}
        plans = pricing.get("plans", [])
        catalog = pricing.get("catalog", {}) if isinstance(pricing.get("catalog"), dict) else {}
        catalog_items = catalog.get("items", []) if isinstance(catalog.get("items"), list) else []

        def _transfer_method_line(raw_method: object) -> str:
            method = raw_method if isinstance(raw_method, dict) else {}
            method_type = PromptBuilderService._as_text(method.get("type", "")).lower()
            if method_type in {"nequi", "daviplata"}:
                number = PromptBuilderService._as_text(method.get("number", ""))
                if number:
                    return f"- {method_type}: {number}"
                return ""
            if method_type == "bank":
                bank = PromptBuilderService._as_text(method.get("bank", ""))
                account_type = PromptBuilderService._as_text(method.get("account_type", ""))
                account_number = PromptBuilderService._as_text(method.get("account_number", ""))
                if bank and account_type and account_number:
                    return f"- bank: {bank} / {account_type} / {account_number}"
                return ""
            if method_type == "breb":
                reference = PromptBuilderService._as_text(method.get("reference", ""))
                if reference:
                    return f"- breb: {reference}"
                return ""
            return ""

        def _collect_transfer_lines(raw_payment: object) -> list[str]:
            payment = raw_payment if isinstance(raw_payment, dict) else {}
            transfer = payment.get("transfer") if isinstance(payment.get("transfer"), dict) else {}
            if not bool(transfer.get("enabled", False)):
                return []
            raw_methods = transfer.get("methods") if isinstance(transfer.get("methods"), list) else []
            return [line for item in raw_methods if (line := _transfer_method_line(item))]

        includes = []
        not_included = []
        conditions = pricing.get("conditions", []) if isinstance(pricing.get("conditions"), list) else []

        plan_names = []
        plan_price_summaries = []
        payment_links = []
        transfer_method_lines = []
        for plan in plans:
            if not isinstance(plan, dict):
                continue
            plan_name = PromptBuilderService._as_text(plan.get("name", "") or plan.get("id", ""))
            if plan_name:
                plan_names.append(plan_name)

            payment_cfg = plan.get("payment", {}) if isinstance(plan.get("payment"), dict) else {}
            payment_link = PromptBuilderService._as_text(payment_cfg.get("link", ""))
            if payment_link:
                payment_links.append(f"{plan_name or 'oferta'}: {payment_link}")
            for transfer_line in _collect_transfer_lines(payment_cfg):
                if transfer_line not in transfer_method_lines:
                    transfer_method_lines.append(transfer_line)

            for value in plan.get("includes", []) if isinstance(plan.get("includes"), list) else []:
                include_text = PromptBuilderService._as_text(value)
                if include_text and include_text not in includes:
                    includes.append(include_text)

            for value in plan.get("not_included", []) if isinstance(plan.get("not_included"), list) else []:
                not_included_value = PromptBuilderService._as_text(value)
                if not_included_value and not_included_value not in not_included:
                    not_included.append(not_included_value)

            pricing_map = plan.get("pricing", {}) if isinstance(plan.get("pricing"), dict) else {}
            currency_chunks = []
            for currency_key, price_values in pricing_map.items():
                if not isinstance(price_values, dict):
                    continue
                value_chunks = []
                for field in ("implementation", "monthly", "first_payment", "price"):
                    value = price_values.get(field)
                    if value not in (None, ""):
                        value_chunks.append(f"{field}={value}")
                if value_chunks:
                    currency_chunks.append(f"{PromptBuilderService._as_text(currency_key).upper()}: {', '.join(value_chunks)}")
            if currency_chunks:
                summary_name = plan_name or "oferta"
                plan_price_summaries.append(f"{summary_name} -> {' | '.join(currency_chunks)}")

        product_names = []
        for item in catalog_items:
            if not isinstance(item, dict):
                continue
            product_name = PromptBuilderService._as_text(item.get("name", "") or item.get("id", ""))
            if product_name:
                product_names.append(product_name)

        catalog_payment_cfg = catalog.get("payment", {}) if isinstance(catalog.get("payment"), dict) else {}
        catalog_payment_link = PromptBuilderService._as_text(catalog_payment_cfg.get("link", ""))
        if catalog_payment_link:
            payment_links.append(f"catálogo: {catalog_payment_link}")
        for transfer_line in _collect_transfer_lines(catalog_payment_cfg):
            if transfer_line not in transfer_method_lines:
                transfer_method_lines.append(transfer_line)

        root_payment_cfg = pricing.get("payment", {}) if isinstance(pricing.get("payment"), dict) else {}
        root_payment_link = PromptBuilderService._as_text(root_payment_cfg.get("link", ""))
        if root_payment_link:
            payment_links.append(root_payment_link)
        for transfer_line in _collect_transfer_lines(root_payment_cfg):
            if transfer_line not in transfer_method_lines:
                transfer_method_lines.append(transfer_line)

        category_names = []
        for category in catalog.get("categories", []) if isinstance(catalog.get("categories"), list) else []:
            if not isinstance(category, dict):
                continue
            category_name = PromptBuilderService._as_text(category.get("name", "") or category.get("id", ""))
            if category_name:
                category_names.append(category_name)

        conditions_text = ", ".join(
            PromptBuilderService._as_text(condition)
            for condition in conditions
            if PromptBuilderService._as_text(condition)
        ) or "sin condiciones explícitas"
        plan_names_text = ", ".join(plan_names)
        category_names_text = ", ".join(category_names[:4])

        if plan_names_text:
            offer_reference_text = plan_names_text
        elif category_names_text:
            offer_reference_text = category_names_text
        elif product_names:
            offer_reference_text = "oferta de catálogo definida en pricing"
        else:
            offer_reference_text = "sin nombres específicos en pricing"

        pricing_structure_text = "; ".join(plan_price_summaries) if plan_price_summaries else "valores definidos en pricing para este negocio"
        payment_links_text = " | ".join(payment_links) if payment_links else "sin links de pago definidos"
        link_available_text = "true" if payment_links else "false"
        transfer_available_text = "true" if transfer_method_lines else "false"
        transfer_methods_text = "\n".join(transfer_method_lines) if transfer_method_lines else "- none"
        pricing_enabled = bool(features.get("pricing_enabled", True))
        if not pricing_enabled and not plan_price_summaries and not payment_links and not transfer_method_lines:
            return ""

        lines = [
            "USO COMPLETO DEL PRICING:",
            "No puedes omitir información que cambie cómo el cliente paga.",
            f"Qué se cobra: {offer_reference_text}.",
            f"Precios: {pricing_structure_text}.",
            f"Condiciones: {conditions_text}.",
            f"LINK_AVAILABLE: {link_available_text}",
            f"TRANSFER_AVAILABLE: {transfer_available_text}",
        ]
        if payment_links:
            lines.append(f"PAYMENT_LINKS: {payment_links_text}")
        else:
            lines.append("sin links de pago definidos")
        lines.extend(
            [
                "TRANSFER_METHODS:",
                transfer_methods_text,
                "NO muestres links, números, cuentas ni referencias sin elección explícita del usuario.",
                "SOLO ejecuta el pago cuando el usuario elige explícitamente link, nequi, daviplata, bank o breb.",
                "Si el usuario aún no eligió método, antes de pedir elegir escribe literalmente: avanzamos con el siguiente paso.",
            ]
        )
        if payment_links and transfer_method_lines:
            lines.append("Si hay link y transferencia disponibles, pregunta: prefieres link o transferencia.")
        return "\n".join(lines)

    @staticmethod
    def build_sales_context(yaml_config: dict) -> str:
        sales = yaml_config.get("sales", {}) if isinstance(yaml_config.get("sales"), dict) else {}
        business = yaml_config.get("business", {}) if isinstance(yaml_config.get("business"), dict) else {}

        motivations = sales.get("buying_motivation", {}) if isinstance(sales.get("buying_motivation"), dict) else {}
        if not motivations:
            motivations = business.get("buying_motivation", {}) if isinstance(business.get("buying_motivation"), dict) else {}

        use_cases = sales.get("use_cases", []) if isinstance(sales.get("use_cases"), list) else []
        if not use_cases:
            use_cases = business.get("use_cases", []) if isinstance(business.get("use_cases"), list) else []

        primary = PromptBuilderService._as_text(motivations.get("primary", ""))
        secondary = PromptBuilderService._as_text(motivations.get("secondary", ""))
        pain = sales.get("pain", {}) if isinstance(sales.get("pain"), dict) else {}
        clusters = pain.get("clusters", {}) if isinstance(pain.get("clusters"), dict) else {}
        impact_samples = []
        for cluster in clusters.values():
            if not isinstance(cluster, dict):
                continue
            impacts = cluster.get("impacts", []) if isinstance(cluster.get("impacts"), list) else []
            for impact in impacts:
                impact_text = PromptBuilderService._as_text(impact)
                if impact_text:
                    impact_samples.append(impact_text)
                    break
            if len(impact_samples) >= 2:
                break
        impact_text = ", ".join(impact_samples)
        use_cases_text = ", ".join(
            PromptBuilderService._as_text(item.get("nombre", "") or item.get("name", ""))
            for item in use_cases[:2]
            if isinstance(item, dict) and PromptBuilderService._as_text(item.get("nombre", "") or item.get("name", ""))
        )

        lines = []
        if primary or secondary:
            lines.append(f"Motores de compra del YAML: {primary or 'no definido'} y {secondary or 'no definido' }.")
        if impact_text or use_cases_text:
            lines.append(f"Casos típicos: {impact_text or use_cases_text}.")
        return "\n".join(lines).strip()

    @staticmethod
    def build_conversation_state(yaml_config: dict, user_message: str) -> str:
        memory = yaml_config.get("memory_context", {}) if isinstance(yaml_config.get("memory_context"), dict) else {}
        history = yaml_config.get("conversation_history", []) if isinstance(yaml_config.get("conversation_history"), list) else []
        del history
        del user_message

        last_intent = PromptBuilderService._as_text(memory.get("last_intent", ""))
        last_pain = PromptBuilderService._as_text(memory.get("last_pain", ""))
        summary = memory.get("history_summary", "")
        price_anchor = memory.get("price_anchor", "")

        conversation_state = PromptBuilderService._as_text(yaml_config.get("conversation_state", "new")) or "new"

        state_legend = "- new: entiende primero.\n- active: ve directo y no repitas.\n- warm: retoma.\n- cold: reengancha."

        if price_anchor:
            return f"""
Estado de la conversación: {conversation_state}
{state_legend}
Este cliente ya conoce el precio: {price_anchor}.
Contexto previo: {summary}
Última intención detectada: {last_intent}
Dolor detectado: {last_pain}
"""

        return f"""
Estado de la conversación: {conversation_state}
    Contexto previo: {summary}
    Última intención detectada: {last_intent}
    Dolor detectado: {last_pain}
{state_legend}
""".strip()

    @staticmethod
    def build_recent_customer_context(yaml_config: dict) -> str:
        memory = yaml_config.get("memory_context", {}) if isinstance(yaml_config.get("memory_context"), dict) else {}

        last_user_message = PromptBuilderService._as_text(memory.get("last_user_message") or memory.get("last_message"))
        last_intent = PromptBuilderService._as_text(memory.get("last_intent", ""))
        detected_intent = PromptBuilderService._as_text(memory.get("intent_detectado", ""))
        payment_method = PromptBuilderService._as_text(memory.get("metodo_pago_elegido", ""))
        payment_status = PromptBuilderService._as_text(memory.get("estado_pago", ""))
        last_ai_response = PromptBuilderService._as_text(memory.get("last_ai_response") or memory.get("last_response"))

        lines = ["Contexto reciente del cliente:"]
        if last_intent:
            lines.append(f"- Última intención detectada: {last_intent}")
        if detected_intent:
            lines.append(f"- Intento comercial recordado: {detected_intent}")
        if payment_method:
            lines.append(f"- Método de pago elegido: {payment_method}")
        if payment_status:
            lines.append(f"- Estado de pago recordado: {payment_status}")
        if last_ai_response:
            lines.append(f"- Última respuesta enviada: {last_ai_response}")
            lines.append("Si ya lo explicaste, no lo repitas; continúa desde ahí.")

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    @staticmethod
    def build_sales_memory_hint(yaml_config: dict) -> str:
        memory = yaml_config.get("memory_context", {}) if isinstance(yaml_config.get("memory_context"), dict) else {}
        sales_memory_hint = PromptBuilderService._as_text(memory.get("sales_memory_hint", ""))
        if not sales_memory_hint:
            return ""

        return f"Dato previo relevante: {sales_memory_hint}. Retómalo sin perder continuidad."

    @staticmethod
    def build_memory_behavior_context(yaml_config: dict) -> str:
        memory = yaml_config.get("memory_context", {}) if isinstance(yaml_config.get("memory_context"), dict) else {}
        intent_detectado = PromptBuilderService._as_text(memory.get("intent_detectado", "")) or "none"
        metodo_pago_elegido = PromptBuilderService._as_text(memory.get("metodo_pago_elegido", "")) or "none"
        estado_pago = PromptBuilderService._as_text(memory.get("estado_pago", "")) or "none"

        if intent_detectado == "none" and metodo_pago_elegido == "none" and estado_pago == "none":
            return ""

        return MEMORY_BEHAVIOR_BLOCK.format(
            intent_detectado=intent_detectado,
            metodo_pago_elegido=metodo_pago_elegido,
            estado_pago=estado_pago,
        )

    @staticmethod
    def build_business_model_context(yaml_config: dict) -> str:
        business_model = detect_business_model(yaml_config)
        return f"modelo: {business_model}"

    @staticmethod
    def build_catalog_behavior_context(yaml_config: dict) -> str:
        pricing = yaml_config.get("pricing") if isinstance(yaml_config.get("pricing"), dict) else {}
        is_catalog = bool(
            pricing.get("model") == "catalog"
            or isinstance(pricing.get("catalog"), dict)
        ) or detect_business_model(yaml_config) == "catalog"
        if not is_catalog:
            return ""
        return "Si es catálogo, nombra 1 o 2 productos o categorías reales y guía a elegir."

    def _resolve_runtime_yaml(self, *, client_config_id: str | None, yaml_config: dict) -> dict:
        from app.application.runtime.runtime_yaml_builder import RuntimeYamlBuilder

        runtime_yaml = RuntimeYamlBuilder().build(
            tenant_slug=str(client_config_id or "").strip(),
            partial_yaml=yaml_config,
        )
        validate_runtime_yaml(runtime_yaml)
        return runtime_yaml

    def _hydrate_runtime_yaml(self, *, client_config_id: str | None, runtime_yaml: dict) -> dict:
        hydrated = dict(runtime_yaml if isinstance(runtime_yaml, dict) else {})
        tenant_slug = str(client_config_id or "").strip()
        if not tenant_slug:
            return hydrated

        sales_cfg = hydrated.get("sales") if isinstance(hydrated.get("sales"), dict) else {}
        if not sales_cfg:
            sales_payload = self.config.load_sales(client_id=tenant_slug)
            loaded_sales = sales_payload.get("sales") if isinstance(sales_payload.get("sales"), dict) else sales_payload
            hydrated["sales"] = loaded_sales if isinstance(loaded_sales, dict) else {}

        business_cfg = hydrated.get("business") if isinstance(hydrated.get("business"), dict) else {}
        if not business_cfg:
            business_payload = self.config.load_business(client_id=tenant_slug)
            loaded_business = business_payload.get("business") if isinstance(business_payload.get("business"), dict) else business_payload
            hydrated["business"] = loaded_business if isinstance(loaded_business, dict) else {}

        pricing_cfg = hydrated.get("pricing") if isinstance(hydrated.get("pricing"), dict) else {}
        if not pricing_cfg:
            pricing_payload = self.config.load_pricing(client_id=tenant_slug)
            hydrated["pricing"] = pricing_payload if isinstance(pricing_payload, dict) else {}

        inventory_cfg = hydrated.get("inventory") if isinstance(hydrated.get("inventory"), dict) else {}
        if not inventory_cfg:
            inventory_payload = self.config.load_inventory(client_id=tenant_slug)
            hydrated["inventory"] = inventory_payload if isinstance(inventory_payload, dict) else {}

        features_cfg = hydrated.get("features") if isinstance(hydrated.get("features"), dict) else {}
        if not features_cfg:
            features_payload = self.config.load_features(client_id=tenant_slug)
            hydrated["features"] = features_payload if isinstance(features_payload, dict) else {}

        validate_runtime_yaml(hydrated)
        return hydrated

    def build(
        self,
        *,
        client_config_id: str | None,
        user_message: str,
        yaml_config: dict | None,
        faq_results: list[dict] | None,
        progression_rules: dict | None,
        **_kwargs,
    ) -> tuple[str, dict, dict]:
        del progression_rules
        del faq_results

        safe_yaml = self._resolve_runtime_yaml(client_config_id=client_config_id, yaml_config=yaml_config if isinstance(yaml_config, dict) else {})
        safe_yaml = self._hydrate_runtime_yaml(client_config_id=client_config_id, runtime_yaml=safe_yaml)
        memory = safe_yaml.get("memory_context") if isinstance(safe_yaml.get("memory_context"), dict) else {}

        context = build_prompt_context(
            user_message=user_message,
            yaml_config=safe_yaml,
            memory=memory,
        )

        prompt_metadata = self._prompt_metadata(client_config_id=client_config_id)
        grounding_block = GROUNDING_BLOCK
        _conv_state = str(safe_yaml.get("conversation_state") or "new").strip().lower() or "new"
        _is_new = _conv_state == "new"
        _is_cold = _conv_state == "cold"
        _prior_ai_response = str(
            memory.get("last_ai_response") or memory.get("last_response") or ""
        ).strip()
        _ai_already_spoke = bool(_prior_ai_response)
        # Suprimir contexto de presentación solo cuando la IA ya habló.
        # Si es new/cold siempre inyectar. Si es active/warm pero no hubo
        # respuesta previa, también inyectar (primer turno real de la IA).
        _suppress_intro = _ai_already_spoke and not (_is_new or _is_cold)
        if _suppress_intro:
            business_context = ""
            customer_context = ""
        else:
            business_context = self.build_business_context(safe_yaml)
            customer_context = self.build_customer_context(safe_yaml)
        capabilities_context = self.build_capabilities_context(safe_yaml)
        post_payment_context = self.build_post_payment_context(safe_yaml)
        memory_behavior_context = self.build_memory_behavior_context(safe_yaml)
        business_model_context = self.build_business_model_context(safe_yaml)
        catalog_behavior_context = self.build_catalog_behavior_context(safe_yaml)
        pricing_context = self.build_pricing_context(safe_yaml)
        sales_context = self.build_sales_context(safe_yaml) if not _suppress_intro else ""
        recent_customer_context = self.build_recent_customer_context(safe_yaml)
        conversation_state = self.build_conversation_state(safe_yaml, user_message)
        sales_memory_hint = self.build_sales_memory_hint(safe_yaml)
        response_length = self._as_text(safe_yaml.get("response_length") or "short") or "short"
        config_section = safe_yaml.get("config") if isinstance(safe_yaml.get("config"), dict) else {}
        response_cfg = config_section.get("response") if isinstance(config_section.get("response"), dict) else {}
        try:
            response_max_words = max(20, int(safe_yaml.get("response_max_words") or response_cfg.get("max_words") or 80))
        except (TypeError, ValueError):
            response_max_words = 80
        commercial_behavior_block = COMMERCIAL_BEHAVIOR_BLOCK
        continuity_rule_block = "NO lo repitas. No reinicies la conversación." if _suppress_intro else ""
        operational_rules_block = grounding_block

        response_style_block = f"""
ESTILO: {response_length}, máximo {response_max_words} palabras, natural y claro.
""".strip()

        existing_prompt = f"""
CONTEXTO DEL NEGOCIO:
{business_context}
{customer_context}

REGLAS OPERATIVAS:
{operational_rules_block}

CAPACIDADES DEL NEGOCIO:
{business_model_context}
{catalog_behavior_context}
{capabilities_context}

COMPORTAMIENTO COMERCIAL:
{commercial_behavior_block}
{sales_context}
{continuity_rule_block}
{recent_customer_context}
{conversation_state}
{sales_memory_hint}
{response_style_block}
{memory_behavior_context}

PRICING:
{pricing_context}
{post_payment_context}
""".strip()
        return existing_prompt, prompt_metadata, context
