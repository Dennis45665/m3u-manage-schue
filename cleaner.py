import configparser
import json
import os
import re
import time
import requests
import shutil
import logging
import sys
from pathlib import Path
from datetime import datetime

from functions import sanitize_filename


def setup_cleaner_logger():
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    def cleanup_logs(max_files=10):
        _logger = logging.getLogger("cleaner_logger")
        logs = sorted(log_dir.glob("*_cleaner_log.log"), key=lambda f: f.stat().st_mtime)
        if len(logs) > max_files:
            to_delete = logs[:-max_files]
            for file in to_delete:
                _logger.info(f"Lösche alte Logdatei: {file.name}")
                file.unlink()

    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"{now_str}_cleaner_log.log"

    logger_ = logging.getLogger("cleaner_logger")
    logger_.setLevel(logging.INFO)

    if not logger_.handlers:
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)

        logger_.addHandler(file_handler)
        logger_.addHandler(stream_handler)

    cleanup_logs()
    return logger_


logger = setup_cleaner_logger()


def load_config():
    """
    Lädt Konfiguration und unterstützt zwei Varianten:
    1) getrennter regulärer und M3U-Pfad über Keys:
       PATH.path_movie / PATH.path_serien          -> regulär
       PATH.path_m3u_movie / PATH.path_m3u_serien  -> M3U
    2) nur M3U-Pfade vorhanden (wie im Repo):
       PATH.path_movie / PATH.path_serien -> M3U
       Optional: PATH.path_regular_movie / PATH.path_regular_serien für regulär
    """
    config = configparser.ConfigParser()
    config.read('CONFIG.ini')

    jellyfin_url = config['JELLYFIN_API']['jellyfin_url']
    jellyfin_api_key = config['JELLYFIN_API']['jellyfin_api_key']
    main_path = config['PATH']['main_path']

    def join_opt(section, key):
        if key in config[section]:
            return os.path.join(main_path, config[section][key])
        return None

    # Mögliche Pfade laden
    fs_m3u_movie = join_opt('PATH', 'path_movie')           # Dateisystem: M3U-Filme (.strm)
    fs_m3u_series = join_opt('PATH', 'path_serien')         # Dateisystem: M3U-Serien (.strm)
    jf_m3u_movie = join_opt('PATH', 'path_m3u_movie')       # Jellyfin zeigt diese Basen in Path
    jf_m3u_series = join_opt('PATH', 'path_m3u_serien')
    blockliste_path = join_opt('PATH', 'path_blockliste')

    # Fallback: Wenn keine Jellyfin-M3U-Basen definiert sind, nehmen wir an,
    # dass Jellyfin dieselben Basen wie das Dateisystem nutzt.
    if jf_m3u_movie is None:
        jf_m3u_movie = fs_m3u_movie
    if jf_m3u_series is None:
        jf_m3u_series = fs_m3u_series

    logger.info("Konfiguration geladen:")
    logger.info(f"  Jellyfin URL: {jellyfin_url}")
    logger.info(f"  Jellyfin M3U Movie Base: {jf_m3u_movie}")
    logger.info(f"  Jellyfin M3U Serien Base: {jf_m3u_series}")
    logger.info(f"  FS M3U Movie Path: {fs_m3u_movie}")
    logger.info(f"  FS M3U Serien Path: {fs_m3u_series}")
    logger.info(f"  Blockliste Path: {blockliste_path}")

    return {
        'jellyfin_url': jellyfin_url,
        'jellyfin_api_key': jellyfin_api_key,
        'jf_m3u_movie': jf_m3u_movie,
        'jf_m3u_series': jf_m3u_series,
        'fs_m3u_movie': fs_m3u_movie,
        'fs_m3u_series': fs_m3u_series,
        'blocklist': blockliste_path,
    }


