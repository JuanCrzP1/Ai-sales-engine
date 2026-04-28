def validate_pricing(pricing: dict) -> None:
    if "plans" in pricing:
        return

    if "catalog" in pricing:
        return

    raise RuntimeError("pricing debe tener 'plans' o 'catalog'")


class RuntimeYamlBuilder:

    REQUIRED_KEYS = ["sales", "business", "pricing", "inventory", "config"]

    def build(self, tenant_slug: str, partial_yaml: dict | None) -> dict:
        normalized_slug = str(tenant_slug or "").strip()
        incoming = partial_yaml if isinstance(partial_yaml, dict) else {}
        if not incoming:
            raise RuntimeError(f"runtime yaml missing for tenant {normalized_slug or 'unknown'}")

        raw_yaml = dict(incoming)
        self._validate(raw_yaml)

        return raw_yaml

    def _validate(self, runtime: dict):
        required = ["sales", "business", "pricing", "inventory", "config"]

        if not isinstance(runtime, dict):
            raise RuntimeError("runtime_yaml debe ser dict")

        for key in required:
            value = runtime.get(key)

            if not isinstance(value, dict) or not value:
                raise RuntimeError(f"{key} inválido o vacío en runtime_yaml")

        # validaciones mínimas críticas
        validate_pricing(runtime["pricing"])

        if "description" not in runtime["business"]:
            raise RuntimeError("business sin description")
