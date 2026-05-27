import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(_TEST_DATABASE_URL, echo=False)
_TestSessionLocal = async_sessionmaker(
    bind=_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@clinique.app",
            "password": "SecureP@ss123",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict[str, str]:
    from app.core.auth.jwt_handler import JWTHandler

    user_id = registered_user["id"]
    token = JWTHandler.create_access_token(user_id=user_id, roles=["patient"])
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers() -> dict[str, str]:
    from app.core.auth.jwt_handler import JWTHandler

    token = JWTHandler.create_access_token(user_id=999, roles=["admin", "super-admin"])
    return {"Authorization": f"Bearer {token}"}