def get_jellyfin_media(jellyfin_url, jellyfin_api_key, item_types, fields):
    logger.info(f"Rufe Jellyfin-Medien ab: Types='{item_types}', Fields='{fields}'")
    headers = {'X-Emby-Token': jellyfin_api_key}
    url = f'{jellyfin_url}/emby/Items'
    params = {
        'Recursive': 'true',
        'IncludeItemTypes': item_types,
        'Fields': fields,
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        items = response.json().get('Items', [])
        logger.info(f"{len(items)} Medien von Jellyfin erhalten.")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen der Jellyfin-Daten: {e}")
        return []


def path_in_base(p: str, base: str) -> bool:
    if not p or not base:
        return False
    try:
        # Normalisieren und case-insensitive unter Windows
        p_norm = os.path.normcase(os.path.normpath(p))
        b_norm = os.path.normcase(os.path.normpath(base))
        # Ensure base has trailing separator logic by comparing commonpath
        common = os.path.commonpath([p_norm, b_norm])
        return common == b_norm
    except Exception:
        return False


def add_to_blocklist(title: str, blocklist_path: str):
    if not blocklist_path:
        logger.warning("Kein Blocklisten-Pfad konfiguriert – überspringe Blocklisteneintrag.")
        return
    safe = sanitize_filename(title)
    os.makedirs(os.path.dirname(blocklist_path), exist_ok=True)
    try:
        existing = set()
        if os.path.exists(blocklist_path):
            with open(blocklist_path, 'r', encoding='utf-8') as f:
                existing = {line.strip() for line in f if line.strip()}
        if safe not in existing:
            with open(blocklist_path, 'a', encoding='utf-8') as f:
                if os.path.getsize(blocklist_path) > 0:
                    f.write("\n")
                f.write(safe)
            logger.info(f"Zur Blockliste hinzugefügt: {safe}")
        else:
            logger.info(f"Bereits in Blockliste: {safe}")
    except Exception as e:
        logger.error(f"Fehler beim Schreiben in Blockliste: {e}")


def delete_tree(path: Path):
    try:
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Gelöscht: {path}")
        else:
            logger.info(f"Nicht gefunden (übersprungen): {path}")
    except Exception as e:
        logger.error(f"Fehler beim Löschen von {path}: {e}")


def dedupe_movies_series(cfg: dict):
    """
    Findet Duplikate anhand des Jellyfin-Namens und löscht die M3U-Variante,
    wenn es eine reguläre Kopie gibt. Fügt den M3U-Ordnernamen zur Blockliste hinzu.
    """
    jf_url = cfg['jellyfin_url']
    jf_key = cfg['jellyfin_api_key']
    jf_m3u_movie = cfg['jf_m3u_movie']
    jf_m3u_series = cfg['jf_m3u_series']
    fs_m3u_movie = cfg['fs_m3u_movie']
    fs_m3u_series = cfg['fs_m3u_series']
    blocklist = cfg['blocklist']

    if not (jf_m3u_movie and jf_m3u_series and fs_m3u_movie and fs_m3u_series):
        logger.warning("M3U-Pfade nicht vollständig konfiguriert – Abbruch.")
        return

    # Filme, Serien (optional) und Episoden abrufen
    movies = get_jellyfin_media(jf_url, jf_key, 'Movie', 'Path,Name')
    series = get_jellyfin_media(jf_url, jf_key, 'Series', 'Path,Name')
    episodes = get_jellyfin_media(jf_url, jf_key, 'Episode', 'Path,SeriesName,ParentIndexNumber')

    # Filme: nach Name aggregieren und klassifizieren
    movie_by_name = {}
    for m in movies:
        name = m.get('Name')
        path = m.get('Path') or ''
        if not name:
            continue
        entry = movie_by_name.setdefault(name, {'m3u': [], 'regular': [], 'm3u_folder_names': set()})
        if path_in_base(path, jf_m3u_movie):
            entry['m3u'].append(path)
            # Ordnername relativ zu Jellyfin-M3U-Basis ableiten (robuster)
            try:
                rel = os.path.relpath(os.path.normpath(path), os.path.normpath(jf_m3u_movie))
                folder_name = rel.split(os.sep)[0]
            except Exception:
                base = Path(path)
                folder_name = base.parent.name if base.suffix.lower() == '.strm' else base.name
            if folder_name:
                entry['m3u_folder_names'].add(folder_name)
        else:
            # Alles außerhalb der M3U-Pfade gilt als regulär
            entry['regular'].append(path)

    # Serien: nach Name aggregieren
    # Serien- und Staffeldubletten über Episoden bestimmen
    # Map: (SeriesName, SeasonNumber) -> {'m3u': bool, 'regular': bool, 'series_folders': set(['SeriesFolderName'])}
    series_season_map = {}
    for ep in episodes:
        series_name = ep.get('SeriesName')
        path = ep.get('Path') or ''
        season_num = ep.get('ParentIndexNumber')
        if series_name is None or season_num is None:
            continue
        key = (series_name, int(season_num))
        entry = series_season_map.setdefault(key, {'m3u': False, 'regular': False, 'series_folders': set()})
        if path_in_base(path, jf_m3u_series):
            entry['m3u'] = True
            # Serienordner aus Relativpfad zur Jellyfin-M3U-Serie ableiten
            try:
                rel = os.path.relpath(os.path.normpath(path), os.path.normpath(jf_m3u_series))
                parts = rel.split(os.sep)
                if parts:
                    entry['series_folders'].add(parts[0])
            except Exception:
                # Fallback
                entry['series_folders'].add(Path(path).parents[2].name if len(Path(path).parents) >= 2 else Path(path).parent.name)
        else:
            entry['regular'] = True

    # Duplikate bestimmen und behandeln
    # Filme
    for name, kinds in movie_by_name.items():
        if kinds['m3u'] and kinds['regular']:
            # Lösche alle passenden M3U-Filmordner im Dateisystem-Pfad und blockliste deren Ordnernamen
            for folder_name in kinds.get('m3u_folder_names', {sanitize_filename(name)}):
                target_dir = Path(fs_m3u_movie) / folder_name
                logger.info(f"Duplikat (Film) erkannt: {name} -> lösche M3U {target_dir}")
                add_to_blocklist(folder_name, blocklist)
                delete_tree(target_dir)

    # Serien: nur Staffeln löschen, die doppelt sind
    for (series_name, season_num), flags in series_season_map.items():
        if flags['m3u'] and flags['regular']:
            season_dir = f"Staffel {int(season_num):02d}"
            # Für jede gefundene M3U-Serienordner-Variante löschen
            folders = flags['series_folders'] if flags['series_folders'] else {sanitize_filename(series_name)}
            for series_folder in folders:
                target_dir = Path(fs_m3u_series) / series_folder / season_dir
                logger.info(f"Duplikat (Serie/Staffel) erkannt: {series_name} S{season_num:02d} -> lösche {target_dir}")

                # Blockliste: jede Episode in dieser Staffel
                try:
                    if target_dir.exists():
                        episode_stems = [p.stem for p in target_dir.glob('*.strm')]
                        logger.info(f"Füge {len(episode_stems)} Episoden zur Blockliste hinzu: Serie {series_folder} | {season_dir}")
                        for ep_stem in episode_stems:
                            add_to_blocklist(ep_stem, blocklist)
                    else:
                        logger.info(f"M3U-Staffelordner nicht vorhanden: {target_dir}")
                except Exception as e:
                    logger.error(f"Fehler beim Erfassen der Episoden für {target_dir}: {e}")

                # Staffelordner löschen; wenn Serie danach leere Ordner hat, bereinigen
                delete_tree(target_dir)
                series_path = Path(fs_m3u_series) / series_folder
                try:
                    if series_path.exists() and not any(series_path.rglob('*.strm')):
                        # keine Episoden mehr -> leere Staffeln und Serie bereinigen
                        for p in sorted(series_path.glob('**/*'), reverse=True):
                            if p.is_dir() and not any(p.iterdir()):
                                p.rmdir()
                        if not any(series_path.iterdir()):
                            series_path.rmdir()
                except Exception as e:
                    logger.error(f"Fehler beim Aufräumen nach Löschen von {target_dir}: {e}")


def _jellyfin_get_items(jellyfin_url: str, api_key: str, include_types: str):
    """
    Ruft eine Liste von Jellyfin-Items ab.
    - include_types: z. B. "Movie", "Series", "Episode" (kommagetrennt möglich)
    - Liefert Items mit grundlegenden Feldern (Path, PrimaryImageTag) zurück.
    """
    headers = {"X-Emby-Token": api_key}
    params = {
        "Recursive": "true",
        "IncludeItemTypes": include_types,
        "Fields": "Path,PrimaryImageTag"
    }
    try:
        r = requests.get(f"{jellyfin_url}/emby/Items", headers=headers, params=params)
        r.raise_for_status()
        return r.json().get("Items", [])
    except Exception as e:
        logger.error(f"Fehler beim Abruf Items ({include_types}): {e}")
        return []


def _has_primary_image(item: dict) -> bool:
    """Gibt True zurück, wenn das Item ein Primary-Image besitzt (Tag vorhanden)."""
    if item.get("PrimaryImageTag"):
        return True
    # Fallback: manche Antworten haben ImageTags-Objekt
    tags = item.get("ImageTags") or {}
    return bool(tags.get("Primary"))


def _parse_base_and_year(name: str):
    """
    Zerlegt einen Namen in (basis_titel, jahr|None).
    - basis_titel: alles vor der ersten Klammer
    - jahr: vierstellige Zahl aus einer der folgenden Klammern, bevorzugt die zweite nach (DE)
    """
    if not name:
        return "", None
    base = name.split("(", 1)[0].strip()
    # Alle Klammerinhalte erfassen
    parts = re.findall(r"\(([^)]*)\)", name)
    # 'DE' entfernen
    parts = [p for p in parts if p.strip().upper() != 'DE']
    year = None
    for p in parts:
        m = re.search(r"\b(19\d{2}|20\d{2})\b", p)
        if m:
            year = int(m.group(1))
            break
    return base, year


def _remote_search_and_apply(jellyfin_url: str, api_key: str, item_id: str, item_type: str, search_name: str, year: int | None = None) -> bool:
    """
    Führt eine Remote-Suche (Movie/Series) mit Name (+ optional Jahr) aus und
    versucht nacheinander passende Treffer anzuwenden (Apply). Nach jedem Apply
    wird ein FullRefresh ausgelöst und geprüft, ob ein Primary-Bild gesetzt wurde.
    - Gibt True zurück, sobald ein Treffer erfolgreich ein Primary-Bild liefert, sonst False.
    """
    headers = {"X-Emby-Token": api_key, "Content-Type": "application/json"}
    # Wähle Endpoint abhängig vom Typ
    if item_type == "Movie":
        url_search = f"{jellyfin_url}/emby/Items/RemoteSearch/Movie"
        si = {"Name": search_name}
        if year:
            si["Year"] = year
        payload = {"SearchInfo": si, "ItemId": item_id}
    elif item_type == "Series":
        url_search = f"{jellyfin_url}/emby/Items/RemoteSearch/Series"
        si = {"Name": search_name}
        if year:
            si["Year"] = year
        payload = {"SearchInfo": si, "ItemId": item_id}
    else:
        logger.info(f"RemoteSearch für Typ {item_type} nicht unterstützt")
        return False

    try:
        rs = requests.post(url_search, headers=headers, data=json.dumps(payload))
        rs.raise_for_status()
        results = rs.json() or []
        logger.info(f"Identify: {item_type} '{search_name}'{f' ({year})' if year else ''} -> {len(results)} Treffer")
        if not results:
            return False
        # Kandidatenliste bilden: bevorzugt mit Jahr, sonst alle
        def _prod_year(r):
            return r.get('ProductionYear') or r.get('Year')
        candidates = [r for r in results if year and _prod_year(r) == year] if year else []
        if not candidates:
            candidates = list(results)
        total = len(candidates)
        for idx, chosen in enumerate(candidates, start=1):
            cand_name = chosen.get('Name') or chosen.get('OriginalTitle') or 'Unbekannt'
            cand_year = _prod_year(chosen)
            logger.info(f"Versuche Treffer {idx}/{total}: '{cand_name}'{f' ({cand_year})' if cand_year else ''}")
            apply_url = f"{jellyfin_url}/emby/Items/RemoteSearch/Apply/{item_id}?replaceAllImages=true"
            ra = requests.post(apply_url, headers=headers, data=json.dumps(chosen))
            if ra.status_code != 204:
                logger.error(f"Apply fehlgeschlagen ({ra.status_code}): {ra.text}")
                continue
            logger.info("Apply OK – löse Refresh aus und prüfe auf Primary-Bild …")
            try:
                refresh_url = (
                    f"{jellyfin_url}/emby/Items/{item_id}/Refresh?"
                    f"metadataRefreshMode=FullRefresh&imageRefreshMode=FullRefresh&"
                    f"replaceAllMetadata=true&replaceAllImages=true"
                )
                rr = requests.post(refresh_url, headers={"X-Emby-Token": api_key})
                if rr.status_code != 204:
                    logger.warning(f"Refresh nicht bestätigt ({rr.status_code}): {rr.text}")
            except Exception as e:
                logger.warning(f"Fehler beim Auslösen Refresh: {e}")
            # Verifikation
            ok = False
            for _ in range(5):
                time.sleep(3)
                imgs = _get_item_images(jellyfin_url, api_key, item_id)
                if any(img.get('ImageType') == 'Primary' for img in imgs):
                    ok = True
                    break
            if ok:
                logger.info("Primary-Bild gefunden – Identify abgeschlossen.")
                return True
            else:
                logger.info("Noch kein Primary-Bild – versuche nächsten Treffer (falls vorhanden)…")
        logger.info("Kein Treffer konnte ein Primary-Bild liefern.")
        return False
    except Exception as e:
        logger.error(f"Fehler bei RemoteSearch/Apply: {e}")
        return False


def identify_missing_posters(cfg: dict):
    """
    Letzter Schritt im Cleaner: Findet Filme/Serien ohne Titelbild, leitet aus dem
    Namen einen Basis-Titel und ggf. das Jahr ab und identifiziert diese via
    RemoteSearch+Apply. Loggt detaillierten Verlauf und eine Zusammenfassung.
    """
    logger.info("Beginne Scan: Inhalte ohne Titelbild identifizieren …")
    jf_url = cfg['jellyfin_url']
    jf_key = cfg['jellyfin_api_key']

    items_movies = _jellyfin_get_items(jf_url, jf_key, "Movie")
    items_series = _jellyfin_get_items(jf_url, jf_key, "Series")

    missing_movies = [m for m in items_movies if not _has_primary_image(m)]
    missing_series = [s for s in items_series if not _has_primary_image(s)]

    logger.info(f"Ohne Titelbild: Filme={len(missing_movies)}, Serien={len(missing_series)}")

    adjusted = []
    failed = []

    # Filme identifizieren
    for m in missing_movies:
        name = m.get("Name") or ""
        item_id = m.get("Id")
        base, year = _parse_base_and_year(name)
        if not item_id or not base:
            continue
        logger.info(f"Identify (Movie): '{name}' -> Suche mit '{base}'{f' ({year})' if year else ''}")
        applied = _remote_search_and_apply(jf_url, jf_key, item_id, "Movie", base, year)
        if applied:
            logger.info(f"Angepasst (Movie): '{name}' -> '{base}'{f' ({year})' if year else ''}")
            adjusted.append(("Movie", name))
        else:
            logger.info(f"Nicht angepasst (Movie, weiterhin ohne Bild): '{name}'")
            failed.append(("Movie", name))

    # Serien identifizieren
    for s in missing_series:
        name = s.get("Name") or ""
        item_id = s.get("Id")
        base, year = _parse_base_and_year(name)
        if not item_id or not base:
            continue
        logger.info(f"Identify (Series): '{name}' -> Suche mit '{base}'{f' ({year})' if year else ''}")
        applied = _remote_search_and_apply(jf_url, jf_key, item_id, "Series", base, year)
        if applied:
            logger.info(f"Angepasst (Series): '{name}' -> '{base}'{f' ({year})' if year else ''}")
            adjusted.append(("Series", name))
        else:
            logger.info(f"Nicht angepasst (Series, weiterhin ohne Bild): '{name}'")
            failed.append(("Series", name))

    # Zusammenfassung
    logger.info(f"Identify-Zusammenfassung: angepasst={len(adjusted)}, nicht angepasst={len(failed)}")
    if failed:
        logger.info("Nicht identifizierte Inhalte (weiterhin ohne Bild):")
        for typ, nm in failed:
            logger.info(f"- {typ}: {nm}")
    else:
        logger.info("Alle Inhalte mit fehlendem Titelbild konnten identifiziert werden.")

    logger.info("Scan Titelbilder: fertig.")


def _get_item_images(jellyfin_url: str, api_key: str, item_id: str):
    """Liest die Image-Infos eines Items (zur Prüfung auf Primary-Bild)."""
    headers = {"X-Emby-Token": api_key}
    try:
        r = requests.get(f"{jellyfin_url}/emby/Items/{item_id}/Images", headers=headers)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Fehler beim Abruf von Item-Images ({item_id}): {e}")
        return []


def cam_scan_log(cfg: dict):
    """
    Reiner Informations-Scan: Listet alle Jellyfin-Filme/Serien mit CAM-Markern
    im Namen. Nimmt keine Änderungen vor – nur Logging.
    """
    logger.info("Starte CAM-Scan (nur Log, keine Änderungen)…")
    jf_url = cfg['jellyfin_url']
    jf_key = cfg['jellyfin_api_key']
    items_movies = _jellyfin_get_items(jf_url, jf_key, "Movie")
    items_series = _jellyfin_get_items(jf_url, jf_key, "Series")

    def is_cam(name: str) -> bool:
        if not name:
            return False
        n = name.upper()
        return '(CAM)' in n or '[CAM]' in n or 'HDCAM' in n

    cam_movies = [m for m in items_movies if is_cam(m.get('Name'))]
    cam_series = [s for s in items_series if is_cam(s.get('Name'))]

    total = len(cam_movies) + len(cam_series)
    if total == 0:
        logger.info("CAM-Scan: Keine CAM-Einträge gefunden.")
    else:
        logger.info(f"CAM-Scan: {total} Einträge gefunden.")
        if cam_movies:
            logger.info("CAM Movies:")
            for m in cam_movies:
                logger.info(f"- {m.get('Name')}")
        if cam_series:
            logger.info("CAM Series:")
            for s in cam_series:
                logger.info(f"- {s.get('Name')}")


def main():
    logger.info("=" * 60)
    logger.info("STARTE CLEANER")
    logger.info("=" * 60)
    cfg = load_config()

    # Hinweise
    if not cfg['blocklist']:
        logger.warning("Blocklisten-Pfad fehlt – Blocklisteneinträge werden übersprungen.")

    # CAM-Scan (nur Logs)
    cam_scan_log(cfg)

    dedupe_movies_series(cfg)
    # Letzter Schritt: fehlende Poster identifizieren
    identify_missing_posters(cfg)

    logger.info("=" * 60)
    logger.info("CLEANER BEENDET")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
