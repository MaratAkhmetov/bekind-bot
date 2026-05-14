from tavily import TavilyClient
from app.config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def web_search(query: str, exclude_urls=None):

    exclude_urls = exclude_urls or []

    try:

        result = client.search(
            query=query,
            max_results=10
        )

        cleaned = []

        for item in result.get("results", []):

            url = item.get("url", "").strip().lower().rstrip("/")

            if url in exclude_urls:
                continue

            cleaned.append({
                "name": item.get("title", "Unknown"),
                "description": item.get("content", ""),
                "website": item.get("url", ""),
                "instagram": "",
                "facebook": "",
                "_source": "web"
            })

        return {
            "results": cleaned,
            "query": query
        }

    except Exception as e:

        print("WEB SEARCH ERROR:", e)

        return {
            "results": [],
            "query": query
        }