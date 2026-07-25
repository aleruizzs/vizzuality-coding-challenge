from typing import Sequence, Optional
from pydantic import BaseModel, ConfigDict


# Schema for the response of a single emission record
class EmissionResponse(BaseModel):
    id: int
    country: str
    sector: str
    parent_sector: Optional[str] = None
    year: int
    value: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# Schema for the response of a paginated list of emission records
class PaginatedEmissionResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    data: Sequence[EmissionResponse]
