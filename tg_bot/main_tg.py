from .logger import tg_logger, log_start, log_end
from .src.load_config import load_config
from .src.get_jellyfin_data import get_jellyfin_data
from .src.send_telegram_message import send_telegram_message
from .src.state import load_snapshot, save_snapshot, compute_new_items
from .src.filter_data import group_episodes_by_series_and_season
from pathlib import Path
import json

def main():
    """
    Hauptfunktion des Skripts.
    Lädt die Konfiguration, ruft Daten von Jellyfin ab, prüft auf neue Medien
    und sendet eine Benachrichtigung an Telegram, wenn neue Medien gefunden wurden.
    """
    log_start()
    tg_logger.info("Schritt 1/5: Lade Konfiguration…")
    jellyfin_url, jellyfin_api_key, tg_bot_token, tg_chat_id, hours_new_film_series = load_config()
    # Änderung: Zeitfenster wird nicht mehr genutzt – voller Abgleich.
    tg_logger.info("Hinweis: Zeitfenster wird ignoriert – vollständiger Vergleich zum letzten Lauf.")

    tg_logger.info("Schritt 2/5: Frage Jellyfin nach allen Inhalten…")
    current_data = get_jellyfin_data(jellyfin_url, jellyfin_api_key)

    if not current_data:
        tg_logger.info("Keine Daten von Jellyfin erhalten.")
        log_end()
        return

    tg_logger.info("Schritt 3/5: Lade vorherigen Snapshot…")
    prev_snapshot = load_snapshot()

    if prev_snapshot is None:
        tg_logger.info("Erster Start erkannt: Erstelle Snapshot und sende keine Nachrichten.")
        save_snapshot(current_data)
        tg_logger.info("Initialer Snapshot gespeichert.")
        log_end()
        return

    tg_logger.info("Schritt 4/5: Vergleiche Snapshots und ermittle neue Inhalte…")
    new_data = compute_new_items(prev_snapshot, current_data)

    # Änderung: Serien-Unterdrückung
    # Serien nicht als "neu" melden, wenn sie bereits in einem
    # vorherigen Snapshot existierten (auch wenn nur neue Staffeln/Folgen kamen).
    prev_series_ids = {s.get("Id") for s in (prev_snapshot.get("series", []) or []) if s.get("Id")}
    # Zusätzlich: Serien, die durch vorhandene Episoden im vorherigen Snapshot existierten
    prev_episode_series_ids = {e.get("SeriesId") for e in (prev_snapshot.get("episodes", []) or []) if e.get("SeriesId")}
    existing_series_ids = prev_series_ids.union(prev_episode_series_ids)

    if new_data.get("series"):
        filtered_series = [s for s in new_data["series"] if s.get("Id") not in existing_series_ids]
        dropped = len(new_data["series"]) - len(filtered_series)
        if dropped > 0:
            tg_logger.info(f"Unterdrücke {dropped} Serien, da bereits vorhanden (neue Staffeln/Folgen werden separat gemeldet).")
        new_data["series"] = filtered_series

    # Änderung: Episoden gruppieren für schönere Ausgabe (Sxx, Eyy–Ezz)
    if new_data.get("episodes"):
        new_data["episodes"] = group_episodes_by_series_and_season(new_data["episodes"])

    # Offline-Items aus m3u-Runner laden (tmp/offline.json im Projektroot)
    try:
        project_root = Path(__file__).resolve().parents[1]
        offline_path = project_root / "tmp" / "offline.json"
        if offline_path.exists():
            offline_items = json.loads(offline_path.read_text(encoding="utf-8"))
        else:
            offline_items = []
    except Exception:
        offline_items = []

    # Unterdrücke "neue" Titel, die in der Offline-Liste stehen
    import re
    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

    offline_movies = set()
    offline_series = set()
    for it in offline_items:
        kind = (it.get("kind") or "").lower()
        if kind == "movie":
            title = it.get("title") or it.get("name") or ""
            offline_movies.add(_norm(title))
        elif kind == "series":
            # Bevorzugt 'series_name' (neu); fallback: Titel ohne Sxx Exx
            sname = it.get("series_name") or it.get("title") or ""
            # Fallback-Strip Sxx Exx
            sname = re.sub(r"\sS\d+\sE\d+.*$", "", sname, flags=re.IGNORECASE).strip()
            offline_series.add(_norm(sname))

    if new_data.get("movies"):
        before = len(new_data["movies"])
        new_data["movies"] = [m for m in new_data["movies"] if _norm(m.get("Name", "")) not in offline_movies]
        dropped = before - len(new_data["movies"])
        if dropped:
            tg_logger.info(f"Unterdrücke {dropped} neue Filme, da in Offline-Liste.")

    if new_data.get("series"):
        before = len(new_data["series"])
        new_data["series"] = [s for s in new_data["series"] if _norm(s.get("Name", "")) not in offline_series]
        dropped = before - len(new_data["series"])
        if dropped:
            tg_logger.info(f"Unterdrücke {dropped} neue Serien, da in Offline-Liste.")

    if new_data.get("episodes"):
        before = len(new_data["episodes"])
        new_data["episodes"] = [e for e in new_data["episodes"] if _norm(e.get("SeriesName", "")) not in offline_series]
        dropped = before - len(new_data["episodes"])
        if dropped:
            tg_logger.info(f"Unterdrücke {dropped} neue Episoden, da zu Serien in Offline-Liste.")

    if any(new_data.get(k) for k in ("movies", "series", "episodes")):
        tg_logger.info("Neue Inhalte gefunden – bereite Versand vor…")
        dry_run = not (tg_bot_token and tg_chat_id)
        if dry_run:
            tg_logger.info("Telegram-Daten fehlen – führe DRY-RUN aus (zeige Nachrichten-Vorschau).")
        # Änderung: Nachrichten senden oder als Vorschau (Dry-Run) ausgeben
        send_telegram_message(
            tg_bot_token,
            tg_chat_id,
            new_data,
            current_data,
            dry_run=dry_run,
            save_sent_ids=False,
        )
    else:
        tg_logger.info("Keine neuen Inhalte seit dem letzten Lauf gefunden.")

    tg_logger.info("Schritt 5/5: Aktualisiere Snapshot…")
    save_snapshot(current_data)
    tg_logger.info("Snapshot aktualisiert. Ende.")

    log_end()



if __name__ == '__main__':
    main()
