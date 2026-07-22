from sqlalchemy import Column, Float, Integer, String
from src.database import Base


class Emission(Base):
    __tablename__ = "emissions"

    id = Column(Integer, primary_key=True)
    country = Column(String, index=True, nullable=False)
    sector = Column(String, index=True, nullable=False)
    parent_sector = Column(String, index=True, nullable=True)
    year = Column(Integer, nullable=False)
    value = Column(Float, nullable=True)
