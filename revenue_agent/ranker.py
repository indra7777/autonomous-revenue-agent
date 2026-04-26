from __future__ import annotations

import re

from .models import Opportunity, ScoredOpportunity


EASY_KEYWORDS = {
    "logo",
    "banner",
    "resume",
    "cv",
    "cover letter",
    "tweet",
    "thread",
    "linkedin",
    "caption",
    "notion",
    "canva",
    "prompt",
    "blog",
    "article",
    "summary",
    "rewrite",
    "proofread",
    "landing page copy",
    "data entry",
    "spreadsheet",
}

PAYMENT_KEYWORDS = {
    "paid",
    "budget",
    "fixed",
    "bounty",
    "hire",
    "hiring",
    "commission",
    "contract",
    "freelance",
    "gig",
    "$",
    "₹",
    "usd",
    "inr",
}

REPEATABLE_KEYWORDS = {
    "template",
    "pack",
    "prompts",
    "resume",
    "logo",
    "thread",
    "article",
    "weekly",
    "monthly",
    "ongoing",
    "batch",
    "bulk",
}

RISK_KEYWORDS = {
    "crypto",
    "adult",
    "nsfw",
    "casino",
    "betting",
    "essay",
    "homework",
    "fake review",
    "followers",
    "upvotes",
    "captcha",
    "scrape emails",
    "commission only",
    "unpaid",
    "equity only",
}

SELLER_KEYWORDS = {
    "[for hire]",
    "for hire",
    "hire me",
    "my rate",
    "my portfolio",
    "i can help",
    "i can make",
    "looking for clients",
}

BUYER_KEYWORDS = {
    "[hiring]",
    "[task]",
    "hiring",
    "need someone",
    "looking for someone",
    "seeking",
    "paid task",
    "fixed budget",
    "i would like to hire",
}

HARD_KEYWORDS = {
    "full stack",
    "backend",
    "mobile app",
    "machine learning",
    "blockchain",
    "rust",
    "kubernetes",
    "senior",
    "years experience",
    "enterprise",
}


def rank_opportunities(opportunities: list[Opportunity]) -> list[ScoredOpportunity]:
    scored = [score_opportunity(opportunity) for opportunity in opportunities]
    return sorted(scored, key=lambda item: (item.total, item.payment_probability, item.ease), reverse=True)


def score_opportunity(opportunity: Opportunity) -> ScoredOpportunity:
    text = f"{opportunity.title} {opportunity.summary}".lower()
    reasons: list[str] = []
    title_text = opportunity.title.lower()

    ease = 2
    easy_hits = keyword_hits(text, EASY_KEYWORDS)
    hard_hits = keyword_hits(text, HARD_KEYWORDS)
    ease += min(4, len(easy_hits) * 2)
    ease -= min(3, len(hard_hits) * 2)
    if easy_hits:
        reasons.append(f"easy keywords: {', '.join(easy_hits[:3])}")
    if hard_hits:
        reasons.append(f"hard keywords: {', '.join(hard_hits[:3])}")

    payment_probability = 1
    payment_hits = keyword_hits(text, PAYMENT_KEYWORDS)
    buyer_hits = keyword_hits(text, BUYER_KEYWORDS)
    seller_hits = keyword_hits(text, SELLER_KEYWORDS)
    amount = extract_amount(text)
    has_buyer_signal = bool(buyer_hits)
    payment_probability += min(5, len(payment_hits)) if has_buyer_signal else min(2, len(payment_hits))
    payment_probability += min(3, len(buyer_hits) * 2)
    if amount:
        payment_probability += 2 if has_buyer_signal else 1
        reasons.append(f"visible budget: {amount}")
    if payment_hits:
        reasons.append(f"payment signals: {', '.join(payment_hits[:3])}")
    if buyer_hits:
        reasons.append(f"buyer signals: {', '.join(buyer_hits[:3])}")
    if seller_hits:
        payment_probability = min(payment_probability, 2)
        reasons.append(f"seller/self-promotion signals: {', '.join(seller_hits[:3])}")

    repeatability = 1
    repeat_hits = keyword_hits(text, REPEATABLE_KEYWORDS)
    repeatability += min(5, len(repeat_hits) * 2)
    if repeat_hits:
        reasons.append(f"repeatable: {', '.join(repeat_hits[:3])}")

    risk = 0
    risk_hits = keyword_hits(text, RISK_KEYWORDS)
    risk += min(8, len(risk_hits) * 3)
    if seller_hits or title_text.startswith("[for hire]"):
        risk += 8
    if opportunity.source.startswith(("hn/", "google-news/")) and not has_buyer_signal:
        risk += 3
        reasons.append("market-signal source without direct buyer intent")
    if risk_hits:
        reasons.append(f"risk keywords: {', '.join(risk_hits[:3])}")

    return ScoredOpportunity(
        opportunity=opportunity,
        ease=clamp(ease, 0, 10),
        payment_probability=clamp(payment_probability, 0, 10),
        repeatability=clamp(repeatability, 0, 10),
        risk=clamp(risk, 0, 10),
        reasons=tuple(reasons) or ("generic opportunity",),
    )


def keyword_hits(text: str, keywords: set[str]) -> list[str]:
    return sorted(keyword for keyword in keywords if keyword in text)


def extract_amount(text: str) -> str | None:
    match = re.search(r"(?:\$|₹)\s?\d+(?:[,.]\d+)?|\b\d+(?:[,.]\d+)?\s?(?:usd|inr)\b", text)
    return match.group(0) if match else None


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
