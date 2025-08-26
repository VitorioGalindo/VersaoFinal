import requests

class BacenClient:
    """Simple client for Banco Central do Brasil SGS API."""

    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}/dados"

    def get_series(self, series: int | str, params: dict | None = None):
        """Fetch a time series from Bacen's SGS API.

        Parameters
        ----------
        series: int | str
            Identifier of the time series.
        params: dict | None
            Additional query parameters. Defaults to requesting JSON format.
        """
        query = {"formato": "json"}
        if params:
            query.update(params)
        url = self.BASE_URL.format(series=series)
        response = requests.get(url, params=query)
        response.raise_for_status()
        return response.json()
