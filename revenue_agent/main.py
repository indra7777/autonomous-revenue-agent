from __future__ import annotations

import argparse
import uuid

from .config import Settings
from .models import AgentRun, utc_now
from .notifier import notify
from .planner import build_instruction
from .ranker import rank_opportunities, select_actionable
from .sources import collect_opportunities
from .storage import append_history, ensure_dirs, load_revenue, save_opportunities, save_run, save_subagent_task


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the autonomous revenue agent once.")
    parser.add_argument("--once", action="store_true", help="Run one scan/planning cycle. This is the default.")
    parser.add_argument("--no-notify", action="store_true", help="Generate reports without Slack/email notification.")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    ensure_dirs(settings.state_dir, settings.report_dir)

    created_at = utc_now()
    opportunities = collect_opportunities(
        max_items_per_source=settings.max_items_per_source,
        timeout_seconds=settings.timeout_seconds,
        custom_feed_urls=settings.custom_feed_urls,
    )
    scored = rank_opportunities(opportunities)
    save_opportunities(settings.state_dir, scored)

    revenue_sources = load_revenue(settings.state_dir)
    selected = select_actionable(scored)
    instruction = build_instruction(
        created_at=created_at,
        selected=selected,
        revenue_sources=revenue_sources,
        opportunities_seen=len(opportunities),
    )

    run = AgentRun(
        run_id=str(uuid.uuid4())[:8],
        created_at=created_at,
        selected=selected,
        instruction_markdown=instruction,
        opportunities_seen=len(opportunities),
    )

    report_path = save_run(settings.report_dir, run)
    save_subagent_task(settings.state_dir, run)

    errors: list[str] = []
    if not args.no_notify:
        errors = notify(settings, "Autonomous Revenue Agent: next action", instruction)
        if errors:
            run = AgentRun(
                run_id=run.run_id,
                created_at=run.created_at,
                selected=run.selected,
                instruction_markdown=run.instruction_markdown,
                opportunities_seen=run.opportunities_seen,
                notification_errors=tuple(errors),
            )
    append_history(settings.state_dir, run)

    print(f"Wrote {report_path}")
    if errors:
        for error in errors:
            print(error)
    return 0
