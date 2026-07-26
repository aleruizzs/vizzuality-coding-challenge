import math
from typing import Any, Optional

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Emission
from src.schemas import PaginatedEmissionResponse

# Dictionary with the safe pagination parameters
ALLOWED_SORT_FIELDS: dict[str, Any] = {
    "id": Emission.id,
    "country": Emission.country,
    "sector": Emission.sector,
    "parent_sector": Emission.parent_sector,
    "year": Emission.year,
    "value": Emission.value,
}


async def get_emissions(
    db: AsyncSession,
    country: Optional[str] = None,
    sector: Optional[str] = None,
    parent_sector: Optional[str] = None,
    year: Optional[int] = None,
    value: Optional[float] = None,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "id",
) -> PaginatedEmissionResponse:
    # Create the query
    query = select(Emission)

    # Apply the filtering
    if country and country.strip():
        query = query.where(Emission.country.istartswith(country.strip(), autoescape=True))

    if sector and  sector.strip():
        query = query.where(Emission.sector.istartswith(sector.strip(), autoescape=True))

    if parent_sector and parent_sector.strip():
        query = query.where(Emission.parent_sector.istartswith(parent_sector.strip(), autoescape=True))

    if year is not None:
        query = query.where(Emission.year == year)

    if value is not None:
        query = query.where(Emission.value == value)

    # Create the sorting clauses
    sort_clauses: list[Any] = []
    requested_fields = [f.strip() for f in sort_by.split(",") if f.strip()]
    id_requested = False

    # Check if the requested fields are valid and add them to the sorting clauses
    for field in requested_fields:
        is_desc = field.startswith("-")
        clean_field_name = field.removeprefix("+").removeprefix("-")

        if clean_field_name not in ALLOWED_SORT_FIELDS:
            raise ValueError(
                f"Invalid sort field '{clean_field_name}'. "
                f"Allowed fields: {list(ALLOWED_SORT_FIELDS.keys())}"
            )
        if clean_field_name == "id":
            id_requested = True

        col = ALLOWED_SORT_FIELDS[clean_field_name]
        sort_clauses.append(desc(col) if is_desc else asc(col))

    # Count the number of results obtained from the original query
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

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
