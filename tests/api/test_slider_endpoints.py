"""Tests API — endpoints Slider."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.slider.infrastructure.models import SliderModel  # noqa: F401


@pytest.mark.asyncio
async def test_list_sliders_returns_only_active(api_client: AsyncClient, db: AsyncSession) -> None:
    active = SliderModel(
        title="Active Slider", image="https://example.com/a.jpg",
        position=0, is_active=True,
    )
    inactive = SliderModel(
        title="Inactive Slider", image="https://example.com/b.jpg",
        position=1, is_active=False,
    )
    db.add(active)
    db.add(inactive)
    await db.flush()

    response = await api_client.get("/api/sliders")
    assert response.status_code == 200
    titles = [s["title"] for s in response.json()]
    assert "Active Slider" in titles
    assert "Inactive Slider" not in titles


@pytest.mark.asyncio
async def test_list_sliders_ordered_by_position(api_client: AsyncClient, db: AsyncSession) -> None:
    s1 = SliderModel(title="Third", image="https://example.com/c.jpg", position=30, is_active=True)
    s2 = SliderModel(title="First", image="https://example.com/d.jpg", position=10, is_active=True)
    s3 = SliderModel(title="Second", image="https://example.com/e.jpg", position=20, is_active=True)
    for s in (s1, s2, s3):
        db.add(s)
    await db.flush()

    response = await api_client.get("/api/sliders")
    assert response.status_code == 200
    relevant = [s for s in response.json() if s["title"] in ("First", "Second", "Third")]
    positions = [s["position"] for s in relevant]
    assert positions == sorted(positions)


@pytest.mark.asyncio
async def test_create_slider_requires_auth(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/admin/sliders",
        json={"title": "No Auth", "image": "https://example.com/x.jpg"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_slider_with_admin(admin_client: AsyncClient) -> None:
    response = await admin_client.post(
        "/api/admin/sliders",
        json={
            "title": "New Slider",
            "image": "https://example.com/new.jpg",
            "position": 5,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Slider"
    assert data["position"] == 5


@pytest.mark.asyncio
async def test_reorder_slider(admin_client: AsyncClient) -> None:
    create_resp = await admin_client.post(
        "/api/admin/sliders",
        json={"title": "Reorderable", "image": "https://example.com/r.jpg", "position": 1},
    )
    assert create_resp.status_code == 201
    slider_id = create_resp.json()["id"]

    reorder_resp = await admin_client.patch(
        f"/api/admin/sliders/{slider_id}/reorder",
        json={"position": 99},
    )
    assert reorder_resp.status_code == 200
    assert reorder_resp.json()["position"] == 99


@pytest.mark.asyncio
async def test_delete_slider(admin_client: AsyncClient, api_client: AsyncClient) -> None:
    create_resp = await admin_client.post(
        "/api/admin/sliders",
        json={"title": "Delete Me", "image": "https://example.com/del.jpg"},
    )
    slider_id = create_resp.json()["id"]

    delete_resp = await admin_client.delete(f"/api/admin/sliders/{slider_id}")
    assert delete_resp.status_code == 204

    list_resp = await api_client.get("/api/sliders")
    ids = [s["id"] for s in list_resp.json()]
    assert slider_id not in ids
