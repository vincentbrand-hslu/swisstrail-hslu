"""SwissTrail – HSLU-Projektprototyp. Start: uvicorn app:app --reload"""
import hashlib
import json
import math
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

BASE = Path(__file__).resolve().parent
DB = Path(os.getenv("SWISSTRAIL_DB", str(BASE / "swisstrail.db")))
GEO = "https://api3.geo.admin.ch"
LAYER = "ch.swisstopo.swisstlm3d-wanderwege"
app = FastAPI(title="SwissTrail API", version="2.0")

@app.middleware("http")
async def reject_cross_origin_writes(request: Request, call_next):
    # Simple same-origin safeguard for cookie-authenticated JSON write endpoints.
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlsplit
            parsed = urlsplit(origin)
            expected = request.headers.get("host", "")
            if not (parsed.scheme in ("http", "https") and parsed.netloc == expected):
                return Response("Cross-origin request blocked", status_code=403)
    return await call_next(request)

app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


@contextmanager
def database():
    con = connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    with database() as con:
        con.executescript("""
          CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
            password_salt TEXT NOT NULL, password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
          );
          CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
          );
          CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
            name TEXT NOT NULL, difficulty TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '', points_json TEXT NOT NULL,
            length_km REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
          );
          CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
            name TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
          );
        """)


init_db()


def password_hash(password: str, salt: bytes) -> str:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request):
    token = request.cookies.get("swisstrail_session", "")
    if not token:
        raise HTTPException(401, "Bitte zuerst anmelden.")
    with database() as con:
        row = con.execute("""SELECT users.id, users.username FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE token_hash=? AND expires_at>?""",
        (token_digest(token), datetime.now(timezone.utc).isoformat())).fetchone()
    if not row:
        raise HTTPException(401, "Sitzung abgelaufen. Bitte erneut anmelden.")
    return dict(row)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=128)


class PlaceIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    lat: float = Field(ge=45, le=48.5)
    lon: float = Field(ge=5, le=11.5)
    notes: str = Field(default="", max_length=1000)


class NotesIn(BaseModel):
    notes: str = Field(max_length=1000)


def make_session(resp: Response, user_id: int):
    token = secrets.token_urlsafe(32)
    expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    with database() as con:
        con.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)",
                    (token_digest(token), user_id, expiry))
    secure = os.getenv("SWISSTRAIL_SECURE_COOKIE", "0") == "1"
    resp.set_cookie("swisstrail_session", token, httponly=True, secure=secure,
                    samesite="lax", max_age=7 * 86400, path="/")


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/api/register", status_code=201)
def register(body: Credentials, response: Response):
    username = body.username.strip().lower()
    if not re.fullmatch(r"[a-z0-9_.-]{3,40}", username):
        raise HTTPException(400, "Benutzername: 3–40 Zeichen (a–z, 0–9, _, . oder -).")
    salt = secrets.token_bytes(16)
    try:
        with database() as con:
            cur = con.execute("INSERT INTO users(username,password_salt,password_hash) VALUES(?,?,?)",
                              (username, salt.hex(), password_hash(body.password, salt)))
            uid = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Dieser Benutzername ist bereits vergeben.")
    make_session(response, uid)
    return {"id": uid, "username": username}


@app.post("/api/login")
def login(body: Credentials, response: Response):
    with database() as con:
        row = con.execute("SELECT * FROM users WHERE username=?", (body.username.strip().lower(),)).fetchone()
    valid = bool(row and secrets.compare_digest(password_hash(body.password, bytes.fromhex(row["password_salt"])), row["password_hash"]))
    if not valid:
        raise HTTPException(401, "Benutzername oder Passwort falsch.")
    make_session(response, row["id"])
    return {"id": row["id"], "username": row["username"]}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("swisstrail_session")
    if token:
        with database() as con:
            con.execute("DELETE FROM sessions WHERE token_hash=?", (token_digest(token),))
    response.delete_cookie("swisstrail_session", path="/")
    return {"ok": True}


@app.get("/api/me")
def me(request: Request):
    return current_user(request)


@app.get("/api/places")
def list_places(request: Request):
    user = current_user(request)
    with database() as con:
        rows = con.execute("SELECT id,name,lat,lon,notes,created_at FROM places WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/places", status_code=201)
