"""Los tokens de sesión de Neon Auth: solo pasan los firmados con sus claves EdDSA, para este emisor y vigentes.

Se firman aquí con una clave Ed25519 propia y se sirve su clave pública como lo haría `/.well-known/jwks.json`.
"""
from __future__ import annotations

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jwt import PyJWK
from jwt.algorithms import OKPAlgorithm
from jwt.exceptions import PyJWKClientError

from app.domain.business_config.access import Principal
from app.infrastructure.auth.neon_auth import NeonAuthVerifier, auth_origin

AUTH_URL = "https://ep-ejemplo.neonauth.us-east-1.aws.neon.tech/neondb/auth"
ORIGIN = "https://ep-ejemplo.neonauth.us-east-1.aws.neon.tech"
SIGNING_KEY = Ed25519PrivateKey.generate()
OTHER_KEY = Ed25519PrivateKey.generate()


class Keys:
    """Lo que publica Neon Auth en su JWKS: la clave pública de `kid-1`."""

    def __init__(self) -> None:
        jwk = json.loads(OKPAlgorithm.to_jwk(SIGNING_KEY.public_key()))
        self._keys = {"kid-1": PyJWK({**jwk, "kid": "kid-1", "alg": "EdDSA"})}

    def get_signing_key_from_jwt(self, token: str) -> PyJWK:
        kid = jwt.get_unverified_header(token).get("kid")
        if kid not in self._keys:
            raise PyJWKClientError("clave desconocida")
        return self._keys[kid]


def _claims(**changes) -> dict:
    now = int(time.time())
    claims = {"sub": "usuario-1", "email": "ana@example.com", "iss": ORIGIN, "aud": ORIGIN, "iat": now, "exp": now + 900, "role": "authenticated"}
    claims.update(changes)
    return {key: value for key, value in claims.items() if value is not None}


def _token(*, key=SIGNING_KEY, kid="kid-1", algorithm="EdDSA", **changes) -> str:
    return jwt.encode(_claims(**changes), key, algorithm=algorithm, headers={"kid": kid})


@pytest.fixture
def verifier() -> NeonAuthVerifier:
    return NeonAuthVerifier(AUTH_URL, jwks_client=Keys())


def test_a_session_token_says_who_the_user_is(verifier):
    assert verifier.verify(_token()) == Principal(user_id="usuario-1", email="ana@example.com")


def test_the_issuer_and_audience_are_the_origin_of_the_auth_url():
    assert auth_origin(AUTH_URL) == ORIGIN
    for bad in ("http://ep-ejemplo.neon.tech/neondb/auth", "", "ep-ejemplo.neon.tech"):
        with pytest.raises(ValueError):
            auth_origin(bad)


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(lambda: _token(exp=int(time.time()) - 120, iat=int(time.time()) - 1020), id="vencido"),
        pytest.param(lambda: _token(iss="https://otro-emisor.example.com"), id="otro_emisor"),
        pytest.param(lambda: _token(aud="https://otra-app.example.com"), id="otra_audiencia"),
        pytest.param(lambda: _token(sub=None), id="sin_usuario"),
        pytest.param(lambda: _token(sub=""), id="usuario_vacio"),
        pytest.param(lambda: _token(exp=None), id="sin_vencimiento"),
        pytest.param(lambda: _token(key=OTHER_KEY), id="firmado_con_otra_clave"),
        pytest.param(lambda: _token(kid="kid-desconocido"), id="clave_desconocida"),
        pytest.param(lambda: _token(key="secreto-compartido-de-32-bytes-o-mas-xx", algorithm="HS256"), id="otro_algoritmo"),
        pytest.param(lambda: "no-es-un-jwt", id="basura"),
        pytest.param(lambda: "", id="vacio"),
        pytest.param(lambda: "a" * 9000, id="demasiado_largo"),
    ],
)
def test_anything_else_is_rejected(verifier, token):
    assert verifier.verify(token()) is None


def test_a_token_without_email_still_identifies_the_user(verifier):
    assert verifier.verify(_token(email=None)) == Principal(user_id="usuario-1", email=None)
