from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_SETTINGS_DIR = Path(__file__).resolve().parent / "config" / "settings"
_SETTINGS_FILE = _SETTINGS_DIR / "__init__.py"
_spec = spec_from_file_location(
    "app_config_settings_module",
    _SETTINGS_FILE,
    submodule_search_locations=[str(_SETTINGS_DIR)],
)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load settings module: {_SETTINGS_FILE}")

_settings_module = module_from_spec(_spec)
sys.modules[_spec.name] = _settings_module
_spec.loader.exec_module(_settings_module)

for _name in dir(_settings_module):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_settings_module, _name)

__all__ = [name for name in globals() if not name.startswith("_")]