def save_place(body: PlaceIn, request: Request):
    user = current_user(request)
    with database() as con:
        cur = con.execute("INSERT INTO places(user_id,name,lat,lon,notes) VALUES(?,?,?,?,?)",
                          (user["id"], body.name.strip(), body.lat, body.lon, body.notes))
        row = con.execute("SELECT id,name,lat,lon,notes,created_at FROM places WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.patch("/api/places/{place_id}")
def update_place(place_id: int, body: NotesIn, request: Request):
    user = current_user(request)
    with database() as con:
        cur = con.execute("UPDATE places SET notes=? WHERE id=? AND user_id=?", (body.notes, place_id, user["id"]))
        if not cur.rowcount:
            raise HTTPException(404, "Eintrag nicht gefunden.")
    return {"ok": True}


@app.delete("/api/places/{place_id}")
def delete_place(place_id: int, request: Request):
    user = current_user(request)
    with database() as con:
        cur = con.execute("DELETE FROM places WHERE id=? AND user_id=?", (place_id, user["id"]))
        if not cur.rowcount:
            raise HTTPException(404, "Eintrag nicht gefunden.")
    return {"ok": True}


@app.get("/api/geoadmin/search")
async def geoadmin_search(q: str = ""):
    if not 2 <= len(q.strip()) <= 100:
        raise HTTPException(400, "Bitte einen Ortsnamen mit mindestens 2 Zeichen eingeben.")
    try:
        async with httpx.AsyncClient(timeout=9) as client:
            resp = await client.get(f"{GEO}/rest/services/api/SearchServer",
                                    params={"searchText": q.strip(), "type": "locations", "origins": "zipcode,gg25,district,kantone,address", "limit": 12, "sr": 4326})
            resp.raise_for_status()
            raw = resp.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(502, "GeoAdmin-Suche momentan nicht erreichbar.")
    results = []
    for item in raw.get("results", []):
        a = item.get("attrs", {})
        # GeoAdmin SearchServer uses x=longitude, y=latitude when sr=4326.
        lon, lat = a.get("x"), a.get("y")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)) or not (45 <= lat <= 48.5 and 5 <= lon <= 11.5):
            continue
        label = re.sub("<[^>]*>", "", str(a.get("label", "Unbekannter Ort")))
        results.append({"name": label, "lat": lat, "lon": lon, "origin": a.get("origin", "")})
    return {"results": results}


@app.get("/api/geoadmin/layer")
async def layer_info():
    try:
        async with httpx.AsyncClient(timeout=9) as client:
            resp = await client.get(f"{GEO}/rest/services/api/MapServer/{LAYER}", params={"lang": "de"})
            resp.raise_for_status()
            return {"layer": LAYER, "metadata": resp.json()}
    except (httpx.HTTPError, ValueError):
        raise HTTPException(502, "GeoAdmin-Layer momentan nicht erreichbar.")


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "sqlite", "geoadmin_layer": LAYER}


# A saved route is an explicitly user-drawn polyline; it is NOT computed
# from the WMTS Wanderwege layer (WMTS is an image, not a route graph).
# Difficulty is supplied by the user, not inferred from the map tiles.
class RoutePoint(BaseModel):
    lat: float = Field(ge=45, le=48.5, allow_inf_nan=False)
    lon: float = Field(ge=5, le=11.5, allow_inf_nan=False)


class RouteIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    difficulty: str
    notes: str = Field(default="", max_length=1000)
    points: list[RoutePoint] = Field(min_length=2, max_length=120)

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, value):
        if value not in ("Wanderweg", "Bergwanderweg", "Alpinwanderweg", "Nicht bewertet"):
            raise ValueError("Unbekannte Schwierigkeit")
        return value


def distance_km(points):
    """Sum of geodesic great-circle distances between provided points (2D)."""
    total = 0.0
    for p, q in zip(points, points[1:]):
        lat1, lon1, lat2, lon2 = map(math.radians, (p.lat, p.lon, q.lat, q.lon))
        a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
        total += 6371.0088 * 2 * math.asin(min(1, math.sqrt(a)))
    return round(total, 3)


def serialise_route(row):
    item = dict(row)
    item["points"] = json.loads(item.pop("points_json"))
    return item


@app.get("/api/routes")
def list_routes(request: Request):
    user = current_user(request)
    with database() as con:
        rows = con.execute("SELECT * FROM routes WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
    return [serialise_route(r) for r in rows]


@app.post("/api/routes", status_code=201)
def create_route(body: RouteIn, request: Request):
    user = current_user(request)
    length = distance_km(body.points)
    if length < 0.01 or length > 250:
        raise HTTPException(422, "Route muss zwischen 10 m und 250 km lang sein.")
    if not body.name.strip():
        raise HTTPException(422, "Bitte Routennamen eingeben.")
    with database() as con:
        cur = con.execute("""INSERT INTO routes(user_id,name,difficulty,notes,points_json,length_km)
            VALUES(?,?,?,?,?,?)""", (user["id"], body.name.strip(), body.difficulty,
            body.notes, json.dumps([p.model_dump() for p in body.points]), length))
        row = con.execute("SELECT * FROM routes WHERE id=?", (cur.lastrowid,)).fetchone()
    return serialise_route(row)


@app.get("/api/routes/{route_id}")
def get_route(route_id: int, request: Request):
    user = current_user(request)
    with database() as con:
        row = con.execute("SELECT * FROM routes WHERE id=? AND user_id=?", (route_id, user["id"])).fetchone()
    if row is None:
        raise HTTPException(404, "Route nicht gefunden.")
    return serialise_route(row)


@app.delete("/api/routes/{route_id}")
def delete_route(route_id: int, request: Request):
    user = current_user(request)
    with database() as con:
        cur = con.execute("DELETE FROM routes WHERE id=? AND user_id=?", (route_id, user["id"]))
        if not cur.rowcount:
            raise HTTPException(404, "Route nicht gefunden.")
    return {"ok": True}
