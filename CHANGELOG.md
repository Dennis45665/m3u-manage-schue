# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.

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
