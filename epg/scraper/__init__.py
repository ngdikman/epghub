"""
This folder contains all the scrapers.
Define update(channel: Channel, scraper_id: str | None = None, dt: date) is necessary.

Scrapers should use get_session() to make HTTP requests: it returns a
thread-local requests.Session with connection pooling and automatic
retries, so concurrent channel updates are both safe and fast.
"""

import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zoneinfo import ZoneInfo

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60"
}

tz_shanghai = ZoneInfo("Asia/Shanghai")
tz_hong_kong = ZoneInfo("Asia/Hong_Kong")

_thread_local = threading.local()


def get_session() -> requests.Session:
    """
    Return a thread-local requests.Session.

    The session carries the default browser-like headers, pools
    connections per host, and retries transient failures (connection
    errors and 429/5xx responses) with a small backoff.
    """
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(headers)
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _thread_local.session = session
    return session
