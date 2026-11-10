"""Quién usa el panel y a qué negocios llega.

En la nube cada persona entra con su cuenta y solo llega a los negocios de los que es miembro: un negocio nunca se cruza
entre usuarios. En este equipo, sin cuentas, quien usa el panel es el operador local y administra todos los negocios.
"""
from __future__ import annotations

from dataclasses import dataclass

# Quien crea un negocio es su dueño. Es el único papel de esta versión.
OWNER = "owner"


@dataclass(frozen=True)
class Principal:
    """Quien hace la petición: el usuario de la cuenta (`user_id` es el identificador de Neon Auth) o el operador local."""

    user_id: str
    email: str | None = None
    local_operator: bool = False

    @property
    def label(self) -> str:
        """Cómo queda registrado en el historial de versiones."""
        return self.email or self.user_id


# Solo existe en la API local, que solo atiende a este equipo. La API de la nube nunca lo crea: allí todo usuario viene de un token.
LOCAL_OPERATOR = Principal(user_id="panel-local", local_operator=True)
