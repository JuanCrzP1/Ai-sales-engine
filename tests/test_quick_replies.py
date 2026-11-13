"""Respuestas rápidas: mensajes guardados del negocio que el equipo pone en un chat (Configuración → Respuestas rápidas).

Con la base real (SQLite, con las mismas restricciones que la migración 0015) y el panel «en la nube»:
- el atajo se normaliza («/Crédito » → «credito») y no se repite en el negocio; otro negocio sí puede usarlo;
- de 1 a 10 mensajes no vacíos, categoría opcional, máximo 500 por negocio, con los problemas por campo;
- cada negocio solo ve y toca las suyas: una ajena responde igual que una inexistente;
- crear, editar y borrar es del dueño; verlas y marcarlas como usadas, de quien llega al negocio;
- las más usadas salen primero, y `{nombre}` se cambia por el primer nombre del cliente.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.admin_api.main import create_app
from app.business_config_application.access import BusinessAccess
from app.business_config_application.quick_replies import QuickRepliesService
from app.domain.business_config import quick_replies as domain
from app.domain.business_config.access import Principal
from app.domain.business_config.errors import InvalidFieldsError, NotAllowedError
from app.infrastructure.business_config.database import build_business_config_service, create_business_config_engine, create_local_schema
from app.infrastructure.business_config.example_businesses import import_example, load_example
from app.infrastructure.business_config.members_store import BusinessMembersStore
from app.infrastructure.business_config.quick_reply_store import QuickReplyStore
from app.infrastructure.business_config.tables import business_members, tenants
from app.infrastructure.business_config.usage_store import UsageCounterStore

ANA = Principal(user_id="usuario-ana", email="ana@example.com")
BETO = Principal(user_id="usuario-beto", email="beto@example.com")
PRICES = {"shortcut": "precios", "category": "precios", "pieces": [{"kind": "text", "text": "Hola {nombre}, el combo vale $25.000."}]}


class Tokens:
    def verify(self, token: str) -> Principal | None:
        return {"token-de-ana": ANA, "token-de-beto": BETO}.get(token)


def _as(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer token-de-{user}"}


@pytest.fixture
def cloud(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'rapidas.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    for slug in ("restaurant", "saas"):
        import_example(service, load_example(slug))
    with engine.begin() as conn:
        ids = {row.slug: row.id for row in conn.execute(select(tenants.c.slug, tenants.c.id))}
        for slug, user in (("restaurant", ANA), ("saas", BETO)):
            conn.execute(business_members.insert().values(tenant_id=ids[slug], user_id=user.user_id, role="owner", created_at=datetime.now(timezone.utc)))
    access = BusinessAccess(service, BusinessMembersStore(engine))
    app = create_app(service, access=access, verifier=Tokens(), usage=UsageCounterStore(engine), quick_replies=QuickReplyStore(engine))
    yield TestClient(app), engine, access
    engine.dispose()


def _base(slug: str = "restaurant") -> str:
    return f"/api/businesses/{slug}/quick-replies"


# ---------------------------------------------------------------------------------------------------------- reglas (dominio)


@pytest.mark.parametrize(
    "written, stored",
    [("precios", "precios"), ("/Precios", "precios"), ("  Saludo   Inicial ", "saludo inicial"), ("Crédito", "credito"), ("#envio_gratis", "envio_gratis")],
)
def test_the_shortcut_is_stored_normalized(written, stored):
    assert domain.validated(shortcut=written, pieces=["Hola"]).shortcut == stored


@pytest.mark.parametrize(
    "payload, path",
    [
        ({"shortcut": "", "pieces": ["Hola"]}, "shortcut"),
        ({"shortcut": "hola!", "pieces": ["Hola"]}, "shortcut"),
        ({"shortcut": "a" * 41, "pieces": ["Hola"]}, "shortcut"),
        ({"shortcut": "hola", "pieces": []}, "pieces"),
        ({"shortcut": "hola", "pieces": ["Hola"] * 11}, "pieces"),
        ({"shortcut": "hola", "pieces": ["Hola", "   "]}, "pieces[1].text"),
        ({"shortcut": "hola", "pieces": ["x" * (domain.MAX_TEXT_CHARS + 1)]}, "pieces[0].text"),
        ({"shortcut": "hola", "category": "c" * 41, "pieces": ["Hola"]}, "category"),
        ({"shortcut": "hola", "category": 5, "pieces": ["Hola"]}, "category"),
    ],
)
def test_each_problem_comes_back_on_its_field(payload, path):
    with pytest.raises(InvalidFieldsError) as error:
        domain.validated(**payload)
    assert [issue.path for issue in error.value.issues] == [path]


def test_the_category_is_tidied_and_empty_means_none():
    assert domain.validated(shortcut="a", category="  pagos   y envíos ", pieces=["x"]).category == "Pagos y envíos"
    assert domain.validated(shortcut="a", category="   ", pieces=["x"]).category is None


@pytest.mark.parametrize(
    "text, name, filled",
    [
        ("Hola {nombre}, ¿cómo vas?", "maría fernanda gómez", "Hola María, ¿cómo vas?"),
        ("Hola {nombre}, ¿cómo vas?", None, "Hola, ¿cómo vas?"),
        ("{nombre}: tu pedido salió", "", ": tu pedido salió"),
        ("Sin nombre aquí", "Laura", "Sin nombre aquí"),
    ],
)
def test_name_is_the_first_name_of_the_customer_or_disappears(text, name, filled):
    assert domain.fill_name(text, name) == filled


# ---------------------------------------------------------------------------------------------------------- en la API


def test_create_list_edit_use_and_delete(cloud):
    client, _engine, _access = cloud
    created = client.post(_base(), headers=_as("ana"), json=PRICES)
    assert created.status_code == 201, created.text
    reply = created.json()
    assert reply["shortcut"] == "precios" and reply["category"] == "Precios" and reply["use_count"] == 0
    assert reply["pieces"] == [{"kind": "text", "text": "Hola {nombre}, el combo vale $25.000."}]

    second = client.post(_base(), headers=_as("ana"), json={"shortcut": "pago", "pieces": [{"kind": "text", "text": "Uno"}, {"kind": "text", "text": "Dos"}]}).json()
    assert second["category"] is None and [piece["text"] for piece in second["pieces"]] == ["Uno", "Dos"]

    # Las más usadas primero.
    for _ in range(2):
        assert client.post(f"{_base()}/{second['id']}/use", headers=_as("ana")).status_code == 200
    listed = client.get(_base(), headers=_as("ana")).json()
    assert listed["can_manage"] is True
    assert [(item["shortcut"], item["use_count"]) for item in listed["quick_replies"]] == [("pago", 2), ("precios", 0)]
    assert listed["quick_replies"][0]["last_used_at"]

    edited = client.put(f"{_base()}/{reply['id']}", headers=_as("ana"), json={**PRICES, "shortcut": "Precio Combo", "category": ""})
    assert edited.status_code == 200 and edited.json()["shortcut"] == "precio combo" and edited.json()["category"] is None

    assert client.delete(f"{_base()}/{reply['id']}", headers=_as("ana")).status_code == 204
    assert [item["shortcut"] for item in client.get(_base(), headers=_as("ana")).json()["quick_replies"]] == ["pago"]
    assert client.delete(f"{_base()}/{reply['id']}", headers=_as("ana")).status_code == 404


def test_a_shortcut_is_unique_in_the_business_but_not_across_businesses(cloud):
    client, _engine, _access = cloud
    assert client.post(_base(), headers=_as("ana"), json=PRICES).status_code == 201
    repeated = client.post(_base(), headers=_as("ana"), json={**PRICES, "shortcut": "/Precios"})
    assert repeated.status_code == 422 and repeated.json()["issues"][0]["path"] == "shortcut"
    other = client.post(_base(), headers=_as("ana"), json={**PRICES, "shortcut": "otra"}).json()
    renamed = client.put(f"{_base()}/{other['id']}", headers=_as("ana"), json={**PRICES, "shortcut": "precios"})
    assert renamed.status_code == 422 and renamed.json()["issues"][0]["path"] == "shortcut"
    # Otro negocio puede tener el mismo atajo.
    assert client.post(_base("saas"), headers=_as("beto"), json=PRICES).status_code == 201


def test_invalid_fields_come_back_with_their_path(cloud):
    client, _engine, _access = cloud
    response = client.post(_base(), headers=_as("ana"), json={"shortcut": "hola", "pieces": [{"kind": "text", "text": "Uno"}, {"kind": "text", "text": " "}]})
    assert response.status_code == 422
    assert response.json()["issues"] == [{"path": "pieces[1].text", "message": "El mensaje 2 está vacío: escríbelo o quítalo."}]


def test_each_business_only_sees_and_touches_its_own(cloud):
    client, _engine, _access = cloud
    mine = client.post(_base(), headers=_as("ana"), json=PRICES).json()
    # Beto no llega al restaurante: responde como si no existiera.
    assert client.get(_base(), headers=_as("beto")).status_code == 404
    assert client.post(_base(), headers=_as("beto"), json=PRICES).status_code == 404
    # Ni siquiera con el id de una respuesta ajena desde su propio negocio.
    assert client.put(f"{_base('saas')}/{mine['id']}", headers=_as("beto"), json=PRICES).status_code == 404
    assert client.delete(f"{_base('saas')}/{mine['id']}", headers=_as("beto")).status_code == 404
    assert client.post(f"{_base('saas')}/{mine['id']}/use", headers=_as("beto")).status_code == 404
    assert client.post(f"{_base('saas')}/no-es-un-id/use", headers=_as("beto")).status_code == 404
    assert [item["shortcut"] for item in client.get(_base(), headers=_as("ana")).json()["quick_replies"]] == ["precios"]
    assert client.get(_base(), headers={"Authorization": "Bearer otro"}).status_code == 401


def test_only_whoever_organizes_the_business_creates_edits_and_deletes(cloud):
    """Hoy solo existe el rol de dueño. Un miembro que no lo sea (los asesores, cuando existan) las ve y las usa, pero no las cambia."""
    _client, engine, access = cloud
    service = QuickRepliesService(QuickReplyStore(engine), access)
    reply = service.create(ANA, "restaurant", PRICES)

    class Advisor:
        def is_member(self, tenant_slug, user_id):
            return True

        def is_owner(self, tenant_slug, user_id):
            return False

        def slugs_of(self, user_id):
            return {"restaurant"}

        def role_of(self, tenant_slug, user_id):
            return "agent"

        def roles_of(self, user_id):
            return {"restaurant": "agent"}

    advisor_access = BusinessAccess(access._configs, Advisor())  # noqa: SLF001 - los mismos negocios con otro rol
    as_advisor = QuickRepliesService(QuickReplyStore(engine), advisor_access)
    view = as_advisor.view(BETO, "restaurant")
    assert view.can_manage is False and [item.shortcut for item in view.replies] == ["precios"]
    assert as_advisor.mark_used(BETO, "restaurant", reply.id).use_count == 1
    for action in (
        lambda: as_advisor.create(BETO, "restaurant", {**PRICES, "shortcut": "otra"}),
        lambda: as_advisor.update(BETO, "restaurant", reply.id, PRICES),
        lambda: as_advisor.delete(BETO, "restaurant", reply.id),
    ):
        with pytest.raises(NotAllowedError):
            action()


def test_a_business_has_at_most_500(cloud, monkeypatch):
    client, _engine, _access = cloud
    monkeypatch.setattr("app.infrastructure.business_config.quick_reply_store.MAX_QUICK_REPLIES", 2)
    for shortcut in ("uno", "dos"):
        assert client.post(_base(), headers=_as("ana"), json={**PRICES, "shortcut": shortcut}).status_code == 201
    full = client.post(_base(), headers=_as("ana"), json={**PRICES, "shortcut": "tres"})
    assert full.status_code == 422 and "máximo" in full.json()["message"]


def test_without_the_store_the_panel_says_it_is_not_available(tmp_path):
    engine = create_business_config_engine(f"sqlite:///{(tmp_path / 'sin.sqlite3').as_posix()}")
    create_local_schema(engine)
    service = build_business_config_service(engine, secrets_key="x" * 43 + "=")
    import_example(service, load_example("restaurant"))
    client = TestClient(create_app(service), base_url="http://127.0.0.1", client=("127.0.0.1", 50000))
    response = client.get(_base())
    assert response.status_code == 503
    engine.dispose()


# ---------------------------------------------------------------------------------------------------- archivos en las respuestas

PDF = b"%PDF-1.7 catalogo"


def _upload(client, content=PDF, mime="application/pdf", name="Catálogo.pdf", user="ana", slug="restaurant"):
    from urllib.parse import quote

    headers = {**_as(user), "Content-Type": mime, "X-File-Name": quote(name)}
    return client.post(f"{_base(slug)}/files", content=content, headers=headers)


def test_a_reply_mixes_texts_and_files_and_the_file_is_kept_with_the_business(cloud):
    client, _engine, _access = cloud
    uploaded = _upload(client)
    assert uploaded.status_code == 201, uploaded.text
    file = uploaded.json()
    assert (file["file_name"], file["mime_type"], file["size_bytes"]) == ("Catálogo.pdf", "application/pdf", len(PDF))
    payload = {"shortcut": "catalogo", "pieces": [{"kind": "text", "text": "Hola {nombre} 👋"}, {"kind": "file", "file_id": file["file_id"], "text": "Nuestro catálogo"}]}
    created = client.post(_base(), headers=_as("ana"), json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["pieces"] == [
        {"kind": "text", "text": "Hola {nombre} 👋"},
        {"kind": "file", "text": "Nuestro catálogo", "file_id": file["file_id"], "file_name": "Catálogo.pdf", "mime_type": "application/pdf", "size_bytes": len(PDF)},
    ]
    shown = client.get(f"{_base()}/files/{file['file_id']}", headers=_as("ana"))
    assert (shown.status_code, shown.content, shown.headers["x-content-type-options"]) == (200, PDF, "nosniff")
    # Otro negocio no lo ve ni lo puede usar.
    assert client.get(f"{_base('restaurant')}/files/{file['file_id']}", headers=_as("beto")).status_code == 404
    foreign = client.post(_base("saas"), headers=_as("beto"), json={**payload, "shortcut": "robado"})
    assert foreign.status_code == 422 and foreign.json()["issues"] == [{"path": "pieces[1].file", "message": "Ese archivo ya no está guardado: vuelve a subirlo."}]


def test_a_file_that_cannot_be_sent_is_not_kept(cloud):
    client, _engine, _access = cloud
    assert _upload(client, b"MZ", "application/x-msdownload", "virus.exe").status_code == 422
    assert _upload(client, b"\xff\xd8\xff foto", "application/pdf").json()["message"].startswith("El archivo no es lo que dice ser")
    assert _upload(client, user="beto").status_code == 404


@pytest.mark.parametrize(
    "piece, path",
    [({"kind": "file", "file_id": "no-es-un-id"}, "pieces[0].file"), ({"kind": "file", "file_id": "0" * 8 + "-0000-0000-0000-" + "0" * 12, "text": "x" * 1025}, "pieces[0].text"), ({"kind": "video"}, "pieces[0]")],
)
def test_a_bad_file_piece_comes_back_on_its_field(piece, path):
    with pytest.raises(InvalidFieldsError) as error:
        domain.validated(shortcut="a", pieces=[piece])
    assert [issue.path for issue in error.value.issues] == [path]


def test_files_nobody_uses_are_cleaned_after_an_hour(cloud):
    from datetime import timedelta

    from sqlalchemy import update

    from app.infrastructure.business_config.tables import quick_reply_files

    client, engine, _access = cloud
    kept = _upload(client, name="usado.pdf").json()["file_id"]
    loose = _upload(client, name="suelto.pdf").json()["file_id"]
    reply = client.post(_base(), headers=_as("ana"), json={"shortcut": "c", "pieces": [{"kind": "file", "file_id": kept}]}).json()
    with engine.begin() as conn:
        conn.execute(update(quick_reply_files).values(created_at=datetime.now(timezone.utc) - timedelta(hours=2)))
    fresh = _upload(client, name="nuevo.pdf").json()["file_id"]
    status = lambda file_id: client.get(f"{_base()}/files/{file_id}", headers=_as("ana")).status_code  # noqa: E731
    assert (status(kept), status(loose), status(fresh)) == (200, 404, 200)
    # Al borrar la respuesta, su archivo queda suelto y también se limpia (pasada la hora).
    assert client.delete(f"{_base()}/{reply['id']}", headers=_as("ana")).status_code == 204
    with engine.begin() as conn:
        conn.execute(update(quick_reply_files).values(created_at=datetime.now(timezone.utc) - timedelta(hours=2)))
    _upload(client, name="otro.pdf")
    assert status(kept) == 404


def test_a_business_keeps_at_most_200_files(cloud, monkeypatch):
    client, _engine, _access = cloud
    monkeypatch.setattr("app.infrastructure.business_config.quick_reply_store.MAX_QUICK_REPLY_FILES", 1)
    assert _upload(client).status_code == 201
    full = _upload(client)
    assert full.status_code == 422 and "máximo de 1 archivos" in full.json()["message"]
