# SwissTrail 3 – offizielle Wanderwegabschnitte

## Laufende Produktion

Railway Projekt `adaptable-balance`, Service `swisstrail-hslu`, Umgebung `production`.
Volume `swisstrail-data` auf `/data`, SQLite `SWISSTRAIL_DB=/data/swisstrail.db`.
`SWISSTRAIL_SECURE_COOKIE=1`. Datenbank wurde neu angelegt; alte Testkonten wurden nicht migriert.

## swisstopo Geodaten importieren

Die WMTS-Karte dient der Visualisierung. Die Klickfunktion benötigt zusätzlich
**swissTLM3D Wanderwege GeoPackage** von
https://data.geo.admin.ch/ch.swisstopo.swisstlm3d-wanderwege/swisstlm3d-wanderwege/swisstlm3d-wanderwege_2056_5728.gpkg.zip

1. Archiv herunterladen und GeoPackage entpacken.
2. `pip install shapely pyproj`
3. `python scripts/import_trails.py /pfad/zu/datei.gpkg --output trails.db`
4. Prüfen, ob `trails.db` Einträge hat. Die Datei nur auf das Railway-Volume
   `/data/trails.db` übertragen (nicht nach GitHub committen).
5. `SWISSTRAIL_TRAILS_DB=/data/trails.db` setzen.
6. `/api/health` prüfen: `official_trails_loaded: true`.
7. Auf Karte einen offiziellen Weg anklicken: Popup zeigt **einzelnen
   Wegabschnitt** und seine amtliche Kategorie. Gesamtrouten-Routing ist nicht implementiert.

## Tests
`pip install -r requirements.txt pytest`, dann `pytest -q`.

## Hinweis
Ein Release ohne importierte `trails.db` würde lediglich den Klick-Schalter
aktivieren, aber beim Klicken eine Fehlermeldung zeigen. Daher vor Merge
den Datensatz importieren und die Abfrage prüfen.
