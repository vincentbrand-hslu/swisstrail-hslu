# Testplan und Testnachweise – SwissTrail

## Testebenen
**Unit:** Distanzformel und geometrische Nähe eines Wegsegments. **Integration:** Registrierung, Login, CRUD Orte und Routen, Nutzertrennung, Validierung, externe-API-Fehler. **System:** Browser über HTTPS, swisstopo-Karte, Suche, Wegklick, Speichern und Reload.

## Automatische Testausführung
```bash
cd SwissTrail_HSLU_Projekt_V2/swisstrail
python -m pip install -r requirements.txt
python -m pytest -q
# Bei laufendem Server: python scripts/system_check.py
```
GitHub Actions: `.github/workflows/tests.yml`, `.github/workflows/production-smoke.yml`.

## Bereits beobachtete Nachweise
- GitHub Actions «SwissTrail tests», Run **42632719648**, am 09.11.2026 erfolgreich; **nach weiteren Commits neu überprüfen**.
- GitHub Actions «SwissTrail production smoke test», Run **42633469894**, am 09.11.2026 erfolgreich; echte Segmentantworten für (47.056,8.485), (46.977,8.255), (47.009,8.524).
- Railway-Deployment des HSLU-Prototyps erfolgreich; Volume `/data` vorhanden.
- Nutzer bestätigte am 09.11.2026, dass der Wanderwegklick im Browser funktioniert. Das ersetzt nicht das vollständige manuelle Systemtestprotokoll.

## Automatisierte Chromium-Systemtests (09.11.2026)
Die Datei `tests/browser_e2e.py` startet die echte SwissTrail-Webanwendung mit einer temporären SQLite-Testdatenbank und bedient sie anschliessend über einen **headless Chromium-Browser mit Playwright**. Der Testlauf für GitHub-Commit `26da4cc90b47b65159666c0bf261eb96473240d1` wurde erfolgreich abgeschlossen:

| Browser-Systemtest | Überprüfter Nutzerablauf | Ergebnis |
|---|---|---|
| `test_public_expedition_homepage_browser` | Expedition-Startseite, Credits Vincent/Marlon/Enzkar/Kevin, Regionen, Überrasch-mich, Sprung zur Karte | Bestanden |
| `test_official_trails_and_geoadmin_search_browser` | Echte Leaflet-Klickbehandlung; RTree-Testsegment wird im Popup mit Länge/Kategorie angezeigt; GeoAdmin-Suchergebnis wird ausgewählt | Bestanden |
| `test_registration_saved_places_routes_and_login` | Registrierung, Anmeldung, Ort mit Notiz speichern, eigene Route zeichnen und speichern, Seiten-Reload, Abmeldung und Neuanmeldung mit erhaltenen Daten | Bestanden |
| `test_mobile_layout_browser` | Mobile Ansicht (390 × 844), zentrale Buttons und Regionskarten, keine horizontale Überbreite | Bestanden |

**Wichtige Testgrenzen:** Der Browser läuft in GitHub Actions, nicht auf einem physischen Smartphone. GeoAdmin-Suchantwort und WMTS-Kacheln werden in diesen isolierten Tests simuliert; die öffentliche GeoAdmin-Integration wurde zusätzlich in anderen Live-Tests geprüft. Die Wegklickfunktion nutzt eine eigens für den Test angelegte RTree-Datenbank mit einem realen FastAPI-Endpunkt. Die Tests legen **keine** Konten auf Railway an.

Ausführen:
```bash
python -m pip install -r requirements.txt
python -m pip install playwright
python -m playwright install chromium
python -m pytest -q tests/browser_e2e.py -v
```

Die GitHub-Actions-Workflowdatei `.github/workflows/tests.yml` führt die Chromium-Systemtests bei Pull Requests automatisch durch. Browser-Screenshots sind als Actions-Artefakt abrufbar.

## Manuelle Browser-Testfälle (nicht erfunden, vom Team auszufüllen)
| ID | Test | Erwartet | Datum/Browser/Testperson | Ist-Ergebnis | Status |
|---|---|---|---|---|---|
| M01 | Desktop und Smartphone öffnen | Layout und Karte bedienbar | | | Offen |
| M02 | Region Rigi/Pilatus/Chur klicken | Karte zentriert und zoomt | | | Offen |
| M03 | Wanderweg anklicken | Popup mit km und amtlicher Kategorie | | | Offen |
| M04 | Abseits eines Wanderwegs klicken | Kein falsches Segment, Hinweis | | | Offen |
| M05 | Nach Luzern suchen | GeoAdmin-Ergebnisse, Kartensprung | | | Offen |
| M06 | Konto registrieren/anmelden | Login erfolgreich | | | Offen |
| M07 | Ort und Notiz speichern/bearbeiten/löschen | CRUD erfolgreich | | | Offen |
| M08 | Eigene Route speichern/anzeigen/löschen | km und eigene Schwierigkeit | | | Offen |
| M09 | Abmelden, neu anmelden, Reload | Einträge bleiben vorhanden | | | Offen |
| M10 | Zweitkonto | Daten des Erstkontos unsichtbar | | | Offen |
| M11 | Redeploy mit gespeichertem Ort | Eintrag bleibt nach Deployment | | | Offen |
| M12 | Keyboard / reduzierte Bewegung | Buttons erreichbar, ruhige Animationen | | | Offen |

Die Spalten mit Beobachtung und Status sind erst nach tatsächlichem Test zu befüllen. Kein manueller Test wird pauschal als bestanden behauptet.
## Ergänzter Chromium-Test: Touren-Werkzeuge
`test_registration_saved_places_routes_and_login` kontrolliert nach dem Erstellen und erneuten Laden einer eigenen Route auch die Filterung (kein Treffer und Treffer), die Sortierung und den Browser-Download einer GPX-1.1-Datei mit zwei Trackpunkten, Wegnamen und selbst gewählter Kategorie. Diese Prüfungen laufen auf einer **isolierten SQLite-Testdatenbank**. Den aktuellen GitHub-Actions-Status erst nach Abschluss des jeweiligen Runs als bestanden markieren.
