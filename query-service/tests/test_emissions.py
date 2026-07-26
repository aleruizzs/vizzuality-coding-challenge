import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from src.emissions import get_emissions
from src.models import Emission

@pytest.mark.asyncio
async def test_invalid_sort_field_raises_400():
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_emissions(mock_db, sort_by="columna_inexistente")

    assert exc_info.value.status_code == 400
    assert "Invalid sort field 'columna_inexistente'" in exc_info.value.detail

    assert mock_db.execute.call_count == 0

@pytest.mark.asyncio
async def test_parameter_whitespaces_are_stripped(test_db_session):
    test_db_session.add(Emission(country="Spain", sector="Energy", parent_sector="Energy", year=2026, value=100.0))
    await test_db_session.commit()

    result = await get_emissions(
        db=test_db_session,
        country=" Spain ",
        sector=" Energy ",
        parent_sector=" Energy ",
    )

    assert result.total == 1
    assert result.data[0].country == "Spain"
    assert result.data[0].sector == "Energy"
    assert result.data[0].parent_sector == "Energy"

@pytest.mark.asyncio
async def test_parameter_ilike(test_db_session):
    test_db_session.add(Emission(country="Spain", sector="Energy", parent_sector="Energy", year=2026, value=100.0))
    await test_db_session.commit()

    result = await get_emissions(
        db=test_db_session,
        country="sp",
        sector="en",
        parent_sector="en",
    )

    assert result.total == 1
    assert result.data[0].country == "Spain"
    assert result.data[0].sector == "Energy"
    assert result.data[0].parent_sector == "Energy"

@pytest.mark.asyncio
async def test_total_count(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2024, value=100.0),
        Emission(country="Spain", sector="Agriculture", year=2025, value=50.0),
        Emission(country="Spain", sector="Energy", year=2026, value=200.0),
    ])
    await test_db_session.commit()

    result_all = await get_emissions(db=test_db_session)
    assert result_all.total == 3

    result_spain = await get_emissions(db=test_db_session, country="Spain")
    assert result_spain.total == 3

    result_none = await get_emissions(db=test_db_session, country="Germany")
    assert result_none.total == 0

@pytest.mark.asyncio
async def test_multiple_filters_combined(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2020, value=100.0),
        Emission(country="Spain", sector="Agriculture", year=2020, value=50.0),
        Emission(country="Spain", sector="Energy", year=2021, value=100.0),
    ])
    await test_db_session.commit()

    result = await get_emissions(
        db=test_db_session, country="Spain", sector="Energy", year=2020
    )
    assert result.total == 1
    assert result.data[0].sector == "Energy"
    assert result.data[0].year == 2020

@pytest.mark.asyncio
async def test_filter_with_zero_value(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2020, value=0.0),
        Emission(country="Spain", sector="Energy", year=2020, value=10.0),
    ])
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session, value=0.0)
    assert result.total == 1
    assert result.data[0].value == 0.0

@pytest.mark.asyncio
async def test_whitespace_only_filters_ignored(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2020, value=10.0),
        Emission(country="France", sector="Energy", year=2020, value=200.0),
    ])
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session, country="   ", sector="   ")
    assert result.total == 2

@pytest.mark.asyncio
async def test_default_sort_by_id_asc(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2024, value=100.0),
        Emission(country="Spain", sector="Energy", year=2025, value=200.0),
        Emission(country="Spain", sector="Energy", year=2026, value=150.0),
    ])
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session)
    ids = [item.id for item in result.data]

    assert ids == [1, 2, 3]

@pytest.mark.asyncio
async def test_sort_id_desc(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2024, value=100.0),
        Emission(country="Spain", sector="Energy", year=2025, value=200.0),
        Emission(country="Spain", sector="Energy", year=2026, value=150.0),
    ])
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session, sort_by="-id")
    ids = [item.id for item in result.data]

    assert ids == [3, 2, 1]

@pytest.mark.asyncio
async def test_single_sort_field(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2024, value=10.0),
        Emission(country="Spain", sector="Energy", year=2025, value=50.0),
        Emission(country="Spain", sector="Energy", year=2026, value=30.0),
    ])
    await test_db_session.commit()

    result_asc = await get_emissions(db=test_db_session, sort_by="year")
    years_asc = [item.year for item in result_asc.data]
    assert years_asc == [2024, 2025, 2026]

    result_desc = await get_emissions(db=test_db_session, sort_by="-year")
    years_desc = [item.year for item in result_desc.data]
    assert years_desc == [2026, 2025, 2024]


@pytest.mark.asyncio
async def test_multiple_sort_fields(test_db_session):
    test_db_session.add_all([
        Emission(country="Spain", sector="Energy", year=2024, value=10.0),
        Emission(country="Spain", sector="Energy", year=2025, value=30.0),
        Emission(country="France", sector="Energy", year=2023, value=20.0),
    ])
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session, sort_by="country,-year")
    
    ordered_pairs = [(item.country, item.year) for item in result.data]
    assert ordered_pairs == [
        ("France", 2023),
        ("Spain", 2025),
        ("Spain", 2024),
    ]

@pytest.mark.asyncio
async def test_pagination_basic_limit_and_total_pages(test_db_session):
    emissions = [
        Emission(country="Spain", sector="Energy", year=2000 + i, value=float(i))
        for i in range(25)
    ]
    test_db_session.add_all(emissions)
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session, page=1, limit=10)

    assert result.total == 25
    assert result.page == 1
    assert result.limit == 10
    assert result.total_pages == 3
    assert len(result.data) == 10

@pytest.mark.asyncio
async def test_pagination_offset_navigation(test_db_session):
    emissions = [
        Emission(country="Spain", sector="Energy", year=2000 + i, value=10.0)
        for i in range(25)
    ]
    test_db_session.add_all(emissions)
    await test_db_session.commit()

    res_p1 = await get_emissions(db=test_db_session, page=1, limit=10, sort_by="year")
    assert [item.year for item in res_p1.data] == list(range(2000, 2010))

    res_p2 = await get_emissions(db=test_db_session, page=2, limit=10, sort_by="year")
    assert [item.year for item in res_p2.data] == list(range(2010, 2020))

    res_p3 = await get_emissions(db=test_db_session, page=3, limit=10, sort_by="year")
    assert [item.year for item in res_p3.data] == list(range(2020, 2025))
    assert len(res_p3.data) == 5

@pytest.mark.asyncio
async def test_get_emissions_pagination_out_of_bounds_page(test_db_session):
    emissions = [
        Emission(country="Spain", sector="Energy", year=2020, value=10.0)
        for _ in range(5)
    ]
    test_db_session.add_all(emissions)
    await test_db_session.commit()

    result = await get_emissions(db=test_db_session, page=99, limit=10)

    assert result.total == 5
    assert result.total_pages == 1
    assert result.page == 99
    assert result.data == []
