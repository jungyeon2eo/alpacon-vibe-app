import time

import httpx

from db import get_conn


def check_url(check_id: int, url: str):
    """Background job: fetch the URL, record status + latency in Postgres."""
    start = time.monotonic()
    http_status = None
    status = "error"
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=10.0)
        http_status = resp.status_code
        status = "ok" if resp.status_code < 400 else "down"
    except Exception:
        status = "error"
    latency_ms = int((time.monotonic() - start) * 1000)

    with get_conn() as conn:
        conn.execute(
            "UPDATE checks SET status=%s, http_status=%s, latency_ms=%s, checked_at=now() WHERE id=%s",
            (status, http_status, latency_ms, check_id),
        )
