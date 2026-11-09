# SwissTrail – Security-Konzept

## Implementierte Massnahmen
- Passwörter per `hashlib.scrypt` mit individuellem Salt, keine Klartextspeicherung.
- Zufällige Session-Tokens: in SQLite nur SHA-256-Digest; Cookie `HttpOnly`, `SameSite=Lax`, im Railway-HTTPS-Deployment `Secure`.
- `user_id`-basierte Zugriffskontrolle für Orte und Routen; fremde Datensätze werden nicht ausgegeben.
- Parameterisierte SQL-Statements und Pydantic-Eingabevalidierung mit Längen-/Koordinatenlimits.
- Fremde `Origin`-Header bei POST/PATCH/DELETE werden abgelehnt.
- Frontend: Textausgabe via `textContent` beziehungsweise HTML-Escaping.
- Offizielle Wanderwege als schreibgeschützte SQLite-Datenbank.
- Keine Zugangsdaten, Session-Tokens, SQLite-Benutzerdateien oder `.env` in Git committen.

## Verbleibende Risiken
- Kein Login-Rate-Limiting und keine MFA; nicht für öffentlichen Hochlastbetrieb gehärtet.
- Kein vollständiger CSRF-Token-Schutz (Origin-/SameSite-Abwehr ist nur Basisschutz).
- Keine Self-Service-Kontolöschung, Passwortreset oder formale Datenschutzprüfung.
- Volume-Persistenz ist **kein Backup**; Backup- und Wiederherstellungsprobe noch zu dokumentieren.
- Drittanbieter: GeoAdmin, Leaflet CDN, Webfonts; Netzwerk nötig.
- Wanderwegkategorie und Länge liefern keine Sicherheitsgarantie: keine Live-Sperrungen, Wetter, Schnee oder Lawinenlage.

## Nachweise vor Abgabe
- [ ] Repo-History auf Credentials prüfen
- [ ] HTTPS / Secure Cookie am Browser nachweisen
- [ ] Falsche Logins und fremde Datensätze ausprobieren
- [ ] Manuelles Testprotokoll mit Datum und Tester ergänzen
- [ ] Zugriff auf Railway und GitHub auf Projektteam begrenzen
- [ ] Backup/Restore und Datenschutzfragen dokumentieren

**Verwendung:** HSLU-Schulprototyp, keine sichere Navigationsanwendung.