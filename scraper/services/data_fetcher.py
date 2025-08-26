from datetime import datetime, timedelta
from .bcb_client import BacenClient
from ..database import get_db_session
from ..models import MacroIndicator, MacroIndicatorHistory


SGS_SERIES = {
    "selic": {"id": 1178, "unit": "% a.a."},
    "ipca": {"id": 433, "unit": "%"},
}


def fetch_macro_indicators(days: int = 30):
    """Fetch macroeconomic indicators from Bacen and upsert into DB."""
    client = BacenClient()
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    with get_db_session() as session:
        # Fetch SGS series
        for name, cfg in SGS_SERIES.items():
            series = client.get_series(cfg["id"], start_date, end_date)
            if not series:
                continue
            indicator = (
                session.query(MacroIndicator).filter_by(name=name).first()
            )
            if not indicator:
                indicator = MacroIndicator(name=name, unit=cfg.get("unit"))
                session.add(indicator)
                session.flush()
            for item in series:
                history = (
                    session.query(MacroIndicatorHistory)
                    .filter_by(indicator_id=indicator.id, reference_date=item["date"])
                    .first()
                )
                if history:
                    history.value = item["value"]
                else:
                    session.add(
                        MacroIndicatorHistory(
                            indicator_id=indicator.id,
                            reference_date=item["date"],
                            value=item["value"],
                        )
                    )
            indicator.latest_value = series[-1]["value"]
            indicator.updated_at = datetime.utcnow()

        # Fetch PTAX USD/BRL
        ptax_data = client.get_ptax(start_date, end_date)
        if ptax_data:
            name = "ptax_usd_brl"
            indicator = session.query(MacroIndicator).filter_by(name=name).first()
            if not indicator:
                indicator = MacroIndicator(name=name, unit="BRL")
                session.add(indicator)
                session.flush()
            for item in ptax_data:
                history = (
                    session.query(MacroIndicatorHistory)
                    .filter_by(indicator_id=indicator.id, reference_date=item["date"])
                    .first()
                )
                value = item["sell"]
                if history:
                    history.value = value
                else:
                    session.add(
                        MacroIndicatorHistory(
                            indicator_id=indicator.id,
                            reference_date=item["date"],
                            value=value,
                        )
                    )
            indicator.latest_value = ptax_data[-1]["sell"]
            indicator.updated_at = datetime.utcnow()
