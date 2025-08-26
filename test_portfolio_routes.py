from backend import db
from backend.models import Company, Ticker, PortfolioPosition, AssetMetrics, Portfolio


def test_upsert_positions_requires_type_for_new_ticker(client):
    payload = [{"symbol": "XXXX", "quantity": 1, "avg_price": 1}]
    resp = client.post("/api/portfolio/1/positions", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Tipo do ticker não fornecido"


def test_upsert_positions_creates_ticker_and_position_when_type_provided(client):
    payload = [{"symbol": "ZZZZ", "quantity": 2, "avg_price": 3, "type": "stock"}]
    resp = client.post("/api/portfolio/1/positions", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["success"] is True
    with client.application.app_context():
        ticker = Ticker.query.filter_by(symbol="ZZZZ").first()
        assert ticker is not None
        assert ticker.type == "stock"
        pos = PortfolioPosition.query.filter_by(portfolio_id=1, symbol="ZZZZ").first()
        assert pos is not None
        assert float(pos.quantity) == 2


def test_upsert_positions_inserts_when_ticker_exists(client):
    with client.application.app_context():
        company = Company(id=1, company_name="Vale")
        ticker = Ticker(symbol="VALE3", company_id=1, type="stock")
        db.session.add_all([company, ticker])
        db.session.commit()

    payload = [{"symbol": "VALE3", "quantity": 10, "avg_price": 5}]
    resp = client.post("/api/portfolio/1/positions", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["success"] is True

    with client.application.app_context():
        pos = PortfolioPosition.query.filter_by(portfolio_id=1, symbol="VALE3").first()
        assert pos is not None
        assert float(pos.quantity) == 10
        assert float(pos.avg_price) == 5





def test_get_daily_contribution_returns_data(client):
    with client.application.app_context():
        company = Company(id=1, company_name="Vale")
        ticker = Ticker(symbol="VALE3", company_id=1, type="stock")
        portfolio = Portfolio(id=1, name="P1")
        pos = PortfolioPosition(portfolio_id=1, symbol="VALE3", quantity=10, avg_price=5)
        metric = AssetMetrics(symbol="VALE3", last_price=10, price_change_percent=2)
        db.session.add_all([company, ticker, portfolio, pos, metric])
        db.session.commit()

    resp = client.get("/api/portfolio/1/daily-contribution")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["contributions"]) == 1
    assert data["contributions"][0]["symbol"] == "VALE3"
    assert data["contributions"][0]["contribution"] == 2


def test_get_suggested_portfolio_returns_data(client):
    with client.application.app_context():
        company = Company(id=1, company_name="Vale")
        ticker = Ticker(symbol="VALE3", company_id=1, type="stock")
        portfolio = Portfolio(id=1, name="P1")
        pos = PortfolioPosition(portfolio_id=1, symbol="VALE3", quantity=10, avg_price=5)
        metric = AssetMetrics(
            symbol="VALE3", last_price=10, price_change_percent=0, sector="Materials"
        )
        db.session.add_all([company, ticker, portfolio, pos, metric])
        db.session.commit()

    resp = client.get("/api/portfolio/1/suggested")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["assets"]) == 1
    asset = data["assets"][0]
    assert asset["ticker"] == "VALE3"
    assert asset["currentPrice"] == 10
    assert round(asset["portfolioWeight"], 2) == 100.0


def test_get_sector_weights_returns_data(client):
    with client.application.app_context():
        company = Company(id=1, company_name="Vale")
        ticker = Ticker(symbol="VALE3", company_id=1, type="stock")
        portfolio = Portfolio(id=1, name="P1")
        pos = PortfolioPosition(portfolio_id=1, symbol="VALE3", quantity=10, avg_price=5)
        metric = AssetMetrics(
            symbol="VALE3", last_price=10, price_change_percent=0, sector="Materials"
        )
        db.session.add_all([company, ticker, portfolio, pos, metric])
        db.session.commit()

    resp = client.get("/api/portfolio/1/sector-weights")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["weights"]) == 1
    weight = data["weights"][0]
    assert weight["sector"] == "Materials"
    assert round(weight["portfolioWeight"], 2) == 100.0


