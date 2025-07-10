import os
from logger import logger

def create_separate_m3u_files_movies_series(filename):
    logger.info("Erstelle m3u NUR mit Movies & Serien")

    tmp_dir = os.path.join(os.path.dirname(__file__), "tmp")
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

    i = 1  # skip header

    while i < len(lines) - 1:
        line_info = lines[i].strip()
        line_url = lines[i + 1].strip()

        is_de = '(DE)' in line_info or '[DE]' in line_info
        has_video_ext = line_url.lower().endswith(video_extensions)

        if is_de and has_video_ext:
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

    logger.info(f"Filme gespeichert...")
    logger.info(f"Serien gespeichert...")
    return movies_filename, series_filename