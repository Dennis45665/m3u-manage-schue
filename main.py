from src.create_m3u_with_stream import *
from src.create_m3u_with_movies import *
from src.save_new_stream_m3u import *
from src.save_new_movies_m3u import *
from src.save_new_series_m3u import *
from src.download_m3u import *
from logger import logger, log_start, log_end
from functions import *

def main ():
    # Start
    log_start()
    # Lade Config Daten
    m3u_url, path_movie, path_serien, path_m3u, blockliste_path = load_config()

    # Lade die Blockliste, um Filme und Serien auszuschließen.
    blocklist = load_blocklist(blockliste_path)

    # Download M3U File in /tmp von PythonPath
    # hier immer auskommentieren, damit ich nicht beim testen x mal downloade
    # m3u_base_filename = "tv_channels_nZtqNMXH.m3u"
    m3u_base_filename = download_m3u(m3u_url)

    # Erstelle neue m3u nur mit Streams in /tmp
    m3u_streams_filename = create_m3u_with_stream(m3u_base_filename)

    # Erstelle zwei neue m3u nur mit Filme & Serien mit (DE) in /tmp
    m3u_movies_filename, m3u_series_filename, cam_titles = create_separate_m3u_files_movies_series(m3u_base_filename)

    # CAM-Ergebnisse in Blockliste schreiben und loggen
    if cam_titles:
        logger.info("Beginne, CAM-Titel zur Blockliste hinzuzufügen …")
        # Stelle sicher, dass der Blocklisten-Ordner existiert
        os.makedirs(os.path.dirname(blockliste_path), exist_ok=True)

        # Lade bestehende Blockliste, um Duplikate zu vermeiden
        existing = set()
        if os.path.exists(blockliste_path):
            with open(blockliste_path, 'r', encoding='utf-8') as f:
                existing = {line.strip() for line in f if line.strip()}

        added_count = 0
        for original_title in cam_titles:
            safe_title = sanitize_filename(original_title)
            if safe_title not in existing:
                with open(blockliste_path, 'a', encoding='utf-8') as f:
                    if os.path.getsize(blockliste_path) > 0:
                        f.write('\n')
                    f.write(safe_title)
                existing.add(safe_title)
                added_count += 1
                logger.info(f"CAM: '{original_title}' -> Blockliste als '{safe_title}' hinzugefügt")
            else:
                logger.info(f"CAM: '{original_title}' bereits in Blockliste als '{safe_title}'")

        if added_count == 0:
            logger.info("CAM: Nichts Neues zur Blockliste hinzugefügt.")
        else:
            logger.info(f"CAM: {added_count} neue Einträge zur Blockliste hinzugefügt.")
    else:
        logger.info("CAM: Keine Einträge gefunden – nichts zur Blockliste hinzugefügt.")

    # check / erstelle m3u stream file
    save_new_stream_m3u(m3u_streams_filename, path_m3u)
    # check / erstelle movies .strm
    save_new_movies_m3u(m3u_movies_filename, path_movie, blocklist)
    # check / erstelle serien .strm
    save_new_series_m3u(m3u_series_filename, path_serien, blocklist)
    # Done
    log_end()



if __name__ == '__main__':
    main()
