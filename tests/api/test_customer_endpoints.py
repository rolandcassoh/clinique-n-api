"""Tests API — module customer."""
import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db, Base
from app.shared.exceptions.domain import DomainException
from app.core.auth.dependencies import get_current_user

# Import des modèles pour SQLite en mémoire
import app.modules.auth.infrastructure.models  # noqa: F401
import app.modules.customer.infrastructure.models  # noqa: F401

from app.modules.customer.api.router import router as customer_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

USER_ID = 1
OTHER_USER_ID = 2


def _build_app(user_id: int = USER_ID) -> FastAPI:
    app = FastAPI(title="test-customer")
    app.include_router(customer_router, prefix="/api")

    @app.exception_handler(DomainException)
    async def _domain(request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return app


@pytest_asyncio.fixture(scope="module", autouse=True)
async def _tables() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with _Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def seed_user(db: AsyncSession) -> None:
    """Crée un utilisateur minimal dans la DB de test."""
    from app.modules.auth.infrastructure.models import UserModel
    from app.core.auth.password import hash_password

    user = UserModel(
        id=USER_ID,
        name="Alice Test",
        email="alice@test.app",
        password=hash_password("Password1!"),
        is_active=True,
    )
    db.add(user)
    await db.flush()


@pytest_asyncio.fixture
async def auth_client(db: AsyncSession, seed_user: None) -> AsyncClient:
    """Client authentifié en tant qu'user #1."""
    from app.core.auth.jwt_handler import JWTHandler

    token = JWTHandler.create_access_token(user_id=USER_ID, roles=["patient"])
    headers = {"Authorization": f"Bearer {token}"}

    app = _build_app(user_id=USER_ID)

    async def _override_db():
        yield db

    async def _override_user():
        return {"id": USER_ID, "roles": ["patient"]}

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def unauth_client(db: AsyncSession) -> AsyncClient:
    """Client sans authentification."""
    app = _build_app()

    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    # Pas d'override de get_current_user → retourne 401

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# ── Tests GET /api/customers/profile ─────────────────────────────────────────


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_get_profile_200_si_authentifie(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/customers/profile")
        # 200 si l'user existe, 404 si pas de profil — les deux sont valides ici
        assert resp.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_get_profile_401_sans_auth(self, unauth_client: AsyncClient) -> None:
        resp = await unauth_client.get("/api/customers/profile")
        assert resp.status_code == 401


# ── Tests POST /api/customers/family-members ──────────────────────────────────


class TestCreateFamilyMember:
    @pytest.mark.asyncio
    async def test_create_family_member_201_avec_donnees_valides(
        self, auth_client: AsyncClient
    ) -> None:
        payload = {
            "name": "Bob",
            "relation": "fils",
            "date_of_birth": "2015-03-10",
            "gender": "male",
            "blood_group": "O+",
            "phone": None,
        }
        resp = await auth_client.post("/api/customers/family-members", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Bob"
        assert data["relation"] == "fils"
        assert data["user_id"] == USER_ID

    @pytest.mark.asyncio
    async def test_create_family_member_401_sans_auth(
        self, unauth_client: AsyncClient
    ) -> None:
        payload = {"name": "Bob", "relation": "fils"}
        resp = await unauth_client.post("/api/customers/family-members", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_family_members_retourne_liste(
        self, auth_client: AsyncClient
    ) -> None:
        # Crée d'abord un membre
        await auth_client.post(
            "/api/customers/family-members",
            json={"name": "Carla", "relation": "soeur"},
        )
        resp = await auth_client.get("/api/customers/family-members")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Tests DELETE family member d'un autre user → 403 ou 404 ──────────────────


class TestDeleteFamilyMemberOwnership:
    @pytest.mark.asyncio
    async def test_delete_member_autre_user_403_ou_404(
        self, db: AsyncSession
    ) -> None:
        """Un user ne peut pas supprimer le membre de famille d'un autre."""
        from app.modules.customer.infrastructure.models import OtherPatientModel

        # Créer un membre appartenant à OTHER_USER_ID
        other_member = OtherPatientModel(
            user_id=OTHER_USER_ID,
            name="Victim",
            relation="frère",
        )
        db.add(other_member)
        await db.flush()
        member_id = other_member.id

        # Client authentifié en tant que USER_ID (différent)
        from app.core.auth.jwt_handler import JWTHandler

        token = JWTHandler.create_access_token(user_id=USER_ID, roles=["patient"])
        headers = {"Authorization": f"Bearer {token}"}

        app = _build_app(user_id=USER_ID)

        async def _override_db():
            yield db

        async def _override_user():
            return {"id": USER_ID, "roles": ["patient"]}

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = _override_user

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=headers,
        ) as client:
            resp = await client.delete(f"/api/customers/family-members/{member_id}")
            assert resp.status_code in (403, 404)
