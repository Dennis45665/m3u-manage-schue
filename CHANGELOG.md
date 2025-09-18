# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.

## 0.3.0 — 2025-09-18

- Download-Erkennung: `src/url_check.py` grundlegend optimiert
  - Gemeinsame HTTP-Session mit Connection-Pooling und Retries
  - Schnellere Negativ-Heuristik für HLS/DASH/Manifeste
  - Validierung per Minimal-Download (Bytes prüfen, HTML-Fehlseiten ausschließen)
  - Thread-sicheres Caching der Ergebnisse (inkl. Grund)
  - Neue API: `is_url_downloadable_with_reason(url) -> (ok, reason)`
- Parallelität: URL-Checks in Filmen/Serien auf 30 Threads erhöht
- Offline-Tracking: Alle nicht downloadbaren Titel werden in `tmp/offline.json` gesammelt (Titel, URL, Typ, Grund)
- Hauptlauf: Am Ende wird `tmp/offline.json` geschrieben
- Telegram-Bot: Unterdrückt „neue“ Titel, die in `tmp/offline.json` stehen; Offline-Liste wird NICHT gepostet
- Serien-Offlines: Serienname wird sauber ohne Sxx/Eyy gespeichert für zuverlässigen Abgleich

## 0.2.0 — 2025-08-27

- tg_bot: Zeitfenster entfernt – vollständiger Vergleich gegen letzten Snapshot (kein `MinDateCreated`).
- tg_bot: Neuer Snapshot-Mechanismus (`tg_bot/tmp/jellyfin_snapshot.json`) via `src/state.py` (load/save/compute_new_items).
- tg_bot: Erster Start erzeugt nur Snapshot, versendet keine Nachrichten.
- tg_bot: Dry-Run, wenn Telegram-Daten fehlen – Nachrichten werden als Vorschau im Terminal angezeigt.
- tg_bot: Konsolen-Logging aktiviert (neben Datei-Logging) via eigenem Logger-Setup.
- tg_bot: Serien-Meldelogik verbessert – Serien werden nicht als „neu“ gemeldet, wenn nur neue Staffeln/Folgen hinzugefügt wurden (Nutzung von `SeriesId`).
- tg_bot: Jellyfin-Felder erweitert (`SeriesId`, `SeriesName`, `SeasonName`, `IndexNumber` etc.) für korrekte Gruppierung.
- tg_bot: Fehler-Logging verbessert (`logger.exception`) für vollständige Stacktraces bei API-Fehlern.
- tg_bot: `load_config` loggt keine Secrets mehr im Klartext, sondern ob TG-Daten vorhanden sind.
- tg_bot: Startscript `tg_bot_script.sh` ermittelt Projektpfad dynamisch und fällt auf `python3` zurück, falls `venv` fehlt.

## 0.1.0 — 2025-08-22

- Erste funktionale Version mit M3U-Verarbeitung, `.strm`-Erstellung und Grundfunktionen.
