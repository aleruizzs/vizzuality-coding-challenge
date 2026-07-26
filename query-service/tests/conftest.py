from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import get_db
from src.main import app
from src.models import Base

# Engine and session for the test database
engine = create_async_engine("sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, 
    expire_on_commit=False, autoflush=False)


# Fixture to create the tables and delete them after each test
@pytest_asyncio.fixture()
async def test_db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Fixture to mock the db dependency
@pytest_asyncio.fixture
async def client():
    mock_session = AsyncMock()

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("src.main.check_db_connection", new_callable=AsyncMock):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            ac.mock_db = mock_session
            yield ac

    app.dependency_overrides.clear()
