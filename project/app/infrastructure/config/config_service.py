from __future__ import annotations

import importlib
import os
from pathlib import Path


class ConfigService:
    TENANT_ALIASES = {
        'viajes': 'agencia_viajes',
        'tienda_de_ropa': 'tienda_ropa',
    }

    ACTIVE_TENANT_ID = (os.getenv('ACTIVE_TENANT_SLUG') or 'asesor_ai_prod').strip() or 'asesor_ai_prod'
    DEFAULT_TENANT_ID = (os.getenv('TENANT_SLUG') or ACTIVE_TENANT_ID).strip() or ACTIVE_TENANT_ID

    SHARED_PATHS = {
        'bot_config.yaml': ('system', 'bot_config.yaml'),
        'intents.yaml': ('core', 'intents.yaml'),
        'flows.yaml': ('core', 'flows.yaml'),
        'nlu.yaml': ('core', 'nlu.yaml'),
        'intent_levels.yaml': ('core', 'intent_levels.yaml'),
        'media.yaml': ('assets', 'media.yaml'),
        'conversation_stage.yaml': ('system', 'conversation_stage.yaml'),
        'menus.yaml': ('system', 'menus.yaml'),
    }

    UNIFIED_SECTION_FILES = {
        'sales.yaml': {
            'responses.yaml': 'responses',
            'objections.yaml': 'objections',
            'offer.yaml': 'offer',
            'closing.yaml': 'closing',
        },
        'config.yaml': {
            'settings.yaml': 'settings',
            'initial_message.yaml': 'initial_message',
            'personality.yaml': 'personality',
            'conversation.yaml': 'conversation',
        },
    }

    TENANT_FIRST_FILES = {
        'business.yaml',
        'sales.yaml',
        'pricing.yaml',
        'inventory.yaml',
        'offer.yaml',
        'responses.yaml',
        'objections.yaml',
        'settings.yaml',
        'initial_message.yaml',
        'conversation.yaml',
        'personality.yaml',
        'closing.yaml',
    }

    DEFAULT_CONVERSATION = {
        'active_window_minutes': 15,
        'reset_hours': 4,
    }

    DEFAULT_INITIAL_MESSAGE_TEXT = (
        "Hola, ¿qué más? 👋\n\n"
        "Muchos negocios terminan perdiendo clientes porque no alcanzan a responder todo a tiempo.\n\n"
        "¿Te está pasando algo así o estás buscando otra cosa?"
    )

    def __init__(self, base_path: str | None = None):
        base = Path(base_path) if base_path else Path(__file__).parents[3] / 'config'
        self.base = base
        self.core_root = self.base / 'core'
        self.system_root = self.base / 'system'
        self.assets_root = self.base / 'assets'
        self.tenants_root = self.base / 'tenants'

    @staticmethod
    def _as_dict(value) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_list(value) -> list:
        return value if isinstance(value, list) else []

    @staticmethod
    def _string_list(value) -> list[str]:
        return [str(item).strip() for item in ConfigService._as_list(value) if str(item).strip()]

    @staticmethod
    def _as_bool(value, *, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default

    def _default_client_id(self, client_id: str | None = None) -> str:
        explicit = str(client_id or "").strip()
        resolved = explicit or self.DEFAULT_TENANT_ID
        normalized = self.TENANT_ALIASES.get(resolved, resolved)

        tenant_root = self.tenants_root / normalized
        if not tenant_root.exists() or not tenant_root.is_dir():
            raise ValueError(f"Tenant no encontrado: {normalized}")

        return normalized

    def _shared_path(self, filename: str) -> Path:
        location = self.SHARED_PATHS.get(filename)
        if not location:
            return self.base / filename
        root_name, relative_name = location
        root = {
            'core': self.core_root,
            'system': self.system_root,
            'assets': self.assets_root,
        }.get(root_name, self.base)
        return root / relative_name

    def _section_path(self, filename: str, client_id: str | None = None) -> Path:
        if filename in self.TENANT_FIRST_FILES:
            return self.tenants_root / self._default_client_id(client_id) / filename
        return self._shared_path(filename)

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            yaml = importlib.import_module('yaml')
            payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _load_unified_section(self, filename: str, client_id: str | None = None) -> dict | None:
        tenant_root = self.tenants_root / self._default_client_id(client_id)
        for unified_name, section_map in self.UNIFIED_SECTION_FILES.items():
            section_name = section_map.get(filename)
            if not section_name:
                continue
            unified_path = tenant_root / unified_name
            payload = self._load_yaml(unified_path)
            source_payload = payload.get('config') if isinstance(payload.get('config'), dict) else payload
            value = source_payload.get(section_name)
            if value is None:
                continue
            if isinstance(value, dict):
                return {section_name: value}
            return {section_name: value}
        return None

    def _load_raw_section(self, filename: str, client_id: str | None = None) -> dict:
        direct = self._load_yaml(self._section_path(filename, client_id))
        if direct:
            return direct
        unified = self._load_unified_section(filename, client_id)
        if unified is not None:
            return unified
        return {}

    def _has_section_file(self, filename: str, client_id: str | None = None) -> bool:
        if self._section_path(filename, client_id).exists():
            return True
        return self._load_unified_section(filename, client_id) is not None

    @staticmethod
    def _extract_named_root(payload: dict, root_key: str) -> dict:
        if not isinstance(payload, dict):
            return {}
        nested = payload.get(root_key)
        if isinstance(nested, dict):
            return nested
        return payload

    @classmethod
    def _normalize_pricing(cls, payload: dict) -> dict:
        pricing = cls._extract_named_root(payload, 'pricing')

        def _normalize_payment_block(raw_payment: object) -> dict:
            payment = cls._as_dict(raw_payment)
            raw_transfer = payment.get('transfer') if isinstance(payment.get('transfer'), dict) else {}
            raw_transfer_methods = raw_transfer.get('methods') if isinstance(raw_transfer.get('methods'), list) else []
            return {
                'link': str(payment.get('link') or '').strip(),
                'transfer': {
                    'enabled': cls._as_bool(raw_transfer.get('enabled'), default=False),
                    'methods': [dict(item) if isinstance(item, dict) else item for item in raw_transfer_methods],
                },
            }

        currencies_raw = cls._as_dict(pricing.get('currencies'))
        legacy_currency = str(pricing.get('currency') or '').strip().upper()

        supported_currencies: list[str] = []
        for item in cls._as_list(currencies_raw.get('supported')):
            code = str(item or '').strip().upper()
            if code and code not in supported_currencies:
                supported_currencies.append(code)
        if legacy_currency and legacy_currency not in supported_currencies:
            supported_currencies.append(legacy_currency)

        primary_currency = str(currencies_raw.get('primary') or '').strip().upper()
        if not primary_currency and supported_currencies:
            primary_currency = supported_currencies[0]
        if primary_currency and primary_currency not in supported_currencies:
            supported_currencies.insert(0, primary_currency)

        catalog = cls._as_dict(pricing.get('catalog'))
        normalized_catalog_payment = _normalize_payment_block(catalog.get('payment'))
        raw_categories = [item for item in cls._as_list(catalog.get('categories')) if isinstance(item, dict)]
        raw_items = [item for item in cls._as_list(catalog.get('items')) if isinstance(item, dict)]

        normalized_catalog_categories: list[dict] = []
        for category in raw_categories:
            category_id = str(category.get('id') or '').strip()
            category_name = str(category.get('name') or category_id).strip()
            if not (category_id or category_name):
                continue
            normalized_catalog_categories.append({
                'id': category_id or category_name.lower().replace(' ', '_'),
                'name': category_name,
            })

        normalized_catalog_items: list[dict] = []
        for item in raw_items:
            item_price = cls._as_dict(item.get('price'))
            normalized_price: dict[str, object] = {}
            for currency_code, value in item_price.items():
                code = str(currency_code or '').strip().upper()
                if not code or value in (None, ''):
                    continue
                normalized_price[code] = value
                if code not in supported_currencies:
                    supported_currencies.append(code)
            normalized_catalog_items.append({
                'id': str(item.get('id') or '').strip(),
                'name': str(item.get('name') or '').strip(),
                'category': str(item.get('category') or '').strip(),
                'description': str(item.get('description') or '').strip(),
                'price': normalized_price,
            })

        raw_plans = [item for item in cls._as_list(pricing.get('plans')) if isinstance(item, dict)]
        if not raw_plans:
            raw_plans = [item for item in cls._as_list(pricing.get('offers')) if isinstance(item, dict)]

        if not raw_plans and normalized_catalog_items:
            mapped_plans: list[dict] = []
            for item in normalized_catalog_items:
                item_pricing = cls._as_dict(item.get('price'))
                plan_pricing: dict[str, dict] = {}
                for code, amount in item_pricing.items():
                    currency_code = str(code or '').strip().upper()
                    if not currency_code or amount in (None, ''):
                        continue
                    plan_pricing[currency_code] = {'price': amount}
                if not plan_pricing:
                    continue
                mapped_plans.append({
                    'id': str(item.get('id') or '').strip(),
                    'name': str(item.get('name') or '').strip(),
                    'description': str(item.get('description') or '').strip(),
                    'target': str(item.get('category') or '').strip(),
                    'pricing': plan_pricing,
                    'payment': dict(normalized_catalog_payment),
                })
            if mapped_plans:
                raw_plans = mapped_plans

        legacy_default_offer = cls._as_dict(pricing.get('default_offer'))
        if not raw_plans and legacy_default_offer:
            raw_plans = [legacy_default_offer]

        if not raw_plans and any(pricing.get(key) not in (None, '') for key in ('implementation', 'monthly', 'first_payment', 'price')):
            raw_plans = [{
                'id': 'plan_unico',
                'name': 'Plan principal',
                'implementation': pricing.get('implementation'),
                'monthly': pricing.get('monthly'),
                'first_payment': pricing.get('first_payment'),
                'price': pricing.get('price'),
                'includes': pricing.get('includes'),
                'not_included': pricing.get('not_included'),
            }]

        normalized_plans: list[dict] = []
        for index, plan in enumerate(raw_plans, start=1):
            pricing_map = cls._as_dict(plan.get('pricing'))
            if not pricing_map:
                legacy_amounts = {
                    key: plan.get(key)
                    for key in ('implementation', 'monthly', 'first_payment', 'price')
                    if plan.get(key) not in (None, '')
                }
                if legacy_amounts:
                    bucket_currency = primary_currency or legacy_currency or 'DEFAULT'
                    pricing_map = {bucket_currency: legacy_amounts}

            normalized_pricing_map: dict[str, dict] = {}
            for currency_code, values in pricing_map.items():
                code = str(currency_code or '').strip().upper()
                if not code or not isinstance(values, dict):
                    continue
                clean_values = {k: v for k, v in values.items() if v not in (None, '')}
                if not clean_values:
                    continue
                normalized_pricing_map[code] = clean_values
                if code not in supported_currencies:
                    supported_currencies.append(code)

            if not normalized_pricing_map:
                continue

            normalized_plans.append({
                'id': str(plan.get('id') or f'plan_{index}').strip() or f'plan_{index}',
                'name': str(plan.get('name') or '').strip(),
                'description': str(plan.get('description') or '').strip(),
                'target': str(plan.get('target') or '').strip(),
                'pricing': normalized_pricing_map,
                'includes': cls._string_list(plan.get('includes')),
                'not_included': cls._string_list(plan.get('not_included')),
                'payment': _normalize_payment_block(plan.get('payment')),
            })

        if not primary_currency and supported_currencies:
            primary_currency = supported_currencies[0]

        model = str(pricing.get('model') or '').strip().lower()
        if model not in {'single', 'subscription', 'hybrid', 'catalog'}:
            if normalized_catalog_items:
                model = 'catalog'
            else:
                legacy_offer_type = str(pricing.get('offer_type') or '').strip().lower()
                if legacy_offer_type == 'single':
                    model = 'single'
                elif legacy_offer_type == 'multi':
                    model = 'hybrid'
                else:
                    model = 'hybrid' if len(normalized_plans) > 1 else 'single'

        custom_rules = cls._as_dict(pricing.get('custom_rules'))
        if not custom_rules:
            custom_rules = {
                'show_single_plan_as_main': len(normalized_plans) <= 1,
                'allow_multi_plan_selection': False,
            }

        primary_plan = normalized_plans[0] if normalized_plans else {}
        primary_pricing = cls._as_dict(primary_plan.get('pricing'))
        primary_currency_key = primary_currency if primary_currency in primary_pricing else (next(iter(primary_pricing.keys()), ''))
        primary_values = cls._as_dict(primary_pricing.get(primary_currency_key))

        implementation = primary_values.get('implementation')
        monthly = primary_values.get('monthly')
        first_payment = primary_values.get('first_payment')

        raw_offers = cls._as_dict(pricing.get('business_offers'))
        financing_raw = cls._as_dict(raw_offers.get('financing'))
        normalized_offers = {
            'core': cls._string_list(raw_offers.get('core')),
            'upsell': cls._string_list(raw_offers.get('upsell')),
            'cross_sell': cls._string_list(raw_offers.get('cross_sell')),
            'financing': {
                'available': cls._as_bool(financing_raw.get('available'), default=False),
                'providers': cls._string_list(financing_raw.get('providers')),
                'options': cls._string_list(financing_raw.get('options')),
            },
        }

        return {
            'currencies': {
                'primary': primary_currency,
                'supported': supported_currencies,
            },
            'exchange_reference': str(pricing.get('exchange_reference') or '').strip(),
            'model': model,
            'catalog': {
                'categories': normalized_catalog_categories,
                'items': normalized_catalog_items,
                'payment': normalized_catalog_payment,
            },
            'plans': normalized_plans,
            'payment': _normalize_payment_block(pricing.get('payment')),
            'custom_rules': custom_rules,
            'conditions': cls._string_list(pricing.get('conditions')),
            'currency': primary_currency,
            'implementation': implementation,
            'monthly': monthly,
            'first_payment': first_payment,
            'price_framing': cls._as_dict(pricing.get('price_framing')),
            'price_objection_rules': cls._as_dict(pricing.get('price_objection_rules')),
            'hard_rules': cls._string_list(pricing.get('hard_rules')),
            'examples': [item for item in cls._as_list(pricing.get('examples')) if isinstance(item, dict)],
            'roi_hints': cls._string_list(pricing.get('roi_hints')),
            'note': str(pricing.get('note') or '').strip(),
            'strategy': cls._as_dict(pricing.get('strategy')),
            'business_offers': normalized_offers,
        }

    @classmethod
    def _normalize_features(cls, payload: dict) -> dict:
        source = payload.get('config') if isinstance(payload.get('config'), dict) else payload
        source = source if isinstance(source, dict) else {}
        features = source.get('features') if isinstance(source.get('features'), dict) else {}
        business_model = str(features.get('business_model') or source.get('business_model') or '').strip().lower()
        if business_model not in {'saas', 'catalog', 'service_booking', 'checkout', 'process'}:
            business_model = ''
        return {
            'pricing_enabled': cls._as_bool(features.get('pricing_enabled'), default=True),
            'multi_currency': cls._as_bool(features.get('multi_currency'), default=False),
            'multi_plan': cls._as_bool(features.get('multi_plan'), default=False),
            'catalog_mode': cls._as_bool(features.get('catalog_mode'), default=False),
            'business_model': business_model,
        }

    @classmethod
    def _normalize_business(cls, payload: dict) -> dict:
        business = cls._extract_named_root(payload, 'business')
        location = cls._as_dict(business.get('location'))
        coverage = cls._as_dict(location.get('coverage'))

        logistics = cls._as_dict(business.get('logistics'))
        delivery = cls._as_dict(logistics.get('delivery'))
        delivery_cost = cls._as_dict(delivery.get('cost'))
        delivery_time = cls._as_dict(delivery.get('time'))

        shipping = cls._as_dict(logistics.get('shipping'))
        shipping_cost = cls._as_dict(shipping.get('cost'))
        shipping_time = cls._as_dict(shipping.get('time'))

        pickup = cls._as_dict(logistics.get('pickup'))
        scheduling = cls._as_dict(logistics.get('scheduling'))

        return {
            'name': str(business.get('name') or '').strip(),
            'brand_name': str(business.get('brand_name') or '').strip(),
            'description': str(business.get('description') or '').strip(),
            'industry': str(business.get('industry') or '').strip(),
            'tone': str(business.get('tone') or '').strip(),
            'voice': str(business.get('voice') or '').strip(),
            'city': str(business.get('city') or '').strip(),
            'promise': str(business.get('promise') or '').strip(),
            'positioning': str(business.get('positioning') or '').strip(),
            'differentiators': cls._string_list(business.get('differentiators')),
            'customer_profile': cls._as_dict(business.get('customer_profile')),
            'pain_points': cls._string_list(business.get('pain_points')),
            'desired_outcomes': cls._string_list(business.get('desired_outcomes')),
            'credibility': cls._string_list(business.get('credibility')),
            'value_drivers': cls._as_dict(business.get('value_drivers')),
            'buying_motivation': cls._as_dict(business.get('buying_motivation')),
            'use_cases': [item for item in cls._as_list(business.get('use_cases')) if isinstance(item, dict)],
            'offer_type': str(business.get('offer_type') or '').strip().lower(),
            'mandatory_base_message': str(business.get('mandatory_base_message') or '').strip(),
            'location': {
                'type': str(location.get('type') or '').strip().lower(),
                'address': str(location.get('address') or '').strip(),
                'city': str(location.get('city') or business.get('city') or '').strip(),
                'coverage': {
                    'type': str(coverage.get('type') or '').strip().lower(),
                    'zones': cls._string_list(coverage.get('zones')),
                },
            },
            'service_modes': cls._string_list(business.get('service_modes')),
            'logistics': {
                'delivery': {
                    'available': cls._as_bool(delivery.get('available'), default=False),
                    'type': str(delivery.get('type') or '').strip().lower(),
                    'zones': cls._string_list(delivery.get('zones')),
                    'cost': {
                        'type': str(delivery_cost.get('type') or '').strip().lower(),
                        'value': delivery_cost.get('value'),
                    },
                    'time': {
                        'min': str(delivery_time.get('min') or '').strip(),
                        'max': str(delivery_time.get('max') or '').strip(),
                    },
                },
                'shipping': {
                    'available': cls._as_bool(shipping.get('available'), default=False),
                    'scope': str(shipping.get('scope') or '').strip().lower(),
                    'providers': cls._string_list(shipping.get('providers')),
                    'cost': {
                        'type': str(shipping_cost.get('type') or '').strip().lower(),
                        'value': shipping_cost.get('value'),
                    },
                    'time': {
                        'min': str(shipping_time.get('min') or '').strip(),
                        'max': str(shipping_time.get('max') or '').strip(),
                    },
                },
                'pickup': {
                    'available': cls._as_bool(pickup.get('available'), default=False),
                    'instructions': str(pickup.get('instructions') or '').strip(),
                },
                'scheduling': {
                    'required': cls._as_bool(scheduling.get('required'), default=False),
                },
            },
        }

    @classmethod
    def _normalize_sales(cls, payload: dict) -> dict:
        sales = cls._extract_named_root(payload, 'sales')
        return {
            'discovery': cls._as_dict(sales.get('discovery')),
            'qualification': cls._as_dict(sales.get('qualification')),
            'support': cls._as_dict(sales.get('support')),
            'pain': cls._as_dict(sales.get('pain')),
            'angles': cls._as_dict(sales.get('angles')),
            'conversation_flow': cls._as_dict(sales.get('conversation_flow')),
            'solution': cls._as_dict(sales.get('solution')),
            'offer': cls._as_dict(sales.get('offer')),
            'objection': cls._as_dict(sales.get('objection')),
            'closing': cls._as_dict(sales.get('closing')),
            'progression_rules': cls._as_dict(sales.get('progression_rules')),
        }

    def load_sales(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('sales.yaml', client_id)
        return {'sales': self._normalize_sales(payload)}

    def load_pricing(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('pricing.yaml', client_id)
        return self._normalize_pricing(payload)

    def load_inventory(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('inventory.yaml', client_id)
        inventory = self._extract_named_root(payload, 'inventory')
        return inventory if isinstance(inventory, dict) else {}

    def load_business(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('business.yaml', client_id)
        return {'business': self._normalize_business(payload)}

    def load_offer(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('offer.yaml', client_id)
        offer = self._extract_named_root(payload, 'offer')
        if not isinstance(offer, dict):
            offer = {}
        if not isinstance(offer.get('pricing'), dict):
            offer['pricing'] = self.load_pricing(client_id)
        return offer

    def load_settings(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('settings.yaml', client_id)
        settings = self._extract_named_root(payload, 'settings')
        return settings if isinstance(settings, dict) else {}

    def load_features(self, client_id: str | None = None) -> dict:
        tenant_root = self.tenants_root / self._default_client_id(client_id)
        payload = self._load_yaml(tenant_root / 'config.yaml')
        return self._normalize_features(payload)

    def load_initial_message(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('initial_message.yaml', client_id)
        initial_message = self._extract_named_root(payload, 'initial_message')
        cfg = initial_message if isinstance(initial_message, dict) else {}
        if cfg and not str(cfg.get('text') or '').strip():
            cfg = {**cfg, 'text': self.DEFAULT_INITIAL_MESSAGE_TEXT}
        return {'initial_message': cfg}

    def load_conversation(self, client_id: str | None = None) -> dict:
        tenant_root = self.tenants_root / self._default_client_id(client_id)
        payload = self._load_yaml(tenant_root / 'config.yaml')
        source_payload = payload.get('config') if isinstance(payload.get('config'), dict) else payload
        raw = source_payload.get('conversation') if isinstance(source_payload.get('conversation'), dict) else {}

        merged = {
            **self.DEFAULT_CONVERSATION,
            **(raw if isinstance(raw, dict) else {}),
        }

        try:
            active_window_minutes = int(merged.get('active_window_minutes', self.DEFAULT_CONVERSATION['active_window_minutes']) or self.DEFAULT_CONVERSATION['active_window_minutes'])
        except (TypeError, ValueError):
            active_window_minutes = self.DEFAULT_CONVERSATION['active_window_minutes']

        try:
            reset_hours = int(merged.get('reset_hours', self.DEFAULT_CONVERSATION['reset_hours']) or self.DEFAULT_CONVERSATION['reset_hours'])
        except (TypeError, ValueError):
            reset_hours = self.DEFAULT_CONVERSATION['reset_hours']

        return {
            'active_window_minutes': max(0, active_window_minutes),
            'reset_hours': max(0, reset_hours),
        }

    def load_response_config(self, client_id: str | None = None) -> dict:
        tenant_root = self.tenants_root / self._default_client_id(client_id)
        payload = self._load_yaml(tenant_root / 'config.yaml')
        source_payload = payload.get('config') if isinstance(payload.get('config'), dict) else payload
        raw = source_payload.get('response') if isinstance(source_payload.get('response'), dict) else {}
        defaults: dict = {'length': 'short', 'max_words': 80}
        merged = {**defaults, **(raw if isinstance(raw, dict) else {})}
        try:
            merged['max_words'] = max(20, int(merged.get('max_words') or defaults['max_words']))
        except (TypeError, ValueError):
            merged['max_words'] = defaults['max_words']
        return merged

    def load_capabilities(self, client_id: str | None = None) -> dict:
        tenant_root = self.tenants_root / self._default_client_id(client_id)
        payload = self._load_yaml(tenant_root / 'config.yaml')
        source_payload = payload.get('config') if isinstance(payload.get('config'), dict) else payload
        capabilities = source_payload.get('capabilities') if isinstance(source_payload.get('capabilities'), dict) else {}
        return dict(capabilities) if isinstance(capabilities, dict) else {}

    def load_responses(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('responses.yaml', client_id)
        responses = self._extract_named_root(payload, 'responses')
        return {'responses': responses if isinstance(responses, dict) else {}}

    def load_objections(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('objections.yaml', client_id)
        objections = self._extract_named_root(payload, 'objections')
        return {'objections': objections if isinstance(objections, dict) else {}}

    def load_intents(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('intents.yaml', client_id)
        intents = self._extract_named_root(payload, 'intents')
        return {'intents': intents if isinstance(intents, dict) else {}}

    def load_nlu(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('nlu.yaml', client_id)
        nlu = self._extract_named_root(payload, 'nlu')
        return {'nlu': nlu if isinstance(nlu, dict) else {}}

    def load_intent_levels(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('intent_levels.yaml', client_id)
        return payload if isinstance(payload, dict) else {}

    def load_media(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('media.yaml', client_id)
        media = self._extract_named_root(payload, 'media')
        return {'media': media if isinstance(media, dict) else {}}

    def load_menus(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('menus.yaml', client_id)
        return payload if isinstance(payload, dict) else {}

    def load_flows(self, client_id: str | None = None) -> dict:
        payload = self._load_raw_section('flows.yaml', client_id)
        flows = self._extract_named_root(payload, 'flows')
        return {'flows': flows if isinstance(flows, dict) else {}}

    def load_config(self, tenant_id: str | None = None) -> dict:
        initial_message_payload = self.load_initial_message(client_id=tenant_id)
        initial_message = initial_message_payload.get('initial_message') if isinstance(initial_message_payload.get('initial_message'), dict) else {}
        conversation = self.load_conversation(client_id=tenant_id)
        return {
            'business': self.load_business(client_id=tenant_id),
            'pricing': self.load_pricing(client_id=tenant_id),
            'sales': self.load_sales(client_id=tenant_id),
            'inventory': self.load_inventory(client_id=tenant_id),
            'settings': self.load_settings(client_id=tenant_id),
            'features': self.load_features(client_id=tenant_id),
            'offer': self.load_offer(client_id=tenant_id),
            'initial_message': initial_message if isinstance(initial_message, dict) else {},
            'conversation': conversation if isinstance(conversation, dict) else dict(self.DEFAULT_CONVERSATION),
            'response': self.load_response_config(client_id=tenant_id),
            'capabilities': self.load_capabilities(client_id=tenant_id),
        }
