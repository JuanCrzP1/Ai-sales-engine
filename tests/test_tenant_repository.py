from app.infrastructure.db.repository import DBRepository


def test_get_tenant_by_slug():
    repo = DBRepository()

    tenant = repo.get_tenant_by_slug("asesor_ai_prod")

    assert tenant is not None
    assert tenant["slug"] == "asesor_ai_prod"