import re
import threading
import requests
from requests.adapters import HTTPAdapter, Retry
from logger import logger


"""
Schnelle, robuste Erkennung, ob eine URL wahrscheinlich eine Datei (Download) ist.

Optimierungen:
- Schnelle Negativ-Heuristik ohne Netzwerk (.m3u8/Manifest ausschließen)
- Globaler Requests-Session-Pool (Connection-Reuse, höherer pool_maxsize)
- Leicht reduzierte Timeouts für flottere Fehlpfade
- Thread-sicheres In-Memory-Caching über Aufrufe hinweg
Wichtig: Keine vorschnellen True-Ergebnisse nur anhand von Dateiendungen; es wird
mindestens ein minimaler Netzwerkabruf validiert, um inaktive Links zu erkennen.
"""

# Schnelle Heuristiken
_STREAMING_HINT = re.compile(r"(\.m3u8(?:\?|#|$)|manifest|/hls/|/dash/|/m3u8/)", re.IGNORECASE)

# Einfaches, threadsicheres Cache pro Prozess
_cache_lock = threading.Lock()
_download_check_cache: dict[str, bool] = {}
_download_check_cache_reason: dict[str, tuple[bool, str]] = {}

# Geteilte Session mit größerem Connection-Pool
_retries = Retry(
    total=2,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    raise_on_status=False,
)
_http_adapter = HTTPAdapter(max_retries=_retries, pool_connections=50, pool_maxsize=50)
_sess = requests.Session()
_sess.mount("http://", _http_adapter)
_sess.mount("https://", _http_adapter)


def _chunk_seems_html(first_bytes: bytes) -> bool:
    if not first_bytes:
        return False
    sample = first_bytes[:512].lower()
    return b"<html" in sample or sample.strip().startswith(b"<!doctype")


def is_url_downloadable_with_reason(url: str, timeout_head: float = 3.0, timeout_get: float = 5.0) -> tuple[bool, str]:
    """
    Prüft, ob hinter der URL ein "downloadbarer" Inhalt steckt.

    Heuristiken (vereinfacht aus Diagnose-Skript):
    - Content-Disposition enthält "attachment"
    - Content-Type enthält "application", "octet-stream" oder beginnt mit "video/"
    - Content-Length ist numerisch und > 0

    Ablauf:
    1) HEAD mit Redirect-Follow; ok + Heuristik => True
    2) Fallback GET mit Range 0-0; 200/206 + Heuristik => True
    3) Minimal-GET; ok + Heuristik => True

    :param url: Zu prüfende URL
    :param timeout_head: Timeout für HEAD
    :param timeout_get: Timeout für GET
    :return: True, wenn es nach herunterladbarer Datei aussieht, sonst False
    """
    # 0) Cache-Hit?
    with _cache_lock:
        cached_r = _download_check_cache_reason.get(url)
    if cached_r is not None:
        return cached_r

    # 0.5) Sofortige Heuristiken ohne Netzwerk
    #    a) Offensichtliche Streaming-Links schnell ausschließen
    if _STREAMING_HINT.search(url):
        with _cache_lock:
            _download_check_cache[url] = False
            _download_check_cache_reason[url] = (False, "streaming-manifest")
        return False, "streaming-manifest"

    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Encoding": "identity",
    }

    def looks_like_file(resp: requests.Response) -> bool:
        ct = (resp.headers.get("Content-Type") or "").lower()
        cd = (resp.headers.get("Content-Disposition") or "").lower()
        cl = resp.headers.get("Content-Length")

        if "attachment" in cd:
            return True
        if ct.startswith("video/") or "application" in ct or "octet-stream" in ct:
            return True
        if cl and cl.isdigit() and int(cl) > 0:
            return True
        return False

    # 1) Versuch: HEAD
    try:
        r = _sess.head(url, headers=base_headers, allow_redirects=True, timeout=timeout_head)
        if r.ok and looks_like_file(r):
            # Bestätige noch mit minimalem GET, um inaktive Ziele auszuschließen
            try:
                g = _sess.get(url, headers=base_headers, allow_redirects=True, timeout=timeout_get, stream=True)
                if g.status_code in (200, 206):
                    try:
                        chunk = next(g.iter_content(chunk_size=2048))
                    except StopIteration:
                        chunk = b""
                    if chunk and not _chunk_seems_html(chunk):
                        with _cache_lock:
                            _download_check_cache[url] = True
                            _download_check_cache_reason[url] = (True, "HEAD+GET bytes")
                        return True, "HEAD+GET bytes"
            except requests.RequestException:
                pass
    except requests.RequestException:
        pass

    # 2) Fallback: GET mit Range 0-0
    try:
        headers = dict(base_headers)
        headers["Range"] = "bytes=0-0"
        r = _sess.get(url, headers=headers, allow_redirects=True, timeout=timeout_get, stream=True)
        if r.status_code in (200, 206) and looks_like_file(r):
            # minimal konsumieren, dann abbrechen
            try:
                chunk = next(r.iter_content(chunk_size=2048))
            except Exception:
                chunk = b""
            if chunk and not _chunk_seems_html(chunk):
                with _cache_lock:
                    _download_check_cache[url] = True
                    _download_check_cache_reason[url] = (True, "RANGE bytes")
                return True, "RANGE bytes"
    except requests.RequestException:
        pass

    # 3) Minimal-GET
    try:
        r = _sess.get(url, headers=base_headers, allow_redirects=True, timeout=timeout_get, stream=True)
        if r.ok:
            try:
                chunk = next(r.iter_content(chunk_size=4096))
            except Exception:
                chunk = b""
            if chunk and not _chunk_seems_html(chunk):
                with _cache_lock:
                    _download_check_cache[url] = True
                    _download_check_cache_reason[url] = (True, "GET bytes")
                return True, "GET bytes"
            else:
                with _cache_lock:
                    _download_check_cache[url] = False
                    _download_check_cache_reason[url] = (False, "GET html-or-empty")
                logger.info(f"Download-Check FAIL (GET html/empty): {url}")
                return False, "GET html-or-empty"
        else:
            with _cache_lock:
                _download_check_cache[url] = False
                _download_check_cache_reason[url] = (False, f"GET status {r.status_code}")
            logger.info(f"Download-Check FAIL (status {r.status_code}): {url}")
            return False, f"GET status {r.status_code}"
    except requests.RequestException as e:
        with _cache_lock:
            _download_check_cache[url] = False
            _download_check_cache_reason[url] = (False, f"exception: {type(e).__name__}")
        logger.info(f"Download-Check FAIL (exception {type(e).__name__}): {url}")
        return False, f"exception: {type(e).__name__}"

    with _cache_lock:
        _download_check_cache[url] = False
        _download_check_cache_reason[url] = (False, "no-indicator")
    # Kurzer Hinweis im Log, um inaktive Links besser nachzuvollziehen
    logger.info(f"Download-Check FAIL: {url}")
    return False, "no-indicator"


def is_url_downloadable(url: str, timeout_head: float = 3.0, timeout_get: float = 5.0) -> bool:
    ok, _ = is_url_downloadable_with_reason(url, timeout_head=timeout_head, timeout_get=timeout_get)
    return ok
