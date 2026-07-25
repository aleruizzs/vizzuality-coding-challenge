from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import func, select
from fastapi import Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.database import check_db_connection, engine
from src.schemas import PaginatedEmissionResponse, StatusResponse
from src.database import get_db
from src.models import Emission
from src.config import settings
from src.emissions import get_emissions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_db_connection()
    yield
    await engine.dispose()


app = FastAPI(title="Environmental Data Query API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/emissions", response_model=PaginatedEmissionResponse)
async def emissions(    
    # Optional parameters for filtering
    country: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    parent_sector: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    value: Optional[float] = Query(None),
    # Pagination parameters
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    # Sorting parameters
    sort_by: str = Query(
        "id",
        description="Comma-separated fields to sort by. "
        "Prefix with '-' for DESC (e.g. 'country,-year')",
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_emissions(country, sector, parent_sector, year, value, page, limit, sort_by, db)


@app.get("/status", response_model=StatusResponse)
async def get_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(Emission))
    total_records = result.scalar() or 0

    return StatusResponse(
        service=settings.SERVICE_NAME,
        status="ok",
        total_records=total_records,
        schema_version=settings.SCHEMA_VERSION,
    )
