import pytest


def test_company_news_crud(client):
    # initially empty
    resp = client.get('/api/company-news/ABCD')
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == []

    # create
    resp = client.post('/api/company-news', json={
        'ticker': 'ABCD',
        'title': 'Note1',
        'url': 'http://example.com',
        'source': 'Source',
        'summary': 'Summary',
        'content': 'Content',
        'author': 'Author',
        'published_at': '2024-01-01T00:00:00'
    })
    assert resp.status_code == 201
    note = resp.get_json()['note']
    note_id = note['id']
    assert note['ticker'] == 'ABCD'

    # update
    resp = client.put(f'/api/company-news/{note_id}', json={'title': 'Updated'})
    assert resp.status_code == 200
    assert resp.get_json()['note']['title'] == 'Updated'

    # delete
    resp = client.delete(f'/api/company-news/{note_id}')
    assert resp.status_code == 200

    # ensure empty again
    resp = client.get('/api/company-news/ABCD')
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == []
