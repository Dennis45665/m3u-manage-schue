# M3U zu .strm Files

Dieses Skript verarbeitet eine M3U-Datei, die Streams, Filme und Serien enthält. Aus dieser Datei werden für jeden Eintrag separate `.strm`-Dateien erzeugt.

---

## Was macht das Skript?

- Liest eine M3U-Datei mit Einträgen für Filme, Serien und andere Streams.
- Prüft, ob Video-Links tatsächlich herunterladbar/erreichbar sind (Minimal-Download, keine HTML-Fehlseiten).
- Nicht erreichbare Einträge werden protokolliert und in `tmp/offline.json` gesammelt.
- Für gültige Einträge wird ein Verzeichnis mit einem sicheren Namen erstellt und eine `.strm`-Datei mit dem Stream-URL abgelegt.
- Bestehende `.strm`-Dateien werden nur aktualisiert, wenn sich der Stream-URL ändert.
 - Löschregeln: Bei Filmen wird beim Entfernen die gesamte Ordnerstruktur des Films gelöscht. Bei Serien werden Episoden-Dateien gelöscht; ist eine Staffel vollständig betroffen, wird der gesamte Staffelordner gelöscht; sind alle Staffeln betroffen, wird der gesamte Serienordner gelöscht.

---

## Installation / Konfiguration

1. Repository klonen oder Dateien herunterladen

2.  `CONFIG.ini` anpassen mit folgendem Aufbau:

```ini
[M3U]
url = ...

[PATH]
main_path=/pfad/zum/projekt
path_movie=Filme
path_serien=Serien
path_m3u=m3u
```

---

## Nutzung

Nutze das mitgelieferte `m3u_script.sh` (Linux):

```bash
chmod +x m3u_script.sh
./m3u_script.sh
```

Das Shellscript prüft, ob ein virtuelles Environment (`venv`) existiert. Falls nicht, wird es erstellt, die Abhängigkeiten aus `requirements.txt` installiert und danach das Script gestartet.

Hinweis: Der Ordner `tmp/` wird zu Beginn eines Laufs geleert. Die Datei `tmp/offline.json` (nicht erreichbare Titel) wird pro Lauf neu erzeugt.

### Cronjob

Du kannst das Skript direkt als ausführbare Datei in Cron verwenden:

1) Pfad prüfen und Ausführbarkeit setzen:

```bash
which python3   # sollte /usr/bin/python3 o.ä. sein
chmod +x /pfad/zu/deinem/projekt/m3u_script.sh
```

2) Cron-Eintrag anlegen (z. B. alle 2 Stunden):

```cron
0 */2 * * * /pfad/zu/deinem/projekt/m3u_script.sh >> /var/log/m3u-manage.log 2>&1
```

Hinweise für Cron:
- Das Skript ermittelt sein Projektverzeichnis selbst (robust bei Cron).
- Es nutzt `venv/bin/python`; falls kein venv existiert, wird es automatisch erstellt und `requirements.txt` installiert.
- Ausgabe geht ins angegebene Log (`/var/log/m3u-manage.log`) und zusätzlich in `logs/*_m3u_log.log` im Projekt.

### .strm-Cleanup-Skript

Separates Skript zum Aufräumen leerer Ordner gemäß Schema:
- Filme: Löscht Filmordner, wenn darin keine `.strm`-Datei mehr existiert.
- Serien: Löscht Staffelordner ohne `.strm`; wenn keine Staffelordner mehr übrig, wird der Serienordner gelöscht.

Ausführen:

```bash
chmod +x cleanup_strm.sh
./cleanup_strm.sh
```

Cron-Beispiel (täglich um 03:15 Uhr):

```cron
15 3 * * * /pfad/zu/deinem/projekt/cleanup_strm.sh >> /var/log/m3u-cleanup.log 2>&1
```

Das Cleanup-Skript nutzt die gleichen Pfade aus `CONFIG.ini`/`.env` wie das M3U-Skript.

---

## Logging

- Logs werden automatisch im `logs`-Ordner erstellt mit Zeitstempel im Dateinamen, z.B.:

```
logs/2025-07-10_15-30-00_m3u_log.log
```

- Es werden maximal 10 Logdateien behalten, ältere werden gelöscht.

Zusätzlich werden Offline-Einträge in `tmp/offline.json` mit Grund gespeichert (z. B. `GET status 404`, `GET html-or-empty`).

---

## Performance & Download-Prüfung

- URL-Checks nutzen eine gemeinsame HTTP-Session mit Connection-Pooling und Retries.
- Vor dem Erstellen von `.strm`-Dateien wird per Minimal-Download verifiziert, dass echte Mediabytes geliefert werden (keine HTML-Fehlerseite).
- Parallele Prüfungen: Standardmäßig 30 Threads. Für sehr viele URLs oder hohe Latenz können 32–64 sinnvoll sein; bei strengen Rate-Limits eher 12–20.

---

## Telegram Bot (tg_bot)

- Zweck: Prüft neue Filme/Serien/Episoden seit dem letzten Lauf und sendet eine Telegram-Nachricht.
- Kein Zeitfenster: Es wird immer gegen den letzten vollständigen Snapshot verglichen.
- Erster Start: Erstellt nur den Snapshot, sendet keine Nachrichten.
- Dry-Run: Falls Telegram-Config fehlt, wird die Nachricht als Vorschau im Terminal ausgegeben (kein Versand).

### Konfiguration

- `.env` in der Projektwurzel oder `CONFIG.ini` verwenden.

