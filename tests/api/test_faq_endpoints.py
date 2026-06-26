"""Tests d'intégration des endpoints FAQ."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.faq.infrastructure.modeles import FAQModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _insert_faq(
    db: AsyncSession,
    question: str = "Quels sont vos horaires ?",
    answer: str = "Du lundi au vendredi 8h-18h.",
    category: str | None = "Général",
    is_active: bool = True,
    sort_order: int = 0,
) -> FAQModel:
    faq = FAQModel(
        question=question,
        answer=answer,
        category=category,
        is_active=is_active,
        sort_order=sort_order,
    )
    db.add(faq)
    await db.flush()
    await db.refresh(faq)
    return faq


# ---------------------------------------------------------------------------
# Tests GET /api/faq (public)
# ---------------------------------------------------------------------------


class TestListFAQsPublic:
    async def test_returns_200(self, api_client: AsyncClient, db: AsyncSession) -> None:
        await _insert_faq(db)
        resp = await api_client.get("/api/faq")
        assert resp.status_code == 200

    async def test_returns_only_active_faqs(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_faq(db, question="FAQ active", is_active=True)
        await _insert_faq(db, question="FAQ inactive", is_active=False)

        resp = await api_client.get("/api/faq")
        body = resp.json()
        questions = [f["question"] for f in body["data"]]
        assert "FAQ active" in questions
        assert "FAQ inactive" not in questions

    async def test_inactive_faq_never_returned(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        """La FAQ inactive ne doit JAMAIS apparaître dans la liste publique."""
        await _insert_faq(db, question="Invisible FAQ", is_active=False)
        resp = await api_client.get("/api/faq")
        body = resp.json()
        for faq in body["data"]:
            assert faq["is_active"] is True

    async def test_filter_by_category(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_faq(db, question="FAQ cat A", category="Cat-A")
        await _insert_faq(db, question="FAQ cat B", category="Cat-B")

        resp = await api_client.get("/api/faq", params={"category": "Cat-A"})
        body = resp.json()
        questions = [f["question"] for f in body["data"]]
        assert "FAQ cat A" in questions
        assert "FAQ cat B" not in questions

    async def test_pagination_structure(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        resp = await api_client.get("/api/faq")
        body = resp.json()
        for key in ("data", "total", "page", "per_page", "total_pages"):
            assert key in body

    async def test_soft_deleted_faq_excluded(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        from datetime import datetime
        faq = await _insert_faq(db, question="FAQ supprimée")
        faq.deleted_at = datetime.utcnow()
        await db.flush()

        resp = await api_client.get("/api/faq")
        body = resp.json()
        questions = [f["question"] for f in body["data"]]
        assert "FAQ supprimée" not in questions


# ---------------------------------------------------------------------------
# Tests GET /api/faq/{id} (public)
# ---------------------------------------------------------------------------


class TestGetFAQ:
    async def test_returns_200_for_existing_faq(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        faq = await _insert_faq(db, question="Ma question ?")
        resp = await api_client.get(f"/api/faq/{faq.id}")
        assert resp.status_code == 200
        assert resp.json()["question"] == "Ma question ?"

    async def test_returns_404_for_unknown_id(
        self, api_client: AsyncClient
    ) -> None:
        resp = await api_client.get("/api/faq/999999")
        assert resp.status_code == 404

    async def test_response_has_all_fields(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        faq = await _insert_faq(db)
        resp = await api_client.get(f"/api/faq/{faq.id}")
        body = resp.json()
        for field in ("id", "question", "answer", "category", "is_active", "sort_order"):
            assert field in body


# ---------------------------------------------------------------------------
# Tests POST /api/admin/faq (admin)
# ---------------------------------------------------------------------------


class TestCreateFAQ:
    async def test_admin_can_create_faq(
        self, admin_client: AsyncClient
    ) -> None:
        payload = {
            "question": "Nouvelle FAQ admin ?",
            "answer": "Réponse de l'admin.",
            "category": "Admin",
            "is_active": True,
            "sort_order": 1,
        }
        resp = await admin_client.post("/api/admin/faq", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["question"] == "Nouvelle FAQ admin ?"
        assert body["is_active"] is True

    async def test_unauthenticated_cannot_create(
        self, api_client: AsyncClient
    ) -> None:
        payload = {
            "question": "FAQ non auth ?",
            "answer": "Réponse.",
        }
        resp = await api_client.post("/api/admin/faq", json=payload)
        assert resp.status_code in (401, 403)

    async def test_create_faq_defaults(
        self, admin_client: AsyncClient
    ) -> None:
        payload = {
            "question": "FAQ avec defaults ?",
            "answer": "Réponse par défaut.",
        }
        resp = await admin_client.post("/api/admin/faq", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["is_active"] is True
        assert body["sort_order"] == 0


# ---------------------------------------------------------------------------
# Tests PUT /api/admin/faq/{id} (admin)
# ---------------------------------------------------------------------------


class TestUpdateFAQ:
    async def test_admin_can_update_faq(
        self, admin_client: AsyncClient, db: AsyncSession
    ) -> None:
        faq = await _insert_faq(db, question="Ancienne question ?")
        payload = {"question": "Nouvelle question ?"}
        resp = await admin_client.put(f"/api/admin/faq/{faq.id}", json=payload)
        assert resp.status_code == 200
        assert resp.json()["question"] == "Nouvelle question ?"

    async def test_update_non_existent_returns_404(
        self, admin_client: AsyncClient
    ) -> None:
        resp = await admin_client.put("/api/admin/faq/999999", json={"question": "Test ?"})
        assert resp.status_code == 404

    async def test_unauthenticated_cannot_update(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        faq = await _insert_faq(db)
        resp = await api_client.put(f"/api/admin/faq/{faq.id}", json={"question": "Hacked ?"})
        assert resp.status_code in (401, 403)

    async def test_can_deactivate_faq(
        self, admin_client: AsyncClient, db: AsyncSession
    ) -> None:
        faq = await _insert_faq(db, is_active=True)
        resp = await admin_client.put(f"/api/admin/faq/{faq.id}", json={"is_active": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


# ---------------------------------------------------------------------------
# Tests DELETE /api/admin/faq/{id} (admin)
# ---------------------------------------------------------------------------


class TestDeleteFAQ:
    async def test_admin_can_delete_faq(
        self, admin_client: AsyncClient, db: AsyncSession, api_client: AsyncClient
    ) -> None:
        faq = await _insert_faq(db, question="FAQ à supprimer ?")
        resp = await admin_client.delete(f"/api/admin/faq/{faq.id}")
        assert resp.status_code == 204

        # Vérification : la FAQ n'est plus accessible publiquement
        check = await api_client.get(f"/api/faq/{faq.id}")
        assert check.status_code == 404

    async def test_delete_non_existent_returns_404(
        self, admin_client: AsyncClient
    ) -> None:
        resp = await admin_client.delete("/api/admin/faq/999999")
        assert resp.status_code == 404

    async def test_unauthenticated_cannot_delete(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        faq = await _insert_faq(db)
        resp = await api_client.delete(f"/api/admin/faq/{faq.id}")
        assert resp.status_code in (401, 403)

    async def test_soft_delete_does_not_destroy_record(
        self, admin_client: AsyncClient, db: AsyncSession
    ) -> None:
        """Après suppression douce, deleted_at doit être non-null en BDD."""
        faq = await _insert_faq(db, question="FAQ soft delete ?")
        await admin_client.delete(f"/api/admin/faq/{faq.id}")

        await db.refresh(faq)
        assert faq.deleted_at is not None
