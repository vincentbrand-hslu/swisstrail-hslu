# Projektmanagement und Nachweise – SwissTrail

## Ziel und Vorgehen
Ziel: datengetriebene Webanwendung für Smart Travel gemäss HSLU ANG_INF, mit öffentlicher GeoAdmin-API, eigenem REST-Backend, persistenten Daten und mindestens zwei zentralen Nutzungsoperationen.

Die Projektphasen der Aufgabenstellung wurden als Arbeitsabschnitte übernommen:

| Phase | Lieferobjekt | Beobachtbarer Projektstand |
|---|---|---|
| Kundenanforderungen | Smart-Travel-Profil und Bedienanforderungen | im README und Spezifikation definiert |
| Software spezifizieren | F01–F08, nichtfunktionale Kriterien, Datenmodell | `docs/SPEZIFIKATION.md` |
| Architektur | Browser, Backend, externe API, 2 SQLite-Dateien | Mermaid-Komponentendiagramm |
| Implementierung | GeoAdmin-Ortssuche, Konten, Orte, eigene Routen | in `app.py`, `static/` |
| Geodaten-Erweiterung | Amtliche swisstopo-Segmente, SQLite-RTree | `trail_data.py`, `scripts/import_trails.py` |
| Testen | pytest, CI, Live-API, manuelle Browser-Tests | `docs/TESTPLAN.md`, GitHub Actions |
| Deployment | Railway + persistentes Volume | öffentlich erreichbar, Dockerfile, `docs/RAILWAY_DEPLOYMENT.md` |
| Präsentation | 20 Minuten inklusive Demo | `docs/PRAESENTATION.md` |

## Zeitliche Meilensteine / Belege
- 05.11.2026: Railway-Service aus GitHub-Repository eingerichtet (Deployment-History auf Railway).
- 09.11.2026: SQLite-Volume angelegt, Konfiguration angepasst, Deployment erfolgreich.
- 09.11.2026: swisstopo-Wanderwegsegmente (409'163) importiert, öffentlicher API-Smoke-Test erfolgreich.
- 09.11.2026: Browser-Klick auf Wanderwege vom Nutzer als funktionierend bestätigt.
- 09.11.2026: Aktualisierung von Abgabeunterlagen und visueller Oberfläche im separaten Feature-Branch.

## Verantwortung (Team selbst ergänzen)
| Aufgabenbereich | Zuständige Person(en) | Individueller Beitrag / Nachweis |
|---|---|---|
| Projektleitung / Kundenanforderungen | Vincent | |
| Frontend / UI | Enzkar | |
| FastAPI / Geschäftslogik | Marlon | |
| SQLite / swisstopo-Import | Kevin | |
| Tests / Security | Vincent & Kevin | |
| Dokumentation / Demo | Enzkar & Marlon | |

**Projektteam:** Vincent, Marlon, Enzkar und Kevin. 


## Decisions (kurzes ADR)
1. **SQLite statt externem DB-Service**: Kursanforderung und schnelle Entwicklung; Risiko: nur eine Replica, Backup nötig.
2. **FastAPI statt fertigem Backenddienst**: klar nachvollziehbarer REST-Layer; zusätzlicher Wartungsaufwand.
3. **GeoAdmin WMTS plus swisstopo GeoPackage**: WMTS für die Karte, GeoPackage für anklickbare Segmentgeometrie; kein Start-Ziel-Routing.
4. **Railway als VM-basierte Cloud-Hosting-Plattform**: HTTPS/Deployments einfach, Konfiguration und Datenhaltung dokumentiert; Docker-/Container-Alternative zur HSLU-VM gemäss Projektauftrag vor Besprechung mit Dozent abgleichen.

