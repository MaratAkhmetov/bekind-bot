from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None):

    results = search_mixed(
        category=category,
        query=query
    )

    # ✅ если есть результат — возвращаем
    if results and len(results) > 0:
        return results

    # 🔥 fallback 1: try random
    fallback = random_initiatives(limit=3)

    if fallback:
        return fallback

    # 🔥 absolute fallback
    return [
        {
            "name": "No initiatives found",
            "description": "Try animals, environment or community"
        }
    ]