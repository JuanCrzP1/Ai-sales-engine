"""Regenera la referencia congelada de un negocio de ejemplo a partir de lo que publica hoy (después de cambiarlo a propósito).

Conserva el orden de las claves que produce el compilador: el del cierre (`sales.closing`) es el que tenían los YAML y el motor lo
lleva tal cual en sus metadatos (`test_business_config_closing_policy.py` lo comprueba).

    python tests/golden/regenerate.py <negocio> [<negocio> ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "project"))

from app.domain.business_config.compiler import comparable_with_yaml, compile_business_config  # noqa: E402
from app.infrastructure.business_config.example_businesses import load_example  # noqa: E402

for slug in sys.argv[1:]:
    example = load_example(slug)
    sections = comparable_with_yaml(compile_business_config(example.config(), example.payment_resolver()))
    (Path(__file__).parent / f"{slug}.json").write_text(json.dumps(sections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] {slug}")
