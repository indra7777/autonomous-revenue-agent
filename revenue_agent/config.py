from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    state_dir: Path
    report_dir: Path
    slack_webhook_url: str | None
    custom_feed_urls: tuple[str, ...]
    max_items_per_source: int
    timeout_seconds: float
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    email_from: str | None
    email_to: str | None
    github_token: str | None
    github_repository: str | None
    github_issue_notifications: bool

    @classmethod
    def from_env(cls) -> "Settings":
        custom_feeds = tuple(
            item.strip()
            for item in os.getenv("CUSTOM_FEED_URLS", "").split(",")
            if item.strip()
        )
        return cls(
            state_dir=Path(os.getenv("AGENT_STATE_DIR", "state")),
            report_dir=Path(os.getenv("AGENT_REPORT_DIR", "reports")),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL") or None,
            custom_feed_urls=custom_feeds,
            max_items_per_source=env_int("MAX_ITEMS_PER_SOURCE", 25),
            timeout_seconds=env_float("SOURCE_TIMEOUT_SECONDS", 12),
            smtp_host=os.getenv("SMTP_HOST") or None,
            smtp_port=env_int("SMTP_PORT", 587),
            smtp_username=os.getenv("SMTP_USERNAME") or None,
            smtp_password=os.getenv("SMTP_PASSWORD") or None,
            email_from=os.getenv("EMAIL_FROM") or None,
            email_to=os.getenv("EMAIL_TO") or None,
            github_token=os.getenv("GITHUB_TOKEN") or None,
            github_repository=os.getenv("GITHUB_REPOSITORY") or None,
            github_issue_notifications=env_bool("GITHUB_ISSUE_NOTIFICATIONS", True),
        )


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    return float(value)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}
