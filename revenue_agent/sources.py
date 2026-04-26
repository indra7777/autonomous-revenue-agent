from __future__ import annotations

import html
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Iterable

from .http import fetch_text
from .models import Opportunity


REDDIT_SUBREDDITS = (
    "slavelabour",
    "forhire",
    "DoneDirtCheap",
    "hireawriter",
    "DesignJobs",
)

HN_QUERIES = (
    "looking for help",
    "need a freelancer",
    "launching side project",
    "paid gig",
)

GOOGLE_NEWS_QUERIES = (
    "AI tools affiliate program launch",
    "new resume templates demand",
    "small business looking for virtual assistant",
)


def collect_opportunities(max_items_per_source: int, timeout_seconds: float, custom_feed_urls: Iterable[str] = ()) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    opportunities.extend(fetch_reddit(max_items_per_source, timeout_seconds))
    opportunities.extend(fetch_hacker_news(max_items_per_source, timeout_seconds))
    opportunities.extend(fetch_google_news(max_items_per_source, timeout_seconds))
    for url in custom_feed_urls:
        opportunities.extend(fetch_rss(url, source="custom-rss", limit=max_items_per_source, timeout_seconds=timeout_seconds))
    return dedupe(opportunities)


def fetch_reddit(limit: int, timeout_seconds: float) -> list[Opportunity]:
    items: list[Opportunity] = []
    for subreddit in REDDIT_SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        result = fetch_text(url, timeout=timeout_seconds)
        if not result.ok:
            continue
        try:
            payload = result.json()
        except json.JSONDecodeError:
            continue
        children = payload.get("data", {}).get("children", []) if isinstance(payload, dict) else []
        for child in children[:limit]:
            data = child.get("data", {})
            title = clean(data.get("title", ""))
            permalink = data.get("permalink", "")
            if not title or not permalink:
                continue
            summary = clean(data.get("selftext", ""))[:500]
            items.append(
                Opportunity(
                    source=f"reddit/r/{subreddit}",
                    title=title,
                    url=urllib.parse.urljoin("https://www.reddit.com", permalink),
                    summary=summary,
                    published_at=str(data.get("created_utc", "")),
                    raw={"subreddit": subreddit, "author": str(data.get("author", ""))},
                )
            )
    return items


def fetch_hacker_news(limit: int, timeout_seconds: float) -> list[Opportunity]:
    items: list[Opportunity] = []
    for query in HN_QUERIES:
        encoded = urllib.parse.urlencode({"query": query, "tags": "story", "hitsPerPage": str(limit)})
        url = f"https://hn.algolia.com/api/v1/search_by_date?{encoded}"
        result = fetch_text(url, timeout=timeout_seconds)
        if not result.ok:
            continue
        try:
            payload = result.json()
        except json.JSONDecodeError:
            continue
        hits = payload.get("hits", []) if isinstance(payload, dict) else []
        for hit in hits[:limit]:
            title = clean(hit.get("title") or hit.get("story_title") or "")
            item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            if not title or not item_url:
                continue
            items.append(
                Opportunity(
                    source=f"hn/{query}",
                    title=title,
                    url=item_url,
                    summary=clean(hit.get("story_text") or hit.get("comment_text") or "")[:500],
                    published_at=str(hit.get("created_at", "")),
                    raw={"query": query},
                )
            )
    return items


def fetch_google_news(limit: int, timeout_seconds: float) -> list[Opportunity]:
    items: list[Opportunity] = []
    for query in GOOGLE_NEWS_QUERIES:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        items.extend(fetch_rss(url, source=f"google-news/{query}", limit=limit, timeout_seconds=timeout_seconds))
    return items


def fetch_rss(url: str, source: str, limit: int, timeout_seconds: float) -> list[Opportunity]:
    result = fetch_text(url, timeout=timeout_seconds)
    if not result.ok:
        return []
    try:
        root = ET.fromstring(result.body)
    except ET.ParseError:
        return []
    items: list[Opportunity] = []
    for item in root.findall(".//item")[:limit]:
        title = clean(text_of(item, "title"))
        link = text_of(item, "link")
        description = clean(text_of(item, "description"))[:500]
        published = text_of(item, "pubDate")
        if title and link:
            items.append(Opportunity(source=source, title=title, url=link, summary=description, published_at=published))
    return items


def dedupe(opportunities: Iterable[Opportunity]) -> list[Opportunity]:
    seen: set[str] = set()
    unique: list[Opportunity] = []
    for opportunity in opportunities:
        key = normalize_key(opportunity.url or opportunity.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(opportunity)
    return unique


def text_of(item: ET.Element, child_name: str) -> str:
    child = item.find(child_name)
    return child.text or "" if child is not None else ""


def clean(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    collapsed = re.sub(r"\s+", " ", html.unescape(without_tags)).strip()
    return collapsed


def normalize_key(value: str) -> str:
    normalized = value.lower().strip()
    normalized = re.sub(r"[?#].*$", "", normalized)
    normalized = re.sub(r"\W+", "", normalized)
    return normalized
