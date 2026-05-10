from app.database.search import search_mixed, random_initiatives


from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None):

    # normalize category
    if category:
        category = category.capitalize()   # Animals / Environment / Community

    # 1. strict category search
    if category in ["Animals", "Environment", "Community"]:

        results = search_mixed(category=category, query=query)

        if results:
            return results

        # fallback ONLY same category
        return random_initiatives(limit=3, category=category)

    # 2. fallback
    results = search_mixed(category=None, query=query)

    if results:
        return results

    return random_initiatives()