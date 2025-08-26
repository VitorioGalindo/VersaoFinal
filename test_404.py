import pytest


@pytest.mark.parametrize(
    "method, endpoint, payload",
    [
        ("GET", "/api/screening/", None),
        ("POST", "/api/screening/", {"sector": "Bancos"}),
        ("GET", "/api/screening/sectors", None),
        ("GET", "/api/cvm/documents", None),
        ("GET", "/api/cvm/document-types", None),
        ("GET", "/api/cvm/companies", None),
        ("GET", "/api/ai/ai/status", None),
    ],
)
def test_fixed_endpoints(client, method, endpoint, payload):
    response = client.open(endpoint, method=method, json=payload)
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    if endpoint == "/api/cvm/document-types":
        assert "document_types" in data
