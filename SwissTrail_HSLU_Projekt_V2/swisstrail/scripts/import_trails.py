"""Import official swissTLM3D hiking segment geometries from a GeoPackage.

Run: pip install shapely pyproj
     python scripts/import_trails.py source.gpkg --output trails.db
Output contains only public geometries, a spatial RTree and categories.
"""
import argparse
import json
import sqlite3
from pathlib import Path
from shapely import wkb
from shapely.ops import transform
from pyproj import Transformer

VALID = {"Wanderweg", "Bergwanderweg", "Alpinwanderweg"}

def read_gpkg_geometry(blob):
    if not blob or blob[:2] != b"GP":
        raise ValueError("Invalid GeoPackage geometry")
    envelope = (blob[3] >> 1) & 7
    offset = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope]
    return wkb.loads(bytes(blob[8+offset:]))

def find_layer(con):
    for table, geom, srid in con.execute(
        "SELECT table_name,column_name,srs_id FROM gpkg_geometry_columns"):
        columns = [c[1] for c in con.execute('PRAGMA table_info("' + table.replace('"','""') + '")')]
        category = next((c for c in columns if c.lower() == "wanderwege"), None)
        if category:
            return table, geom, srid, category
    raise ValueError("No vector layer has a WANDERWEGE category attribute")

def import_data(source, output, limit=None):
    src = sqlite3.connect(str(source))
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(str(output))
    try:
        name, geom, srid, category = find_layer(src)
        print("Reading layer", name, "CRS EPSG:", srid)
        transformer = Transformer.from_crs(srid, 4326, always_xy=True)
        dst.executescript("""DROP TABLE IF EXISTS trail_index;
          DROP TABLE IF EXISTS trail_segments;
          CREATE TABLE trail_segments(id INTEGER PRIMARY KEY,
            category TEXT NOT NULL, length_km REAL NOT NULL, coords_json TEXT NOT NULL);
          CREATE VIRTUAL TABLE trail_index USING rtree(id,min_lon,max_lon,min_lat,max_lat);""")
        count = 0
        escaped_table = name.replace('"','""')
        escaped_geom = geom.replace('"','""')
        escaped_cat = category.replace('"','""')
        query = f'SELECT "{escaped_geom}" AS geom, "{escaped_cat}" AS category FROM "{escaped_table}" WHERE "{escaped_cat}" IS NOT NULL'
        for row in src.execute(query):
            label = str(row["category"]).strip()
            if label not in VALID or not row["geom"]:
                continue
            shape = read_gpkg_geometry(row["geom"])
            if shape.geom_type == "LineString":
                lines = [shape]
            elif shape.geom_type == "MultiLineString":
                lines = list(shape.geoms)
            else:
                continue
            for line in lines:
                if line.is_empty or line.length <= 1:
                    continue
                simplified = line.simplify(5, preserve_topology=True)
                wgs = transform(transformer.transform, simplified)
                coords = [[round(x, 7), round(y, 7)] for x, y, *_ in wgs.coords]
                if len(coords) < 2:
                    continue
                minlon, minlat, maxlon, maxlat = wgs.bounds
                length_km = round(line.length / 1000, 3) if srid in (2056, 21781) else round(line.length / 1000, 3)
                inserted = dst.execute(
                    "INSERT INTO trail_segments(category,length_km,coords_json) VALUES(?,?,?)",
                    (label, length_km, json.dumps(coords, separators=(",",":"))))
                dst.execute("INSERT INTO trail_index VALUES(?,?,?,?,?)",
                            (inserted.lastrowid,minlon,maxlon,minlat,maxlat))
                count += 1
                if count % 10000 == 0:
                    dst.commit()
                    print(count, "segments")
                if limit and count >= limit: break
            if limit and count >= limit: break
        dst.commit()
        print(count, "segments written to", output)
        if not count:
            raise RuntimeError("No segments imported: inspect WANDERWEGE category values")
    finally:
        dst.close()
        src.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("geopackage", type=Path)
    p.add_argument("--output", type=Path, default=Path("trails.db"))
    p.add_argument("--limit", type=int)
    a = p.parse_args()
    import_data(a.geopackage, a.output, a.limit)
