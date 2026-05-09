from tavily import TavilyClient
from app.config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def web_search(query: str):
    try:
        result = client.search(query=query)

        return {
            "results": result.get("results", []),
            "query": query
        }

    except Exception:
        return {
            "results": [],
            "query": query
        }