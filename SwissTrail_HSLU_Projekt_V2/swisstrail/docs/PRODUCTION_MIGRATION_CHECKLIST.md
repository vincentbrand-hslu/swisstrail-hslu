# SwissTrail – sichere Migration zu Version 3

Stand: 09.11.2026. Dieses Dokument ist ein **Migrationsplan** und keine Bestätigung einer bereits abgeschlossenen Migration.

## Festgestellter Ist-Zustand (Railway production)
- Dienst: `swisstrail-hslu`, Domain: `swisstrail-hslu-production.up.railway.app`
- GitHub: `vincentbrand-hslu/swisstrail-hslu`, Branch: `main`
- Railway Root Directory: `SwissTrail_HSLU_Projekt_V2/swisstrail`
- Letztes überprüftes Deployment: erfolgreich (Version 2)
- Kein Volume angeschlossen; keine app-spezifischen Environment-Variablen konfiguriert
- Aktuelle Anwendung verwendet den Pfad `SWISSTRAIL_DB` oder standardmässig `swisstrail.db` neben `app.py`.
- Das Dockerfile setzt zwar `SWISSTRAIL_DB=/data/swisstrail.db`, aber diese Variable ist **nur wirksam, wenn das Dockerfile auch tatsächlich verwendet wird**. Der Railway-Service meldet den Builder `RAILPACK`.

## Datenverlust vermeiden
1. **Vor Volume-Anbindung feststellen, ob echte Konten/gespeicherte Routen existieren.**
2. **Vor Änderungen eine Kopie der laufenden SQLite-Datei mit den Tabellen `users`, `sessions`, `places`, `routes` sichern.** Die Kopie nicht in Git committen und nicht öffentlich weitergeben.
3. Prüfen, welcher Dateipfad im laufenden Container tatsächlich verwendet wird. Wenn die Datei schon auf flüchtigem Speicher liegt, vor der Migration exportieren.
4. Volume auf Railway für den Web-Service anlegen und unter `/data` mounten. Achtung: Das neue Volume überdeckt bestehende Dateien an diesem Mount-Pfad und löst einen Redeploy aus.
5. `SWISSTRAIL_DB=/data/swisstrail.db` und `SWISSTRAIL_SECURE_COOKIE=1` setzen, **nachdem** die bisherige Datenbank übertragen wurde.
6. Nur eine Replica betreiben (SQLite). App-Start, Login und bereits vorhandene Konten/Routen prüfen; danach erneut deployen und Persistenz prüfen.
7. Railway Volume Backups nach verfügbarem Plan einschalten.

## GeoAdmin – anklickbare Wegabschnitte
Die GeoAdmin-WMTS-Kartenebene besteht aus Rasterkacheln und liefert beim Klick keine routenfähigen Vektordaten. Version 3 ergänzt einen Import aus swisstopo GeoPackage sowie eine räumliche Abfrage. Auf dem öffentlichen Dienst funktioniert die Detailanzeige erst **nach** Datenimport und Bereitstellung der importierten `trails.db` auf dem Volume; nicht schon nach einer reinen Codeaktualisierung. Angezeigt wird die Länge des **Wegabschnitts**, nicht einer vollständigen Wanderung.

## Release-Gates
- [ ] Bestehende Daten inventarisiert und gesichert oder ausdrücklich als verzichtbar bestätigt
- [ ] Volume korrekt eingehängt; SQLite-Pfad und Cookie-Sicherheit wirksam
- [ ] Migration von Testdaten geprüft; Registrierung/Login/Löschen getestet
- [ ] Importdaten für offiziellen Wanderweg vorhanden
- [ ] API-Tests und manuelle Kartentests bestanden
- [ ] Änderungen im separaten Branch geprüft, danach Merge und Railway Deployment kontrolliert
