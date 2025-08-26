import pandas as pd
from datetime import datetime

def test_get_ibov_history(monkeypatch, client):
    from backend.routes import market_routes

    def fake_download(symbol, start=None, end=None, progress=None):
        idx = pd.date_range(datetime(2024, 1, 1), periods=3, freq='D')
        return pd.DataFrame({'Adj Close': [100, 101, 102]}, index=idx)

    monkeypatch.setattr(market_routes, 'yf', type('obj', (), {'download': fake_download}))

    resp = client.get('/api/market/ibov-history')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert len(data['history']) == 3
