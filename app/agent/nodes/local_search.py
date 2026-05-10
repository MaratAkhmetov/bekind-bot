from app.database.search import search_mixed, random_initiatives


from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None):

    # =====================================
    # 1. STRICT CATEGORY SEARCH (ВАЖНО)
    # =====================================

    if category in ["animals", "environment", "community"]:

        results = search_mixed(category=category, query=query)

        if results:
            return results

        # fallback: random within category ONLY
        return random_initiatives(limit=3, category=category)

    # =====================================
    # 2. fallback search
    # =====================================
    results = search_mixed(category=None, query=query)

    if results:
        return results

    return random_initiatives()