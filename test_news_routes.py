import pytest
from datetime import datetime
from backend import db
from backend.models import MarketArticle


@pytest.fixture
def news_with_dates(client):
    """Insere duas notícias com horários de coleta distintos."""
    with client.application.app_context():
        older = MarketArticle(
            titulo='Old',
            portal='PortalA',
            data_coleta=datetime(2024, 1, 1, 9, 0, 0),
            tickers_relacionados=[],
        )
        newer = MarketArticle(
            titulo='New',
            portal='PortalB',
            data_coleta=datetime(2024, 1, 1, 15, 30, 0),
            tickers_relacionados=[],
        )
        db.session.add_all([older, newer])
        db.session.commit()
        return older.data_coleta, newer.data_coleta

def test_get_news_by_ticker(client):
    with client.application.app_context():
        db.session.add(MarketArticle(titulo='Match', tickers_relacionados=['PETR4']))
        db.session.add(MarketArticle(titulo='Other', tickers_relacionados=['VALE3']))
        db.session.commit()

    resp = client.get('/api/news/company/PETR4')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]['titulo'] == 'Match'


def test_analyze_news(client):
    with client.application.app_context():
        article = MarketArticle(titulo='Test', resumo='Boa notícia', tickers_relacionados=[])
        db.session.add(article)
        db.session.commit()
        art_id = article.id

    resp = client.post(f'/api/news/{art_id}/analyze')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'sentiment' in data
    assert 'summary' in data


def test_get_latest_news_portal_filter(client, news_with_dates):
    resp = client.get('/api/news/latest?portal=PortalA')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]['portal'] == 'PortalA'


@pytest.mark.parametrize("order", ["asc", "desc"])
def test_get_latest_news_ordering(client, news_with_dates, order):
    older_dt, newer_dt = news_with_dates
    resp = client.get(f'/api/news/latest?order={order}')
    assert resp.status_code == 200
    data = resp.get_json()
    data_coletas = [datetime.fromisoformat(item['data_coleta']) for item in data]
    expected = [older_dt, newer_dt] if order == 'asc' else [newer_dt, older_dt]
    assert data_coletas == expected


def test_get_latest_news_invalid_order(client):
    resp = client.get('/api/news/latest?order=foo')
    assert resp.status_code == 400
