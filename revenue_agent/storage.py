from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import AgentRun, RevenueSource, ScoredOpportunity


def ensure_dirs(state_dir: Path, report_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "subagents").mkdir(parents=True, exist_ok=True)


def load_revenue(state_dir: Path) -> list[RevenueSource]:
    path = state_dir / "revenue.json"
    if not path.exists():
        sources = [RevenueSource(name="manual", amount_inr=0, notes="Update this file after revenue is received.")]
        path.write_text(json.dumps([asdict(source) for source in sources], indent=2) + "\n", encoding="utf-8")
        return sources
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [RevenueSource(name="manual", amount_inr=0, notes="Invalid revenue.json; reset needed.")]
    sources: list[RevenueSource] = []
    for item in payload if isinstance(payload, list) else []:
        if isinstance(item, dict):
            sources.append(
                RevenueSource(
                    name=str(item.get("name", "unknown")),
                    amount_inr=float(item.get("amount_inr", 0) or 0),
                    notes=str(item.get("notes", "")),
                )
            )
    return sources


def save_opportunities(state_dir: Path, scored: list[ScoredOpportunity]) -> None:
    payload = []
    for item in scored[:50]:
        payload.append(
            {
                "total": item.total,
                "ease": item.ease,
                "payment_probability": item.payment_probability,
                "repeatability": item.repeatability,
                "risk": item.risk,
                "reasons": list(item.reasons),
                "source": item.opportunity.source,
                "title": item.opportunity.title,
                "url": item.opportunity.url,
                "summary": item.opportunity.summary,
                "published_at": item.opportunity.published_at,
            }
        )
    (state_dir / "opportunities.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def save_run(report_dir: Path, run: AgentRun) -> Path:
    filename = f"{run.created_at.strftime('%Y-%m-%dT%H%M%SZ')}-{run.run_id}.md"
    path = report_dir / filename
    path.write_text(run.instruction_markdown, encoding="utf-8")
    latest = report_dir / "latest.md"
    latest.write_text(run.instruction_markdown, encoding="utf-8")
    return path


def save_subagent_task(state_dir: Path, run: AgentRun) -> Path | None:
    selected = run.selected
    if selected is None:
        return None
    path = state_dir / "subagents" / f"{run.created_at.strftime('%Y-%m-%dT%H%M%SZ')}-{run.run_id}.json"
    payload: dict[str, Any] = {
        "role": "sales_copy_subagent",
        "created_at": run.created_at.isoformat(),
        "goal": "Prepare one approval-gated revenue action for the human overseer.",
        "opportunity": {
            "source": selected.opportunity.source,
            "title": selected.opportunity.title,
            "url": selected.opportunity.url,
            "summary": selected.opportunity.summary,
        },
        "constraints": [
            "No autonomous posting.",
            "No account creation.",
            "No paid tools.",
            "No false claims.",
            "Human must approve and send the final message.",
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def append_history(state_dir: Path, run: AgentRun) -> None:
    path = state_dir / "history.jsonl"
    record = {
        "run_id": run.run_id,
        "created_at": run.created_at.isoformat(),
        "selected_title": run.selected.opportunity.title if run.selected else None,
        "selected_url": run.selected.opportunity.url if run.selected else None,
        "opportunities_seen": run.opportunities_seen,
        "notification_errors": list(run.notification_errors),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
