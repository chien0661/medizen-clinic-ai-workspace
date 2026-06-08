"""Integration tests: health endpoint."""


async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_returns_ok_status(client):
    response = await client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "clinic-cms-api"


async def test_root_returns_200(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health" in data
