import os
from logger import logger
from pathlib import Path

def create_separate_m3u_files_movies_series(filename):
    logger.info("Erstelle m3u NUR mit Movies & Serien")
    logger.info("Starte CAM-Scan während der Aufteilung …")

    tmp_dir = Path.cwd() / "tmp"
    os.makedirs(tmp_dir, exist_ok=True)

    input_file = os.path.join(tmp_dir, filename)
    movies_filename = f"movies_{filename}"
    series_filename = f"series_{filename}"
    movies_file = os.path.join(tmp_dir, movies_filename)
    series_file = os.path.join(tmp_dir, series_filename)

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    video_extensions = ('.mp4', '.mkv', '.avi', '.ts', '.mpg')
    movies_lines = ['#EXTM3U\n']
    series_lines = ['#EXTM3U\n']
    cam_titles = []

    i = 1  # skip header

    while i < len(lines) - 1:
        line_info = lines[i].strip()
        line_url = lines[i + 1].strip()

        is_de = '(DE)' in line_info or '[DE]' in line_info
        is_cam = '(CAM)' in line_info
        has_video_ext = line_url.lower().endswith(video_extensions)

        # CAM sammeln (für Logging/Blockliste), aber nicht in Output übernehmen
        if is_de and has_video_ext and is_cam:
            # Title aus EXTINF extrahieren
            title = line_info.replace("#EXTINF:-1,", "").strip() if line_info.startswith("#EXTINF:-1,") else line_info
            cam_titles.append(title)

        if is_de and has_video_ext and not is_cam:
            if '/movie/' in line_url:
                movies_lines.append(line_info + '\n')
                movies_lines.append(line_url + '\n')
            elif '/series/' in line_url:
                series_lines.append(line_info + '\n')
                series_lines.append(line_url + '\n')

        i += 2

    with open(movies_file, 'w', encoding='utf-8') as f:
        f.writelines(movies_lines)

    with open(series_file, 'w', encoding='utf-8') as f:
        f.writelines(series_lines)

    if cam_titles:
        logger.info(f"CAM-Scan: {len(cam_titles)} Einträge gefunden.")
    else:
        logger.info("CAM-Scan: Keine CAM-Einträge gefunden.")

    logger.info(f"Filme gespeichert...")
    logger.info(f"Serien gespeichert...")
    return movies_filename, series_filename, cam_titles
