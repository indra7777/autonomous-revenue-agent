from __future__ import annotations

import json
import smtplib
import urllib.request
from email.message import EmailMessage
from urllib.error import HTTPError

from .config import Settings


def notify(settings: Settings, subject: str, markdown: str) -> list[str]:
    errors: list[str] = []
    if settings.github_issue_notifications and settings.github_token and settings.github_repository:
        error = send_github_issue(settings.github_token, settings.github_repository, subject, markdown)
        if error:
            errors.append(error)
    if settings.slack_webhook_url:
        error = send_slack(settings.slack_webhook_url, subject, markdown)
        if error:
            errors.append(error)
    if settings.smtp_host and settings.email_from and settings.email_to:
        error = send_email(settings, subject, markdown)
        if error:
            errors.append(error)
    return errors


def send_slack(webhook_url: str, subject: str, markdown: str) -> str | None:
    text = f"*{subject}*\n\n{trim_for_slack(markdown)}"
    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            if response.status >= 300:
                return f"Slack returned HTTP {response.status}"
    except Exception as exc:
        return f"Slack notification failed: {exc}"
    return None


def send_github_issue(token: str, repository: str, subject: str, markdown: str) -> str | None:
    try:
        issue = find_github_inbox_issue(token, repository)
        if issue is None:
            request_json(
                token,
                f"https://api.github.com/repos/{repository}/issues",
                {
                    "title": "Autonomous Revenue Agent Inbox",
                    "body": f"## {subject}\n\n{markdown}",
                },
            )
        else:
            number = issue["number"]
            request_json(
                token,
                f"https://api.github.com/repos/{repository}/issues/{number}/comments",
                {"body": f"## {subject}\n\n{markdown}"},
            )
    except Exception as exc:
        return f"GitHub issue notification failed: {exc}"
    return None


def find_github_inbox_issue(token: str, repository: str) -> dict[str, object] | None:
    issues = request_json(token, f"https://api.github.com/repos/{repository}/issues?state=open&per_page=100", None)
    if not isinstance(issues, list):
        return None
    for issue in issues:
        if isinstance(issue, dict) and issue.get("title") == "Autonomous Revenue Agent Inbox":
            return issue
    return None


def request_json(token: str, url: str, payload: dict[str, object] | None) -> object:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = response.read().decode("utf-8", errors="replace")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub HTTP {exc.code}: {body[:500]}") from exc


def send_email(settings: Settings, subject: str, markdown: str) -> str | None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from or ""
    message["To"] = settings.email_to or ""
    message.set_content(markdown)
    try:
        with smtplib.SMTP(settings.smtp_host or "", settings.smtp_port, timeout=12) as smtp:
            smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception as exc:
        return f"Email notification failed: {exc}"
    return None


def trim_for_slack(markdown: str) -> str:
    if len(markdown) <= 3500:
        return markdown
    return markdown[:3400].rstrip() + "\n\n[trimmed; see reports/latest.md for full instruction]"
