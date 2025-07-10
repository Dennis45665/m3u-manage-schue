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
chmod +x run_script.sh
./run_script.sh
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
