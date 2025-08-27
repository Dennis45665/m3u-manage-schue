# M3U zu .strm Files

Dieses Skript verarbeitet eine M3U-Datei, die Streams, Filme und Serien enthält. Aus dieser Datei werden für jeden Eintrag separate `.strm`-Dateien erzeugt.

---

## Was macht das Skript?

- Liest eine M3U-Datei mit Einträgen für Filme, Serien und andere Streams.
- Für jeden Eintrag wird ein Verzeichnis mit einem sicheren Namen erstellt.
- In diesem Verzeichnis wird eine `.strm`-Datei mit dem entsprechenden Stream-URL abgelegt.
- Bestehende `.strm`-Dateien werden nur aktualisiert, wenn sich der Stream-URL ändert.

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

---

## Logging

- Logs werden automatisch im `logs`-Ordner erstellt mit Zeitstempel im Dateinamen, z.B.:

```
logs/2025-07-10_15-30-00_m3u_log.log
```

- Es werden maximal 10 Logdateien behalten, ältere werden gelöscht.

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
