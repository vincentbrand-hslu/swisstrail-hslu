# SwissTrail 2.0 – HSLU ANG_INF

Eine browserbasierte, datengetriebene Wanderkarten-Anwendung als Schulprojekt. Offizielle swisstopo/GeoAdmin-Karten und Wanderwege anzeigen, Orte über GeoAdmin suchen, eigene Routen auf der Karte einzeichnen, Länge berechnen, Schwierigkeit selbst erfassen und Nutzer-Daten dauerhaft in SQLite speichern.

## Schnellstart – Windows / VS Code

1. ZIP **entpacken** und in VS Code den **Unterordner `swisstrail`** öffnen, in dem `app.py` und `requirements.txt` liegen.
2. Terminal (PowerShell) öffnen:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

3. Browser öffnen: **http://127.0.0.1:8000**. API-Doku: http://127.0.0.1:8000/docs.
4. **Anmelden/Registrieren** → **Route zeichnen** → Punkte auf der Karte setzen → **Fertig** → Schwierigkeit selbst auswählen → **Speichern**.
5. Gespeicherte blaue Linie anklicken: Popup mit **km und Schwierigkeit**. Alternative: **Meine Routen** → **Auf Karte**.

Falls PowerShell im übergeordneten Ordner ist: erst `cd swisstrail`.

### Lokaler Docker-Start (auf Windows: Docker Desktop)

```bash
docker compose up --build -d
# http://127.0.0.1:8000
docker compose logs -f web
```

SQLite verbleibt im persistenten Volume `swissdata`; bei lokalem Start als Datei `swisstrail.db` im Projektordner (nicht in Git).

### Tests

```bash
python -m pytest -q
python scripts/system_check.py   # nur wenn Server bereits gestartet ist
```

GitHub Actions führt Tests bei Push/PR aus. **Workflow erst aktiv nach Push ins eigene Repository.**

## Deployment – HSLU-VM / andere Linux-VM

**Variante A – VM im Hochschulnetz ohne öffentliche Domain:**
1. Docker Engine und Docker Compose Plugin auf der Linux-VM installieren (gemäss HSLU-Vorgaben).
2. Code per Git klonen oder übertragen.
3. In `compose.yaml` Portbindung `127.0.0.1:8000:8000` beibehalten; nur via VM-SSH-Tunnel erreichbar.
4. Auf lokalem Laptop: `ssh -L 8000:127.0.0.1:8000 USER@VM-HOST` und http://127.0.0.1:8000 öffnen.

**Variante B – öffentlich erreichbare VM mit DNS und HTTPS:**
1. Voraussetzung: eigene Domain, DNS-Eintrag für VM, Port 80/443 offen.
2. `cp .env.example .env` und `DOMAIN` auf echte DNS-Domain setzen; **niemals die Beispieldomain übernehmen**.
3. `docker compose -f compose.prod.yaml up --build -d`.
4. Caddy stellt HTTPS bereit, leitet an FastAPI weiter, setzt sichere Session-Cookies.
5. Über die echte Domain Health- und Browser-Tests durchführen.
6. Vor öffentlicher Freigabe die offenen Security-Punkte in `docs/SECURITY.md` abarbeiten.

**Wichtig:** Das Deployment ist vorbereitet, aber keine VM wurde von diesem ZIP aus tatsächlich bereitgestellt.

## Wie die Route funktioniert

- GeoAdmin `ch.swisstopo.swisstlm3d-wanderwege` ist **WMTS-Rasterkarte**, keine mit Klick abfragbare Route (siehe offizielle GeoAdmin-Layer-Tabelle).
- Durch `Route zeichnen` setzt der Nutzer Stützpunkte. FastAPI berechnet mit der Haversine-Formel die Summe der **2D-Luftlinienabschnitte** zwischen den Stützpunkten.
- Die Karte **rastet nicht automatisch auf Wanderwege ein**. Mehr Punkte entlang der Kurven verbessern die Näherung. Höhenmeter und echte 3D-Weglänge sind nicht enthalten.
- Der Grad **Wanderweg / Bergwanderweg / Alpinwanderweg** wird bewusst **manuell durch den Nutzer** erfasst, nicht automatisch aus GeoAdmin erfunden.
- Für reale Wanderungen sind aktuelle offizielle Wegmeldungen/Wetter und eigene Erfahrung zu berücksichtigen.

## API-Endpunkte

| Methode | URL | Zweck |
|---|---|---|
| POST | `/api/register`, `/api/login`, `/api/logout` | Authentifizierung |
| GET | `/api/me` | Aktuelles Konto |
| GET/POST | `/api/places` | Orte lesen/anlegen |
| PATCH/DELETE | `/api/places/{id}` | Notiz ändern / löschen |
| GET/POST | `/api/routes` | Eigene Routen lesen/anlegen |
| GET/DELETE | `/api/routes/{id}` | Eigene Route anzeigen/löschen |
| GET | `/api/geoadmin/search?q=Luzern` | GeoAdmin-Standortsuche |
| GET | `/api/geoadmin/layer` | GeoAdmin-Layer-Metadaten |
| GET | `/api/health` | Betriebsstatus |

## Projektdokumentation (HSLU)

- [Software-Spezifikation + Architektur + Datenmodell](docs/SPEZIFIKATION.md)
- [Testing und Testprotokoll](docs/TESTPLAN.md)
- [Security-Konzept](docs/SECURITY.md)
- [20-Minuten-Präsentationsgliederung](docs/PRAESENTATION.md)

## Git / Zusammenarbeit

```bash
git init
git add .
git commit -m "Initial SwissTrail prototype with GeoAdmin and routing"
# Neues eigenes Repo auf GitHub/GitLab anlegen, Remote eintragen,
# danach git push ausführen. Keine Passwörter, DB-Dateien oder .env committen.
```

Jedes Gruppenmitglied sollte danach eigene **inhaltlich aussagekräftige Commits** erstellen. Eine vorherige echte Commit-History lässt sich aus der gelieferten ZIP-Datei nicht nachträglich rekonstruieren.

## Quellen und Credits

- Daten: [swisstopo / geo.admin.ch](https://www.geo.admin.ch/) und [GeoAdmin Tech Docs](https://docs.geo.admin.ch/).
- Offizielle Layer-ID: `ch.swisstopo.swisstlm3d-wanderwege`.
- Frontend: [Leaflet](https://leafletjs.com/) (CDN), HTML/CSS/JS.
- Backend: FastAPI/Pydantic, SQLite, httpx. Deployment: Docker und Caddy.
- Projektarbeit: HSLU ANG_INF; **Teammitglieder und Rollen noch vom Team zu ergänzen**.
- Keine externen DB-Services; die GeoAdmin-API und Kartenkacheln benötigen Internet.
