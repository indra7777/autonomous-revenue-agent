import unittest

from revenue_agent.models import Opportunity
from revenue_agent.ranker import rank_opportunities


class RankerTest(unittest.TestCase):
    def test_ranker_prefers_fixed_price_easy_repeatable_work(self) -> None:
        logo = Opportunity(
            source="test",
            title="Paid fixed budget logo and banner gig $25",
            url="https://example.com/logo",
            summary="Need a quick logo template and social banner.",
        )
        hard = Opportunity(
            source="test",
            title="Senior full stack blockchain platform",
            url="https://example.com/hard",
            summary="Equity only, long-term, crypto.",
        )

        ranked = rank_opportunities([hard, logo])

        self.assertEqual(ranked[0].opportunity.url, "https://example.com/logo")
        self.assertGreater(ranked[0].total, ranked[1].total)

    def test_ranker_penalizes_risky_unpaid_work(self) -> None:
        risky = Opportunity(
            source="test",
            title="Unpaid crypto followers gig",
            url="https://example.com/risk",
            summary="Need followers and upvotes.",
        )

        scored = rank_opportunities([risky])[0]

        self.assertGreaterEqual(scored.risk, 6)

    def test_ranker_prefers_buyer_posts_over_for_hire_posts(self) -> None:
        seller = Opportunity(
            source="test",
            title="[FOR HIRE] Freelance graphic designer $20/hr",
            url="https://example.com/seller",
            summary="I can make logos and banners. My portfolio is ready.",
        )
        buyer = Opportunity(
            source="test",
            title="[Hiring] Turn logo into vector art $30 paid",
            url="https://example.com/buyer",
            summary="I would like to hire someone for a fixed budget logo vector task.",
        )

        ranked = rank_opportunities([seller, buyer])

        self.assertEqual(ranked[0].opportunity.url, "https://example.com/buyer")
        self.assertGreaterEqual(ranked[1].risk, 8)


if __name__ == "__main__":
    unittest.main()
