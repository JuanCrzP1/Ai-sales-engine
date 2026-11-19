"""Seguridad del motor: ningún registro con tokens o datos de clientes.

Que un webhook solo acepte lo que trae el token de la instancia del negocio lo prueba `test_whatsapp_qr_channel.py` (el de Meta,
que exigía su firma, se retiró el 18 de noviembre de 2026).
"""
from __future__ import annotations

import re
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "project" / "app"


def test_the_engine_never_prints():
    """Un `print` termina en los registros de la nube: ahí no puede ir un token ni el mensaje de un cliente."""
    offenders = [
        f"{path.relative_to(APP_DIR)}:{number}"
        for path in APP_DIR.rglob("*.py")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if re.search(r"(?<![\w.])print\(", line)
    ]
    assert offenders == []


def test_only_the_neon_auth_verifier_uses_a_jwt_library():
    """Las cuentas de la plataforma son de Neon Auth: el panel en la nube comprueba sus tokens con PyJWT, solo en su verificador.
    La librería del sistema de cuentas anterior (`python-jose`, retirado el 18 de noviembre de 2026) sigue sin declararse."""
    project_dir = APP_DIR.parent
    declared = "".join((project_dir / name).read_text(encoding="utf-8").lower() for name in ("requirements.txt", "requirements-dev.txt"))
    assert not re.search(r"^(python-jose|jose|authlib)\b", declared, re.MULTILINE)
    assert re.search(r"^pyjwt==", declared, re.MULTILINE)
    uses = {
        path.relative_to(project_dir).as_posix()
        for path in APP_DIR.rglob("*.py")
        if re.search(r"^\s*(import jwt|from jwt)\b", path.read_text(encoding="utf-8"), re.MULTILINE)
    }
    assert uses == {"app/infrastructure/auth/neon_auth.py"}
