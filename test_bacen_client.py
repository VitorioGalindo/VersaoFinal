import pytest
from unittest.mock import patch, Mock
from backend.clients.bacen_client import BacenClient
import requests


def test_get_series_success():
    sample = [{"data": "2024-01-01", "valor": "10.50"}]
    with patch("backend.clients.bacen_client.requests.get") as mock_get:
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = sample
        mock_get.return_value = mock_resp

        client = BacenClient()
        result = client.get_series(11)

        mock_get.assert_called_once_with(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados",
            params={"formato": "json"},
        )
        assert result == sample


def test_get_series_http_error():
    with patch("backend.clients.bacen_client.requests.get") as mock_get:
        mock_resp = Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("boom")
        mock_get.return_value = mock_resp

        client = BacenClient()
        with pytest.raises(requests.HTTPError):
            client.get_series(11)
