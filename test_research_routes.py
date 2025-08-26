import pytest


def test_research_notes_crud(client):
    # initially empty
    resp = client.get('/api/research/notes')
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == []

    # create
    resp = client.post('/api/research/notes', json={'title': 'Note1', 'summary': 'Summary1', 'content': 'Content1'})
    assert resp.status_code == 201
    note = resp.get_json()['note']
    note_id = note['id']
    assert note['title'] == 'Note1'
    assert note['summary'] == 'Summary1'

    # update
    resp = client.put(
        f'/api/research/notes/{note_id}',
        json={'title': 'Updated', 'summary': 'Sum2', 'content': 'Updated'},
    )
    assert resp.status_code == 200
    updated = resp.get_json()['note']
    assert updated['title'] == 'Updated'
    assert updated['summary'] == 'Sum2'

    # delete
    resp = client.delete(f'/api/research/notes/{note_id}')
    assert resp.status_code == 200

    # ensure empty again
    resp = client.get('/api/research/notes')
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == []

def test_create_note_with_null_content(client):
    resp = client.post('/api/research/notes', json={'title': 'Only title', 'content': None})
    assert resp.status_code == 400
