from typing import Optional

from sqlalchemy import Double, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Emission(Base):
    __tablename__ = "emissions"
    __table_args__ = (
        UniqueConstraint(
            "country",
            "sector",
            "parent_sector",
            "year",
            name="unique_country_sector_year",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    parent_sector: Mapped[Optional[str]] = mapped_column(
        String(255), index=True, nullable=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[Optional[float]] = mapped_column(Double, nullable=False)
