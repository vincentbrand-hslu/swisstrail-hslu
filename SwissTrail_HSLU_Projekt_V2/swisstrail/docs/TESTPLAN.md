# Testplan / Qualitätssicherung

## Automatisierte Unit- und Integrationsprüfungen
Auf dem Entwicklungsgerät: `python -m pytest -q`.

Abgedeckt:
- Account registrieren, Login, Logout, ungültige Anmeldung, doppelte Benutzernamen.
- Privater CRUD-Lebenszyklus von gespeicherten Orten.
- Distanzformel und negative Eingabevalidierung (Punktanzahl, keine Null-Strecke, erlaubte Schwierigkeit).
- Route-CRUD und strikte Datentrennung zweier Konten (404 statt fremde Daten).
- Cross-Origin-Blockade bei Cookie-Schreibzugriffen.
- Fehlerbehandlung bei nicht erreichbarem externem SearchServer (502).
- HTTP-Startseite, API-Health und OpenAPI-Dokumentation.

## Integrations- und System-Smoke-Test (laufender Server)
1. `python -m uvicorn app:app --reload` starten.
2. `python scripts/system_check.py` ausführen.
3. Browser öffnen, Karte prüfen und nach **Luzern** suchen; externe Netzwerkverbindung nötig.
4. Account registrieren; Ort speichern und löschen.
5. „Route zeichnen“ anklicken, drei Punkte entlang eines Wegs setzen, „Fertig“ und Schwierigkeit auswählen.
6. Prüfen: km-Anzeige vor dem Speichern; nach Speichern Route anklicken und km/Schwierigkeit im Popup prüfen.
7. Browser neu laden: Route und Merkliste weiterhin vorhanden.
8. Mit zweitem Account prüfen: fremde Routen bleiben unsichtbar.
9. `docker compose up --build -d`, danach dieselben Schritte über http://127.0.0.1:8000 ausführen.

## Testprotokoll (vom Team auszufüllen)
| Datum | Umgebung / Browser | Testfall | Soll | Ist | Status | Tester |
|---|---|---|---|---|---|---|
| | | Ortssuche Luzern | Treffer | | | |
| | | Karteneinblendung | Wanderwege sichtbar | | | |
| | | Route 3 Punkte | Länge und Schwierigkeit | | | |
| | | Dauerhafte Speicherung | Nach Neustart vorhanden | | | |
| | | VM-Demo | extern erreichbar | | | |

**Wichtig:** Diese manuellen Tests sind noch nicht ausgeführt und dürfen im Projektbericht nicht als bestanden behauptet werden.
