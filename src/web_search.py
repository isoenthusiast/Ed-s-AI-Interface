"""
🌐 Web Search module — queries DuckDuckGo and formats results for the AI agent.
Zero API key required.
"""

import threading
from typing import Optional


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using DuckDuckGo and return formatted results.
    
    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).
    
    Returns:
        List of dicts with keys: title, url, snippet.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return [{"error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}]

    results = []
    try:
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        return [{"error": str(e)}]

    return results


def format_search_results(query: str, results: list[dict]) -> str:
    """Format search results into a prompt-friendly string."""
    if not results:
        return f"No results found for: \"{query}\""

    if "error" in results[0]:
        return f"Search error: {results[0]['error']}"

    lines = [f"## 🌐 Web Search Results for: \"{query}\"\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"**{i}. {r['title']}**")
        lines.append(f"   {r['snippet']}")
        lines.append(f"   🔗 {r['url']}")
        lines.append("")

    return "\n".join(lines)


def should_search(query: str) -> bool:
    """Heuristic: detect if the user is asking for current/recent information."""
    triggers = [
        "latest", "recent", "news", "today", "current",
        "search", "look up", "find me", "from the web",
        "price of", "stock", "weather", "2024", "2025", "2026",
        "updated", "release date", "just came out",
        "what happened", "breaking", "who won",
    ]
    q_lower = query.lower()
    return any(t in q_lower for t in triggers)


def search_async(query: str, callback, max_results: int = 5):
    """Run a web search in a background thread and call callback(results) when done."""
    def worker():
        results = search_web(query, max_results)
        callback(query, results)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
