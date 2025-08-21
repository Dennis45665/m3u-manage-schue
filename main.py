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
    m3u_movies_filename, m3u_series_filename = create_separate_m3u_files_movies_series(m3u_base_filename)

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