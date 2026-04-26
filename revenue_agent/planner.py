from __future__ import annotations

from datetime import datetime

from .models import RevenueSource, ScoredOpportunity


def build_instruction(
    *,
    created_at: datetime,
    selected: ScoredOpportunity | None,
    revenue_sources: list[RevenueSource],
    opportunities_seen: int,
) -> str:
    total_revenue = sum(source.amount_inr for source in revenue_sources)
    revenue_lines = "\n".join(
        f"- {source.name}: ₹{source.amount_inr:.2f}" + (f" ({source.notes})" if source.notes else "")
        for source in revenue_sources
    )

    if selected is None:
        action = fallback_action()
        opportunity_block = "No suitable live opportunity was found. Using fallback product experiment."
        decision = "Should the agent keep fallback prompt-pack creation as the primary track for the next 24 hours? Yes/No"
    else:
        action = action_for(selected)
        opportunity = selected.opportunity
        reasons = ", ".join(selected.reasons)
        opportunity_block = (
            f"Selected opportunity: {opportunity.title}\n\n"
            f"Source: {opportunity.source}\n\n"
            f"URL: {opportunity.url}\n\n"
            f"Score: {selected.total} "
            f"(ease {selected.ease}, payment {selected.payment_probability}, "
            f"repeatability {selected.repeatability}, risk {selected.risk})\n\n"
            f"Why this: {reasons}"
        )
        decision = decision_for(selected)

    reinvestment = reinvestment_note(total_revenue)
    return f"""# Autonomous Revenue Agent Instruction

Generated: {created_at.isoformat()}

Opportunities scanned: {opportunities_seen}

## One Human Action

{action}

## One Yes/No Decision

{decision}

## Earning Report

Total recorded revenue: ₹{total_revenue:.2f}

{revenue_lines or "- No revenue recorded yet."}

{reinvestment}

## Opportunity Rationale

{opportunity_block}

## Operating Rule

If this experiment earns ₹0 after 7 days, drop it. If it earns less than ₹85/day after 14 days, reduce it to 10% effort and test the next variant.
"""


def action_for(scored: ScoredOpportunity) -> str:
    opportunity = scored.opportunity
    category = categorize(f"{opportunity.title} {opportunity.summary}")
    if category == "service":
        return service_action(opportunity.title, opportunity.url)
    if category == "content":
        return content_action(opportunity.title, opportunity.url)
    if category == "product":
        return product_action(opportunity.title, opportunity.url)
    return service_action(opportunity.title, opportunity.url)


def service_action(title: str, url: str) -> str:
    return f"""Open this lead and send the message below only if the post rules allow replies or DMs:

Lead: {title}
URL: {url}

Exact message:

Hi, I can help with this today. I can deliver a clean first draft within 24 hours using a simple approval workflow: 1) I send a concise draft, 2) you request one revision if needed, 3) I deliver the final file/text. I can keep the scope small and fixed-price. If this is still open, send me the brief and preferred format and I will start with a sample direction."""


def content_action(title: str, url: str) -> str:
    return f"""Create a short value post based on this signal, then publish it on one free channel you already use:

Signal: {title}
URL: {url}

Exact post:

I am testing a zero-cost, 24-hour microservice: send me a rough idea, resume bullet, product page, or announcement and I will rewrite it into a sharper version. First 3 requests are free samples today; paid follow-up starts at ₹499 for a polished version. Reply with "rewrite" and one paragraph."""


def product_action(title: str, url: str) -> str:
    return f"""Build a tiny digital asset today and list it on Gumroad for free-to-create distribution:

Signal: {title}
URL: {url}

Exact listing copy:

Title: 25 High-Converting AI Prompts for Job Seekers
Description: A compact prompt pack for resumes, cover letters, LinkedIn summaries, interview practice, and recruiter outreach. Built for people who need a better job-search workflow today. Pay what you want; suggested price ₹99."""


def fallback_action() -> str:
    return """Create and post the first fallback offer today:

Exact post:

I am giving away a small "25 ChatGPT prompts for job seekers" pack today and using feedback to decide the paid version. It includes resume rewrites, LinkedIn headline ideas, cover letter drafts, interview practice, and recruiter outreach prompts. Comment "prompts" and I will send it. If it saves you time, the expanded version will be pay-what-you-want."""


def decision_for(scored: ScoredOpportunity) -> str:
    if scored.risk >= 5:
        return "Is this opportunity clean enough to pursue despite the risk flags? Yes/No"
    if scored.payment_probability >= 6:
        return "Double down on this service category for the next 24 hours? Yes/No"
    return "Should the agent test this as a lead source for one more run? Yes/No"


def reinvestment_note(total_revenue: float) -> str:
    if total_revenue < 500:
        return "Reinvestment status: below ₹500. Keep all activity free."
    ad = total_revenue * 0.2
    operator = total_revenue * 0.2
    va = total_revenue * 0.2
    profit = total_revenue * 0.4
    return (
        "Reinvestment status: ₹500+ threshold reached.\n\n"
        f"- Buy extra human time: ₹{operator:.2f}\n"
        f"- Test small ads: ₹{ad:.2f}\n"
        f"- Hire VA support: ₹{va:.2f}\n"
        f"- Keep profit: ₹{profit:.2f}"
    )


def categorize(text: str) -> str:
    lower = text.lower()
    if any(keyword in lower for keyword in ("template", "pack", "gumroad", "notion", "prompt")):
        return "product"
    if any(keyword in lower for keyword in ("article", "blog", "tweet", "thread", "linkedin", "copy", "rewrite")):
        return "content"
    return "service"
