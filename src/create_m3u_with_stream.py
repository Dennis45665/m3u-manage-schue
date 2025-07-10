import os
from logger import logger

def create_m3u_with_stream(filename):
    logger.info("Erstelle m3u mit NUR Streams..")
    new_filename = f"streams_{filename}"

    tmp_dir = os.path.join(os.path.dirname(__file__), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    input_file = os.path.join(tmp_dir, filename)
    output_file = os.path.join(tmp_dir, new_filename)

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    filtered_lines = ['#EXTM3U\n']
    i = 1  # Start nach Header

    while i < len(lines) - 1:
        line_info = lines[i].strip()
        line_url = lines[i + 1].strip()

        # Nur behalten, wenn die URL nicht auf .mp4 || .mkv || .avi || .ts || .mpg  endet
        if not line_url.lower().endswith(('.mp4', '.mkv', '.avi', '.ts', '.mpg')):
            filtered_lines.append(line_info + '\n')
            filtered_lines.append(line_url + '\n')

        i += 2  # zum nächsten Paar

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(filtered_lines)

    logger.info("m3u mit nur Streams erstellt...")
    return new_filename