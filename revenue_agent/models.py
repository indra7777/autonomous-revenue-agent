from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


@dataclass(frozen=True)
class Opportunity:
    source: str
    title: str
    url: str
    summary: str = ""
    published_at: str = ""
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredOpportunity:
    opportunity: Opportunity
    ease: int
    payment_probability: int
    repeatability: int
    risk: int
    reasons: tuple[str, ...]

    @property
    def total(self) -> int:
        return self.ease + self.payment_probability + self.repeatability - self.risk


@dataclass(frozen=True)
class RevenueSource:
    name: str
    amount_inr: float
    notes: str = ""


@dataclass(frozen=True)
class AgentRun:
    run_id: str
    created_at: datetime
    selected: ScoredOpportunity | None
    instruction_markdown: str
    opportunities_seen: int
    notification_errors: tuple[str, ...] = ()
