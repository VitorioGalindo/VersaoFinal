import requests
from datetime import datetime


class BacenClient:
    """Simple client for Banco Central do Brasil services."""

    SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
    PTAX_URL = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
    )

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def get_series(self, series_id: int, start: datetime, end: datetime):
        """Return SGS time series values between dates."""
        params = {
            "formato": "json",
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
        }
        url = self.SGS_URL.format(series_id=series_id)
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        result = []
        for item in data:
            result.append(
                {
                    "date": datetime.strptime(item["data"], "%d/%m/%Y").date(),
                    "value": float(item["valor"].replace(",", ".")),
                }
            )
        return result

    def get_ptax(self, date_from: datetime, date_to: datetime):
        """Return PTAX USD/BRL quotations between dates."""
        params = {
            "@dataInicial": date_from.strftime("%m-%d-%Y"),
            "@dataFinalCotacao": date_to.strftime("%m-%d-%Y"),
            "$format": "json",
        }
        resp = self.session.get(self.PTAX_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("value", [])
        result = []
        for item in data:
            result.append(
                {
                    "date": datetime.strptime(
                        item["dataHoraCotacao"], "%Y-%m-%d %H:%M:%S.%f"
                    ).date(),
                    "buy": float(item["cotacaoCompra"]),
                    "sell": float(item["cotacaoVenda"]),
                }
            )
        return result
