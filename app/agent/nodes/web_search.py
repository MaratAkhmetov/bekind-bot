from tavily import TavilyClient
from app.config import TAVILY_API_KEY
from app.utils.logger import logger

client = TavilyClient(api_key=TAVILY_API_KEY)


def web_search(query: str, exclude_urls=None):

    exclude_urls = exclude_urls or []

    logger.info(f"[WEB] QUERY = {query}")

    try:
        result = client.search(
            query=query,
            max_results=10
        )

        raw = result.get("results", [])

        logger.info(f"[WEB] RAW RESULTS = {len(raw)}")

        cleaned = []

        for item in raw:

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

        logger.info(f"[WEB] CLEANED RESULTS = {len(cleaned)}")

        return {
            "results": cleaned,
            "query": query
        }

    except Exception as e:
        logger.error(f"[WEB ERROR] {e}")

        return {
            "results": [],
            "query": query
        }