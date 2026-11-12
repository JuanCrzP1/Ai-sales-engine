"""Toda variable de entorno que lee el código está en la plantilla `project/.env.example`, que dice dónde va cada una (este equipo
o Vercel). Así ninguna variable nueva queda sin documentar, y quien prepara un equipo o un despliegue sabe qué poner.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "project" / ".env.example"
# Las pone el sistema o las pruebas: nadie las escribe.
SYSTEM = {"PYTEST_CURRENT_TEST", "USERNAME"}
_PYTHON = re.compile(r'(?:getenv|environ\.get)\("([A-Z][A-Z0-9_]+)"|environ\["([A-Z][A-Z0-9_]+)"\]|_(?:ENV|VAR) = "([A-Z][A-Z0-9_]+)"')
_PANEL = re.compile(r"(?:import\.meta\.env|process\.env|env)\.((?:VITE_)?[A-Z][A-Z0-9_]{3,})|env\[\"([A-Z][A-Z0-9_]+)\"\]")


def _tracked(*paths: str) -> list[Path]:
    output = subprocess.run(["git", "ls-files", *paths], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    # Un archivo movido o borrado sigue en la lista de git hasta el próximo commit: se salta.
    return [ROOT / line for line in output.splitlines() if line.endswith((".py", ".ts", ".tsx")) and (ROOT / line).exists()]


def _names(pattern: re.Pattern[str], files: list[Path]) -> set[str]:
    found: set[str] = set()
    for path in files:
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            found.update(group for group in match.groups() if group)
    return found


def test_every_variable_the_code_reads_is_in_the_template():
    template = TEMPLATE.read_text(encoding="utf-8")
    documented = set(re.findall(r"\b([A-Z][A-Z0-9_]{3,})\b", template))
    engine = _names(_PYTHON, _tracked("project/app", "scripts"))
    panel = _names(_PANEL, [path for path in _tracked("apps/admin-web/src", "apps/admin-web/vite.config.ts") if ".test." not in path.name])
    assert {"RESEND_API_KEY", "CRON_SECRET", "UAZAPI_ADMIN_TOKEN", "BUSINESS_CONFIG_SECRETS_KEY"} <= engine, "la búsqueda debe ver el motor"
    missing = sorted((engine | panel) - documented - SYSTEM)
    assert missing == [], f"variables sin documentar en project/.env.example: {missing}"


def test_production_values_are_never_written_in_the_template():
    """La parte de Vercel va comentada y sin valores: los de producción solo viven en Vercel."""
    production = TEMPLATE.read_text(encoding="utf-8").split("# 2. VERCEL", 1)[1].split("# 3. OPCIONALES", 1)[0]
    for line in production.splitlines()[1:]:
        assert not line.strip() or line.lstrip().startswith("#"), line
    assert not re.search(r"(re_[A-Za-z0-9]{8,}|sk-or-v1-[0-9a-f]{16,}|postgres(ql)?://[^@\s]+:[^@\s]+@[a-z0-9-]+\.neon\.tech)", TEMPLATE.read_text(encoding="utf-8"))
