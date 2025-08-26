import pytest


@pytest.mark.parametrize("endpoint", [
    "/health",
    "/api/health",
    "/api/companies/",
    "/api/market/overview",
    "/api/tickers/search?q=VALE",
])
def test_get_endpoints(client, endpoint):
    response = client.get(endpoint)
    assert response.status_code == 200
