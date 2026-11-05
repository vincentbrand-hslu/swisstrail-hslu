# Security-Konzept (Basis für Unterrichtsprojekt)

## Umgesetzte Massnahmen
- `hashlib.scrypt` statt Klartext-Passwörtern, per Konto zufälliger Salt.
- Session-Token sind zufällig, in SQLite nur als SHA-256-Digest hinterlegt.
- `HttpOnly` und `SameSite=Lax` Cookies; in der VM TLS und `SWISSTRAIL_SECURE_COOKIE=1`.
- Datenbankzugriffe parameterisiert, keine SQL-Stringinterpolation von Nutzereingaben.
- Pydantic-Eingabekontrollen und maximale Text-/Punktlängen.
- Server prüft bei allen sensiblen CRUD-Endpunkten den Eigentümer.
- Cross-Origin-POST/PATCH/DELETE mit fremdem Origin-Header werden geblockt.
- Frontend escaped oder setzt vom Nutzer stammende Texte via `textContent`.
- Caddy-Deployment enthält HTTPS und grundlegende Sicherheits-Header.

## Vor öffentlichem produktivem Betrieb zusätzlich notwendig
- Rate-Limiting für Login/Registrierung, E-Mail-Verifizierung/Passwort-Reset.
- Vollständiger CSRF-Schutz mit Token, insbesondere für Browser ohne Origin-Header; ggf. Trusted-Proxies.
- Infrastruktur-Updates, Monitoring, SQLite-Backups und Wiederherstellung testen.
- Geregelter Zugriff auf VM / Firewall / Benutzerrechte, realen DNS-Namen konfigurieren.
- Datenschutz, Aufbewahrung, Löschung, Auskunft und Datenschutzerklärung prüfen.
- TLS-Zertifikat über öffentliche DNS und Port 80/443 nur bei freigeschalteter Infrastruktur.

## Restrisiko
Nicht für sicherheitskritische Navigation oder öffentliches Mehrmandanten-Produktionssystem geeignet. Benutzerdefinierte Routenschwierigkeit ist nicht objektiv verifiziert.
