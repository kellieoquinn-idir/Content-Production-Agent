"""Researcher resources.

Same idea as get_weather in weather_agent.py: a @tool the model can call.
search_sources hits the live web (DuckDuckGo). If search fails, it falls
back to the stub catalog so the pipeline still runs.
"""

from langchain.tools import tool


def _stub_sources(topic: str) -> str:
    slug = "-".join(topic.strip().lower().split()) or "travel"
    sources = [
        (
            "National tourism board visitor guide",
            f"https://www.example-tourism.gov/guides/{slug}",
            f"The official visitor guide covering '{topic}' lists peak season, "
            "shoulder season, and neighborhood overviews for trip planning.",
        ),
        (
            "National meteorological service climate normals",
            f"https://www.example-weather.gov/climate/{slug}",
            f"Climate normals for '{topic}' include typical monthly highs, lows, "
            "and rainfall, which is used to recommend the best months to go.",
        ),
        (
            "Government statistics office overnight-stay report",
            f"https://www.example-stats.gov/tourism/{slug}",
            f"Overnight-stay data for '{topic}' shows which months have the "
            "highest visitor volume and which months are less crowded.",
        ),
        (
            "City events calendar",
            f"https://www.example-city.gov/events/{slug}",
            f"The municipal events calendar for '{topic}' lists major festivals "
            "and public holidays that affect crowds, prices, and closures.",
        ),
        (
            "Public-transit operator visitor information",
            f"https://www.example-transit.gov/visitors/{slug}",
            f"Transit visitor information for '{topic}' covers airport links, "
            "passes, and how to get between the main districts without a car.",
        ),
        (
            "Foreign ministry travel advice",
            f"https://www.example-travel-advice.gov/destinations/{slug}",
            f"Official travel advice for '{topic}' covers entry rules, safety "
            "notes, and documents visitors should have before they go.",
        ),
    ]
    lines = [f"Source catalog results for: {topic} (stub fallback)", ""]
    for i, (title, url, fact) in enumerate(sources, start=1):
        lines.append(f"{i}. {title}")
        lines.append(f"   Fact: {fact}")
        lines.append(f"   Citation: {url}")
        lines.append("")
    return "\n".join(lines).strip()


def _web_search(topic: str, max_results: int = 8) -> str:
    from ddgs import DDGS

    results = list(DDGS().text(topic, max_results=max_results))
    if not results:
        raise ValueError("search returned no results")

    lines = [f"Live web search results for: {topic}", ""]
    for i, item in enumerate(results, start=1):
        title = item.get("title") or "(untitled)"
        url = item.get("href") or ""
        fact = item.get("body") or ""
        lines.append(f"{i}. {title}")
        lines.append(f"   Fact: {fact}")
        lines.append(f"   Citation: {url}")
        lines.append("")
    return "\n".join(lines).strip()


@tool
def search_sources(topic: str) -> str:
    """Search credible sources for a travel blog topic.

    Use this before writing a research brief. The input should be the blog
    topic, for example: 'best time to visit Lisbon' or 'hiking in Patagonia'.
    Returns at least five facts with citations and links for verification.
    """
    try:
        return _web_search(topic)
    except Exception as exc:
        return (
            f"Live web search failed ({exc}). Using stub catalog instead.\n\n"
            + _stub_sources(topic)
        )
