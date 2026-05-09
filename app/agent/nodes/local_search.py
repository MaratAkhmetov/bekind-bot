from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None):

    results = search_mixed(
        category=category,
        query=query
    )

    # если нашли — возвращаем
    if results:
        return results

    # fallback
    return random_initiatives(limit=3)