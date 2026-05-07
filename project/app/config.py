from __future__ import annotations

import app.config_core as _config_core

for _name in dir(_config_core):
	if _name.startswith("_"):
		continue
	globals()[_name] = getattr(_config_core, _name)

__all__ = [name for name in globals() if not name.startswith("_")]
