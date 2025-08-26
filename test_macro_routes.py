from collections import namedtuple
from datetime import datetime
from backend import db


def test_get_macro_indicators(client, monkeypatch):
    Row = namedtuple('Row', 'indicator value unit description updated_at')
    indicators = [Row('SELIC', 10.5, '%', 'Taxa Selic', datetime(2024, 1, 1))]

    monkeypatch.setattr(db.session, 'execute', lambda *args, **kwargs: indicators)

    resp = client.get('/api/macro/indicators')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['indicators']['SELIC']['value'] == 10.5


def test_get_indicator_history(client, monkeypatch):
    Row = namedtuple('Row', 'date value')
    history = [Row(datetime(2024, 1, 1), 10.5), Row(datetime(2024, 2, 1), 10.25)]

    class Result:
        def fetchall(self_inner):
            return history

    monkeypatch.setattr(db.session, 'execute', lambda *args, **kwargs: Result())

    resp = client.get('/api/macro/historical/SELIC')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert len(data['history']) == 2


def test_get_macro_summary(client, monkeypatch):
    Row = namedtuple('Row', 'indicator value unit')
    indicators = [Row('SELIC', 10.5, '%')]

    monkeypatch.setattr(db.session, 'execute', lambda *args, **kwargs: indicators)

    resp = client.get('/api/macro/summary')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['summary']['SELIC']['unit'] == '%'
