import pytest_asyncio
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
