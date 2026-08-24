"""Researcher resources.

Same idea as get_weather in weather_agent.py: a @tool the model can call.
This stub is the fake city dict. Swap the function body later for MCP/Google;
keep the name and docstring so the researcher agent does not change.
"""

from langchain.tools import tool


@tool
def search_sources(topic: str) -> str:
    """Search credible sources for a travel blog topic.

    Use this before writing a research brief. The input should be the blog
    topic, for example: 'best time to visit Lisbon' or 'hiking in Patagonia'.
    Returns at least five facts with citations and links for verification.
    """
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

    lines = [f"Source catalog results for: {topic}", ""]
    for i, (title, url, fact) in enumerate(sources, start=1):
        lines.append(f"{i}. {title}")
        lines.append(f"   Fact: {fact}")
        lines.append(f"   Citation: {url}")
        lines.append("")
    return "\n".join(lines).strip()
