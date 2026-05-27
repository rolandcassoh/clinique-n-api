"""Tests API — endpoints Tag."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tag.infrastructure.models import TagModel  # noqa: F401 — enregistrement metadata


@pytest.mark.asyncio
async def test_list_tags_returns_200(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/tags")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_tags_filters_by_type(api_client: AsyncClient, db: AsyncSession) -> None:
    blog_tag = TagModel(name="Blog Tag", slug="blog-tag-test", type="blog")
    product_tag = TagModel(name="Product Tag", slug="product-tag-test", type="product")
    db.add(blog_tag)
    db.add(product_tag)
    await db.flush()

    response = await api_client.get("/api/tags?type=blog")
    assert response.status_code == 200
    data = response.json()
    assert all(t["type"] == "blog" for t in data if t["type"] is not None)


@pytest.mark.asyncio
async def test_list_tags_search_filter(api_client: AsyncClient, db: AsyncSession) -> None:
    tag = TagModel(name="Dermatologie", slug="dermatologie-tag", type="doctor")
    db.add(tag)
    await db.flush()

    response = await api_client.get("/api/tags?search=Derma")
    assert response.status_code == 200
    slugs = [t["slug"] for t in response.json()]
    assert "dermatologie-tag" in slugs


@pytest.mark.asyncio
async def test_get_tag_not_found(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/tags/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_tag_requires_auth(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/admin/tags",
        json={"name": "Test", "slug": "test-slug-noauth", "type": "blog"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_tag_with_admin_token(admin_client: AsyncClient) -> None:
    response = await admin_client.post(
        "/api/admin/tags",
        json={"name": "Admin Tag", "slug": "admin-tag-unique", "type": "blog"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "admin-tag-unique"
    assert data["type"] == "blog"


@pytest.mark.asyncio
async def test_create_tag_duplicate_slug_returns_409(admin_client: AsyncClient) -> None:
    payload = {"name": "Dup", "slug": "dup-slug-409", "type": None}
    await admin_client.post("/api/admin/tags", json=payload)
    response = await admin_client.post("/api/admin/tags", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_tag_soft_deletes(admin_client: AsyncClient) -> None:
    create_resp = await admin_client.post(
        "/api/admin/tags",
        json={"name": "To Delete", "slug": "to-delete-tag", "type": None},
    )
    assert create_resp.status_code == 201
    tag_id = create_resp.json()["id"]

    delete_resp = await admin_client.delete(f"/api/admin/tags/{tag_id}")
    assert delete_resp.status_code == 204

    get_resp = await admin_client.get(f"/api/tags/{tag_id}")
    assert get_resp.status_code == 404
