"""Read-only spatial lookup of swisstopo's imported hiking trail segments.

Each returned length describes a single mapped segment, not a full hike.
"""
import json
import math
import os
import sqlite3
from pathlib import Path

DEFAULT_TRAILS_DB = Path(os.getenv(
    "SWISSTRAIL_TRAILS_DB",
    "/data/trails.db" if os.getenv("RAILWAY_ENVIRONMENT") else str(Path(__file__).parent / "trails.db"),
))

def segment_distance_m(lat, lon, coords):
    scale_x = 111320 * math.cos(math.radians(lat))
    scale_y = 111195
    def local(p):
        return (float(p[0] - lon) * scale_x, float(p[1] - lat) * scale_y)
    best = float("inf")
    for a, b in zip(coords, coords[1:]):
        ax, ay = local(a)
        bx, by = local(b)
        dx, dy = bx - ax, by - ay
        denom = dx*dx + dy*dy
        t = max(0, min(1, (-ax*dx-ay*dy)/denom)) if denom else 0
        best = min(best, math.hypot(ax+t*dx, ay+t*dy))
    return best

def nearby_segment(lat, lon, radius_m=65, db_path=None):
    path = Path(db_path or DEFAULT_TRAILS_DB)
    if not path.is_file():
        return None
    dx = radius_m / (111320 * max(0.1, math.cos(math.radians(lat))))
    dy = radius_m / 111195
    # Query-only database is deliberately opened read-only.
    try:
        con = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute("""SELECT s.id,s.category,s.length_km,s.coords_json
              FROM trail_index i JOIN trail_segments s ON s.id=i.id
              WHERE i.min_lon <= ? AND i.max_lon >= ?
                AND i.min_lat <= ? AND i.max_lat >= ?
              LIMIT 500""", (lon+dx, lon-dx, lat+dy, lat-dy)).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return None
    winner = None
    for row in rows:
        coords = json.loads(row["coords_json"])
        dist = segment_distance_m(lat, lon, coords)
        if dist <= radius_m and (winner is None or dist < winner["click_distance_m"]):
            winner = {"id": row["id"], "category": row["category"],
              "length_km": row["length_km"], "coordinates": coords,
              "click_distance_m": round(dist, 1), "length_type": "Wegabschnitt",
              "source": "swisstopo swissTLM3D Wanderwege"}
    return winner
