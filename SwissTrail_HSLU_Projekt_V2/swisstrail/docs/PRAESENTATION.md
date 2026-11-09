# SwissTrail – 20-Minuten-Schlusspräsentation inkl. Demo

| Zeit | Inhalt | Nachweis |
|---|---|---|
| 0:00–1:30 | Team, reale Rollen und Projektplanung | Namen/Zuständigkeiten ergänzen |
| 1:30–3:00 | Kundenproblem: Smart Travel | Wanderwege entdecken, Streckenideen organisieren |
| 3:00–4:30 | Anforderungen | F01–F08, Qualität und Deployment |
| 4:30–7:00 | Architektur / C4 | Browser → REST-Backend → GeoAdmin + SQLite |
| 7:00–8:30 | Externe API | GeoAdmin SearchServer, WMTS versus GeoPackage |
| 8:30–10:00 | Datenmodell / Security | Nutzer und Routen, scrypt, Cookies, Nutzertrennung |
| 10:00–14:30 | Live-Demo | Rigi → Wegklick → Suche → Konto → Ort / eigene Route |
| 14:30–16:00 | Qualität | pytest, CI, Live-Smoke-Test, manuelle Prüfungen |
| 16:00–17:30 | Deployment | Railway, Docker, SQLite, Volume |
| 17:30–20:00 | Entscheidungen, Grenzen, Lessons Learned | Abschnitte ≠ Routen, persönliche Reflexionen |

## Demo-Skript
1. `/api/health` zeigen und Standort des Services erklären.
2. [SwissTrail live](https://swisstrail-hslu-production.up.railway.app/) öffnen, Rigi-Regionskarte wählen.
3. Wanderweg anklicken; Distanz und offizielle Kategorie erläutern (kein SAC T1–T6).
4. GeoAdmin-Ortssuche (z.B. Luzern) vorführen, Backend-API `/api/geoadmin/search` erklären.
5. Mit Demo-Konto einen Ort merken, Notiz bearbeiten, Route mit Stützpunkten zeichnen und speichern.
6. Falls Zeit: Swagger `/docs`, GitHub Actions, Railway-Volume zeigen.

## Prüferfragen
**WMTS vs. GeoPackage?** Rasterkacheln sind Bilder. Klickbare Weggeometrie kommt aus importierten Vektordaten und wird räumlich indiziert.

**Wofür SQLite?** Lokale relationale Datenhaltung und amtliche Wegsegmente; persistent über ein Volume, keine Fremd-DB.

**Wo wird der Weg berechnet?** Amtliche Segmentlänge aus swisstopo-Geometrie; eigene Routen als 2D-Haversine-Summe, nicht automatisch am Wanderwegnetz.

**Sicherheit?** Scrypt+Salt, zufällige Session, Cookie-Flags, Eigentümerfilter, Origin-Prüfung.

**Grenzen?** Kein echtes Start-Ziel-Routing, keine 3D-Höhenmeter, keine aktuellen Wegsperrungen.

## Vor Abgabe
Screenshots/Backup der Demo, **echte** Teammitglieder und Rollen, Probedurchlauf auf 20 Minuten, manuellen Testplan sowie selbst formulierte Lessons Learned ergänzen.