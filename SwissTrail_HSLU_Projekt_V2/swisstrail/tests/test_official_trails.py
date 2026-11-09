"""Focused tests for official trail segment proximity and route metadata."""
import json
import sqlite3
from fastapi.testclient import TestClient
from app import app
import trail_data

def test_official_segment(tmp_path, monkeypatch):
    db = tmp_path / "trails.db"
    con = sqlite3.connect(db)
    con.executescript("""CREATE TABLE trail_segments(id INTEGER PRIMARY KEY,
         category TEXT, length_km REAL, coords_json TEXT);
         CREATE VIRTUAL TABLE trail_index USING rtree(
         id,min_lon,max_lon,min_lat,max_lat);""")
    con.execute("INSERT INTO trail_segments VALUES(1,?,?,?)",
        ("Bergwanderweg",0.55,json.dumps([[8.3,47.0],[8.306,47.003]])))
    con.execute("INSERT INTO trail_index VALUES(1,8.3,8.306,47.0,47.003)")
    con.commit()
    con.close()
    assert trail_data.nearby_segment(47.0015,8.303,db_path=db)["category"] == "Bergwanderweg"
    assert trail_data.nearby_segment(47.2,8.3,db_path=db) is None
    monkeypatch.setattr("app.DEFAULT_TRAILS_DB",db)
    monkeypatch.setattr(trail_data,"DEFAULT_TRAILS_DB",db)
    with TestClient(app) as client:
        response = client.get("/api/trails/nearby?lat=47.0015&lon=8.303")
        assert response.status_code == 200
        assert response.json()["segment"]["length_type"] == "Wegabschnitt"
        assert client.get("/api/trails/nearby?lat=90&lon=8.3").status_code == 422