Beispiel (`CONFIG.ini`):

```ini
[JELLYFIN_API]
jellyfin_url = https://dein-jellyfin
jellyfin_api_key = <API_KEY>

[TG_BOT]
tg_bot_token = <BOT_TOKEN>
tg_chat_id = <CHAT_ID>
```

Hinweis: Wenn `tg_bot_token` oder `tg_chat_id` fehlen, läuft der Bot im Dry-Run und zeigt die Nachricht im Terminal.

### Ausführen

```bash
cd tg_bot
chmod +x tg_bot_script.sh
./tg_bot_script.sh
```

- Das Script ermittelt den Projektpfad automatisch und nutzt `venv/bin/python`, ansonsten `python3`.
- Alternativ aus der Projektwurzel: `python -m tg_bot.main_tg`.

### Snapshot & Vergleich

- Snapshot-Datei: `tg_bot/tmp/jellyfin_snapshot.json`
- Bei jedem Lauf werden alle Jellyfin-Items (Filme, Serien, Episoden) geladen und mit dem Snapshot verglichen.
- Resultat: Nur neue Filme/Serien werden gemeldet. Serien werden nicht als „neu“ gemeldet, wenn nur neue Staffeln/Episoden hinzugekommen sind; neue Episoden werden gruppiert gemeldet (z. B. `S02, E01–E03`).

### Offline-Unterdrückung (aus M3U-Lauf)

- Der Bot liest optional `tmp/offline.json` aus der Projektwurzel.
- Titel, die dort als „offline“ stehen, werden NICHT als neu in Telegram gemeldet (sie existierten bereits, sind aber aktuell inaktiv/offline).
- Die Offline-Liste selbst wird NICHT gepostet.

### Ausgabe/Logging (tg_bot)

- Konsole: Alle Schritte und ggf. Nachrichten-Vorschau.
- Logdateien: `tg_bot/logs/*_tg_bot_log.log` (max. 10 Dateien; Rotation automatisch).


## Cleaner: Duplikate & Identifizierung

- Scannt Jellyfin und erkennt Duplikate zwischen M3U-Inhalten und regulären Inhalten.
- Löscht nur die M3U-Seite des Duplikats:
  - Filme: löscht `path_movie/<Filmordner>` und schreibt den Ordnernamen in die Blockliste.
  - Serien: löscht nur doppelte Staffeln unter `path_serien/<Serie>/Staffel XX` und schreibt alle Episoden-Namen der gelöschten Staffel in die Blockliste.
- Führt einen CAM-Scan durch (nur Log): listet Filme/Serien mit `(CAM)`, `[CAM]` oder `HDCAM` im Namen.
- Identifiziert Inhalte ohne Titelbild automatisch über die Jellyfin-API:
  - Verwendet als Suchbegriff den Titel bis zur ersten Klammer (ohne `(DE)`/`(Jahr)`) und – falls vorhanden – das Jahr aus der nächsten Klammer.
  - Probiert bei mehreren Treffern mit passendem Jahr nacheinander alle aus, bis ein Eintrag ein Titelbild liefert.
  - Nach jedem Apply wird ein FullRefresh (Metadaten/Bilder) ausgelöst und auf ein Primary-Bild geprüft.

### Konfiguration (CONFIG.ini)

Ergänze/prüfe folgende Keys im Abschnitt `[PATH]`:

```ini
[PATH]
# Hauptpfad
main_path=/pfad/zum/projekt

# Dateisystem-Pfade mit .strm-Ordnern (M3U-Ausgabe)
path_movie=Filme
path_serien=Serien

# Jellyfin-Basisordner, wie sie in den Jellyfin-"Path"-Feldern erscheinen (M3U-Seite)
# Falls nicht gesetzt, werden die Werte aus path_movie/path_serien verwendet.
path_m3u_movie=m3u_Filme
path_m3u_serien=m3u_Serien

# Blockliste (Datei im main_path)
path_blockliste=M3U_Blocklist.txt

[JELLYFIN_API]
jellyfin_url=https://your-jellyfin
jellyfin_api_key=... # API-Key mit Rechten für Metadata Apply/Refresh
```

### Nutzung (Cleaner)

```bash
chmod +x cleaner.sh
./cleaner.sh
```

`cleaner.sh` verwendet das bestehende `venv` aus dem Projekt. Der Cleaner führt in dieser Reihenfolge aus:
1. CAM-Scan (nur Log; keine Änderungen)
2. Duplikat-Bereinigung (M3U-Seite entfernen, Blockliste pflegen)
3. Identifizierung fehlender Titelbilder (RemoteSearch + Apply + Refresh, mit Verifikation)

### Logging (Cleaner)

- CAM-Scan: `Starte CAM-Scan …`, `CAM-Scan: X Einträge gefunden`, Liste der Treffer.
- Duplikate: `Duplikat (Film/Serie/Staffel) erkannt …`, danach Lösch- und Blocklisten-Einträge.
- Identify (ohne Titelbild):
  - `Identify: Movie/Series 'Basis' (Jahr) -> N Treffer`
  - `Versuche Treffer i/N: 'Name (Jahr)'`, `Apply OK – löse Refresh aus …`
  - `Primary-Bild gefunden – Identify abgeschlossen.` oder `Noch kein Primary-Bild – versuche nächsten Treffer …`
  - Zusammenfassung: `angepasst=…, nicht angepasst=…` und Liste der weiterhin ohne Bild.

---
