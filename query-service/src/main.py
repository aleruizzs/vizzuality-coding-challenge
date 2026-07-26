from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import check_db_connection, engine, get_db
from src.emissions import get_emissions
from src.models import Emission
from src.schemas import PaginatedEmissionResponse, StatusResponse


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
    country: Annotated[Optional[str], Query()] = None,
    sector: Annotated[Optional[str], Query()] = None,
    parent_sector: Annotated[Optional[str], Query()] = None,
    year: Annotated[Optional[int], Query()] = None,
    value: Annotated[Optional[float], Query()] = None,
    # Pagination parameters
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    # Sorting parameters
    sort_by: Annotated[
        str,
        Query(
            description="Comma-separated fields to sort by. "
            "Prefix with '-' for DESC (e.g. 'country,-year')"
        ),
    ] = "id",
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_emissions(
            country=country,
            sector=sector,
            parent_sector=parent_sector,
            year=year,
            value=value,
            page=page,
            limit=limit,
            sort_by=sort_by,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
