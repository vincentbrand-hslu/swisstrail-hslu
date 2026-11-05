"""Unit and integration tests; never require public API or live map service."""
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Existing test suite imports app at collection time, all tests use isolated temp DB.
from app import RoutePoint, app, distance_km
from fastapi.testclient import TestClient


def test_distance_known_equator_example():
    # One degree longitude at equator (unit maths only; validation on RoutePoint
    # constrains actual SwissTrail coordinates to Switzerland, so use model_construct).
    start = RoutePoint.model_construct(lat=0, lon=0)
    end = RoutePoint.model_construct(lat=0, lon=1)
    assert 111.1 < distance_km([start, end]) < 111.3


def test_routes_crud_ownership_and_validation():
    data = {"name":"Pilatuswanderung", "difficulty":"Bergwanderweg",
            "notes":"Test", "points":[{"lat":46.98,"lon":8.25},{"lat":46.99,"lon":8.26}]}
    with TestClient(app) as a, TestClient(app) as b:
        assert a.get('/api/routes').status_code == 401
        assert a.post('/api/register',json={'username':'routetest_a','password':'password123'}).status_code == 201
        assert b.post('/api/register',json={'username':'routetest_b','password':'password123'}).status_code == 201
        created=a.post('/api/routes',json=data)
        assert created.status_code == 201,created.text
        route=created.json()
        assert route['length_km']>0
        assert route['difficulty']=='Bergwanderweg'
        assert len(a.get('/api/routes').json())>=1
        assert b.get('/api/routes').json()==[]
        assert b.get('/api/routes/'+str(route['id'])).status_code==404
        assert b.delete('/api/routes/'+str(route['id'])).status_code==404
        assert a.get('/api/routes/'+str(route['id'])).status_code==200
        assert a.post('/api/routes',json={**data,'difficulty':'T999'}).status_code==422
        assert a.post('/api/routes',json={**data,'points':[data['points'][0]]}).status_code==422
        assert a.post('/api/routes',json={**data,'points':data['points']*80}).status_code==422
        assert a.post('/api/routes',json={**data,'points':[data['points'][0]]*2}).status_code==422
        assert a.delete('/api/routes/'+str(route['id'])).status_code==200
        assert a.get('/api/routes/'+str(route['id'])).status_code==404


def test_same_origin_protection():
    with TestClient(app) as c:
        bad=c.post('/api/login',json={'username':'whoever','password':'wrongpass'},headers={'Origin':'https://other.example'})
        assert bad.status_code == 403


def test_external_api_error_is_handled():
    with TestClient(app) as c:
        with patch('app.httpx.AsyncClient') as mocked:
            mocked.return_value.__aenter__ = AsyncMock(return_value=mocked.return_value)
            mocked.return_value.__aexit__ = AsyncMock(return_value=None)
            mocked.return_value.get = AsyncMock(side_effect=__import__('httpx').ConnectError('offline'))
            response = c.get('/api/geoadmin/search?q=Luzern')
            assert response.status_code == 502
            assert 'nicht erreichbar' in response.json()['detail']


def test_http_html_and_health():
    with TestClient(app) as c:
        assert c.get('/').status_code == 200
        assert 'SwissTrail' in c.get('/').text
        assert c.get('/api/health').json()['status'] == 'ok'
        assert c.get('/docs').status_code == 200
