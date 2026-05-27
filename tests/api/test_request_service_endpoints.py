"""Tests d'intégration des endpoints RequestService."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import des modèles pour créer les tables
import app.modules.request_service.infrastructure.models  # noqa: F401

from app.modules.request_service.infrastructure.models import RequestServiceModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patient_headers(user_id: int = 1) -> dict[str, str]:
    from app.core.auth.jwt_handler import JWTHandler
    token = JWTHandler.create_access_token(user_id=user_id, roles=["patient"])
    return {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    from app.core.auth.jwt_handler import JWTHandler
    token = JWTHandler.create_access_token(user_id=999, roles=["admin", "super-admin"])
    return {"Authorization": f"Bearer {token}"}


async def _insert_request(
    db: AsyncSession,
    user_id: int = 1,
    title: str = "Besoin d'une infirmière",
    description: str = "Je cherche une infirmière pour soins quotidiens.",
    status: str = "pending",
) -> RequestServiceModel:
    m = RequestServiceModel(
        user_id=user_id,
        title=title,
        description=description,
        status=status,
    )
    db.add(m)
    await db.flush()
    await db.refresh(m)
    return m


# ---------------------------------------------------------------------------
# Tests POST /api/request-services
# ---------------------------------------------------------------------------


class TestCreateRequestService:
    async def test_create_requires_auth(self, api_client: AsyncClient) -> None:
        resp = await api_client.post(
            "/api/request-services",
            json={"title": "Test", "description": "Description longue suffisante."},
        )
        assert resp.status_code == 401

    async def test_create_returns_201(self, api_client: AsyncClient) -> None:
        headers = _patient_headers(user_id=10)
        resp = await api_client.post(
            "/api/request-services",
            json={
                "title": "Demande de soin",
                "description": "J'ai besoin d'une infirmière pour des soins quotidiens.",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Demande de soin"
        assert body["status"] == "pending"
        assert body["user_id"] == 10

    async def test_create_sets_status_pending(self, api_client: AsyncClient) -> None:
        headers = _patient_headers(user_id=11)
        resp = await api_client.post(
            "/api/request-services",
            json={
                "title": "Ma demande",
                "description": "Description de ma demande médicale à domicile.",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    async def test_create_with_all_fields(self, api_client: AsyncClient) -> None:
        headers = _patient_headers(user_id=12)
        resp = await api_client.post(
            "/api/request-services",
            json={
                "title": "Demande complète",
                "description": "Demande avec tous les champs renseignés.",
                "location": "123 Rue de la Paix, Paris",
                "latitude": "48.8698",
                "longitude": "2.3078",
                "budget_min": "50.00",
                "budget_max": "200.00",
                "preferred_date": "2026-06-01",
                "preferred_time": "09:00:00",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["location"] == "123 Rue de la Paix, Paris"
        assert body["budget_min"] == "50.00"


# ---------------------------------------------------------------------------
# Tests GET /api/request-services (mes demandes seulement)
# ---------------------------------------------------------------------------


class TestListMyRequestServices:
    async def test_requires_auth(self, api_client: AsyncClient) -> None:
        resp = await api_client.get("/api/request-services")
        assert resp.status_code == 401

    async def test_returns_only_own_requests(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        # User 20 a 2 demandes
        await _insert_request(db, user_id=20, title="Demande user 20 - A")
        await _insert_request(db, user_id=20, title="Demande user 20 - B")
        # User 21 a 1 demande
        await _insert_request(db, user_id=21, title="Demande user 21")

        headers = _patient_headers(user_id=20)
        resp = await api_client.get("/api/request-services", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        # User 20 ne voit QUE ses 2 demandes
        assert all(r["user_id"] == 20 for r in body["data"])
        titles = [r["title"] for r in body["data"]]
        assert "Demande user 20 - A" in titles
        assert "Demande user 20 - B" in titles
        assert "Demande user 21" not in titles

    async def test_pagination_structure(self, api_client: AsyncClient) -> None:
        headers = _patient_headers(user_id=30)
        resp = await api_client.get("/api/request-services", headers=headers)
        assert resp.status_code == 200
        for key in ("data", "total", "page", "per_page", "total_pages"):
            assert key in resp.json()


# ---------------------------------------------------------------------------
# Tests GET /api/request-services/{id}
# ---------------------------------------------------------------------------


class TestGetMyRequestService:
    async def test_get_own_request_200(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=40)
        headers = _patient_headers(user_id=40)
        resp = await api_client.get(f"/api/request-services/{req.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == req.id

    async def test_cannot_get_other_user_request(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=41)
        headers = _patient_headers(user_id=42)  # Autre utilisateur
        resp = await api_client.get(f"/api/request-services/{req.id}", headers=headers)
        assert resp.status_code == 403

    async def test_get_nonexistent_request_404(self, api_client: AsyncClient) -> None:
        headers = _patient_headers(user_id=50)
        resp = await api_client.get("/api/request-services/999999", headers=headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests DELETE /api/request-services/{id} (annulation)
# ---------------------------------------------------------------------------


class TestCancelRequestService:
    async def test_cancel_pending_request_204(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=60, status="pending")
        headers = _patient_headers(user_id=60)
        resp = await api_client.delete(f"/api/request-services/{req.id}", headers=headers)
        assert resp.status_code == 204

    async def test_cancel_matched_request_409(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Un request avec status='matched' ne peut pas être annulé → 409."""
        req = await _insert_request(db, user_id=61, status="matched")
        headers = _patient_headers(user_id=61)
        resp = await api_client.delete(f"/api/request-services/{req.id}", headers=headers)
        assert resp.status_code == 409

    async def test_cancel_in_review_request_409(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=62, status="in_review")
        headers = _patient_headers(user_id=62)
        resp = await api_client.delete(f"/api/request-services/{req.id}", headers=headers)
        assert resp.status_code == 409

    async def test_cannot_cancel_other_user_request(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=63, status="pending")
        headers = _patient_headers(user_id=64)  # Autre user
        resp = await api_client.delete(f"/api/request-services/{req.id}", headers=headers)
        assert resp.status_code == 403

    async def test_cancel_requires_auth(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=65)
        resp = await api_client.delete(f"/api/request-services/{req.id}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests Admin — /api/admin/request-services
# ---------------------------------------------------------------------------


class TestAdminRequestServices:
    async def test_admin_list_all_requests(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_request(db, user_id=70, title="Admin voit tout A")
        await _insert_request(db, user_id=71, title="Admin voit tout B")
        headers = _admin_headers()
        resp = await api_client.get("/api/admin/request-services", headers=headers)
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.json()["data"]]
        assert "Admin voit tout A" in titles
        assert "Admin voit tout B" in titles

    async def test_admin_filter_by_status(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_request(db, user_id=72, status="pending")
        await _insert_request(db, user_id=73, status="matched")
        headers = _admin_headers()
        resp = await api_client.get(
            "/api/admin/request-services", params={"status": "pending"}, headers=headers
        )
        assert resp.status_code == 200
        assert all(r["status"] == "pending" for r in resp.json()["data"])

    async def test_admin_update_status(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        req = await _insert_request(db, user_id=74, status="pending")
        headers = _admin_headers()
        resp = await api_client.patch(
            f"/api/admin/request-services/{req.id}/status",
            json={"status": "in_review"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_review"

    async def test_non_admin_cannot_list_all(
        self, api_client: AsyncClient
    ) -> None:
        headers = _patient_headers(user_id=75)
        resp = await api_client.get("/api/admin/request-services", headers=headers)
        assert resp.status_code in (401, 403)
