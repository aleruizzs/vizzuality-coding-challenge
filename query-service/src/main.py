from contextlib import asynccontextmanager
import math
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.database import check_db_connection, engine
from src.schemas import PaginatedEmissionResponse
from src.database import get_db
from src.models import Emission


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_db_connection()
    yield
    await engine.dispose()


app = FastAPI(title="Environmental Data Query API", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "query-service"}


@app.get("/emissions", response_model=PaginatedEmissionResponse)
async def get_emissions(
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
    query = select(Emission)

    # Apply the filtering
    if country and country.strip():
        query = query.where(Emission.country.ilike(f"{country.strip()}%"))
    if sector and sector.strip():
        query = query.where(Emission.sector.ilike(f"{sector.strip()}%"))
    if parent_sector and parent_sector.strip():
        query = query.where(Emission.parent_sector.ilike(f"{parent_sector.strip()}%"))
    if year is not None:
        query = query.where(Emission.year == year)
    if value is not None:
        query = query.where(Emission.value == value)

    # Count the number of results obtained from the query
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Dictionary with the safe pagination parameters
    allowed_sort_fields: dict[str, Any] = {
        "id": Emission.id,
        "country": Emission.country,
        "sector": Emission.sector,
        "parent_sector": Emission.parent_sector,
        "year": Emission.year,
        "value": Emission.value,
    }

    # Create the sorting clauses
    sort_clauses: list[Any] = []
    requested_fields = [f.strip() for f in sort_by.split(",") if f.strip()]
    id_requested = False

    # Check if the requested fields are valid and add them to the sorting clauses
    for field in requested_fields:
        is_desc = field.startswith("-")
        clean_field_name = field.lstrip("-+")

        if clean_field_name not in allowed_sort_fields:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid sort field '{clean_field_name}'. "
                    f"Allowed fields: {list(allowed_sort_fields.keys())}"
                ),
            )
        if clean_field_name == "id":
            id_requested = True

        col = allowed_sort_fields[clean_field_name]
        sort_clauses.append(desc(col) if is_desc else asc(col))

    # Apply the sorting
    if not id_requested:
        sort_clauses.append(asc(Emission.id))
    query = query.order_by(*sort_clauses)

    # Calculate the offset and limit
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute the query and return the results
    result = await db.execute(query)
    emissions = list(result.scalars().all())

    total_pages = math.ceil(total / limit) if total > 0 else 0

    return PaginatedEmissionResponse(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        data=emissions,
    )
