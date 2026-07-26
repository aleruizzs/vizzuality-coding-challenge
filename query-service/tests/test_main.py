from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas import PaginatedEmissionResponse


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "service" in response.json()

@pytest.mark.asyncio
async def test_status(client):
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    client.mock_db.execute.return_value = mock_result

    response = await client.get("/status")

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "ok"
    assert result["total_records"] == 0
    assert "schema_version" in result

@pytest.mark.asyncio
async def test_emissions(client):
    fake_response = PaginatedEmissionResponse(
        total=1,
        page=1,
        limit=20,
        total_pages=1,
        data=[],
    )

    with patch("src.main.get_emissions", new_callable=AsyncMock) as mock_get_emissions:
        mock_get_emissions.return_value = fake_response

        response = await client.get("/emissions?country=Spain&page=1")

        assert response.status_code == 200
        assert response.json()["total"] == 1
        
        mock_get_emissions.assert_called_once_with(
            country="Spain",
            sector=None,
            parent_sector=None,
            year=None,
            value=None,
            page=1,
            limit=20,
            sort_by="id",
            db=client.mock_db,
        )


@pytest.mark.asyncio
async def test_emissions_fastapi_validations(client):
    res_page = await client.get("/emissions?page=0")
    assert res_page.status_code == 422

    res_limit = await client.get("/emissions?limit=101")
    assert res_limit.status_code == 422

@pytest.mark.asyncio
async def test_emissions_wrong_sort_field(client):
    res = await client.get("/emissions?sort_by=wrong_field")
    assert res.status_code == 400
