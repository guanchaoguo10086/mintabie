"""web_search tool — search the web and extract content."""

import json
import logging

from tools.registry import registry

logger = logging.getLogger(__name__)


def web_search(args: dict, **kw) -> str:
    """Search the web via a configurable search API."""
    query = args.get("query", "")
    if not query:
        return json.dumps({"error": "No query provided", "success": False})

    # Basic implementation using DuckDuckGo (no API key needed)
    import urllib.parse
    import urllib.request

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Simple extraction of result snippets
        import re
        results = []
        for m in re.finditer(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL,
        ):
            results.append({
                "url": m.group(1),
                "title": re.sub(r"<[^>]+>", "", m.group(2)).strip(),
                "snippet": re.sub(r"<[^>]+>", "", m.group(3)).strip(),
            })

        return json.dumps({"results": results[:10], "success": True})
    except Exception as e:
        logger.exception("web_search failed")
        return json.dumps({"error": str(e), "success": False})


def web_extract(args: dict, **kw) -> str:
    """Extract content from a URL."""
    urls = args.get("urls", [])
    if isinstance(urls, str):
        urls = [urls]
    if not urls:
        return json.dumps({"error": "No URLs provided", "success": False})

    import urllib.request
    import re

    results = []
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Strip HTML tags
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            # Limit to first 5000 chars
            text = text[:5000]
            results.append({"url": url, "content": text, "success": True})
        except Exception as e:
            results.append({"url": url, "error": str(e), "success": False})

    return json.dumps({"results": results, "success": True})


registry.register(
    name="web_search",
    description="Search the web for information",
    schema={
        "name": "web_search",
        "description": "Search the web and return results",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    handler=web_search,
    toolset="web",
    emoji="🌐",
)

registry.register(
    name="web_extract",
    description="Extract content from a URL",
    schema={
        "name": "web_extract",
        "description": "Fetch and extract text content from one or more URLs",
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URL(s) to extract content from",
                },
            },
            "required": ["urls"],
        },
    },
    handler=web_extract,
    toolset="web",
    emoji="📄",
)
