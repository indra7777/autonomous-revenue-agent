from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


USER_AGENT = "AutonomousRevenueAgent/0.1 (+https://github.com/)"


@dataclass(frozen=True)
class HttpResult:
    url: str
    ok: bool
    body: str
    status: int | None = None
    error: str | None = None

    def json(self) -> object:
        return json.loads(self.body)


def fetch_text(url: str, timeout: float = 12) -> HttpResult:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/rss+xml, application/xml, text/xml, text/html;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
            return HttpResult(url=url, ok=True, body=body, status=response.status)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return HttpResult(url=url, ok=False, body=body, status=exc.code, error=str(exc))
    except Exception as exc:  # Network sources are best-effort.
        return HttpResult(url=url, ok=False, body="", error=str(exc))
