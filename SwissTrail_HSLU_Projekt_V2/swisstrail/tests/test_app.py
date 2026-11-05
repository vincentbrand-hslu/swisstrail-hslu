import os
import tempfile
from pathlib import Path

_tempdir = tempfile.TemporaryDirectory()
os.environ['SWISSTRAIL_DB'] = str(Path(_tempdir.name) / 'test.db')
from fastapi.testclient import TestClient
from app import app


def test_registration_and_private_places():
    with TestClient(app) as c:
        assert c.get('/api/health').status_code == 200
        assert c.get('/api/places').status_code == 401
        r = c.post('/api/register', json={'username':'testuser','password':'secret123'})
        assert r.status_code == 201
        p = c.post('/api/places', json={'name':'Pilatus','lat':46.98,'lon':8.25,'notes':'Schön'})
        assert p.status_code == 201
        place_id = p.json()['id']
        assert len(c.get('/api/places').json()) == 1
        assert c.patch('/api/places/'+str(place_id),json={'notes':'Toll'}).status_code == 200
        assert c.delete('/api/places/'+str(place_id)).status_code == 200
        assert c.get('/api/places').json() == []
        assert c.post('/api/logout').status_code == 200
        assert c.get('/api/me').status_code == 401
        assert c.post('/api/login',json={'username':'testuser','password':'secret123'}).status_code == 200


def test_duplicate_and_invalid_registration():
    with TestClient(app) as c:
        assert c.post('/api/register', json={'username':'alpha','password':'password123'}).status_code == 201
        assert c.post('/api/register', json={'username':'alpha','password':'password123'}).status_code == 409
        assert c.post('/api/register', json={'username':'x','password':'password123'}).status_code == 422
        assert c.post('/api/login',json={'username':'alpha','password':'incorrect'}).status_code == 401
