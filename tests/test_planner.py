import unittest
from datetime import datetime, timezone

from revenue_agent.models import Opportunity, RevenueSource
from revenue_agent.planner import build_instruction
from revenue_agent.ranker import score_opportunity


class PlannerTest(unittest.TestCase):
    def test_instruction_contains_single_action_decision_and_report(self) -> None:
        opportunity = Opportunity(
            source="test",
            title="Paid resume rewrite needed $20",
            url="https://example.com/resume",
            summary="Fixed budget for a resume rewrite.",
        )
        instruction = build_instruction(
            created_at=datetime(2026, 4, 26, tzinfo=timezone.utc),
            selected=score_opportunity(opportunity),
            revenue_sources=[RevenueSource(name="manual", amount_inr=0)],
            opportunities_seen=1,
        )

        self.assertIn("## One Human Action", instruction)
        self.assertIn("## One Yes/No Decision", instruction)
        self.assertIn("## Earning Report", instruction)
        self.assertIn("https://example.com/resume", instruction)


if __name__ == "__main__":
    unittest.main()
