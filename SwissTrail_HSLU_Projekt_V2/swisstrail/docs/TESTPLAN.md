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