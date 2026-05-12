from app.database.search import search_mixed, random_initiatives

def local_search(category=None, query=None, exclude_names=None):
    # normalize category
    if category:
        category = category.capitalize()   # Animals / Environment / Community / Mixed

    # if category is explicitly Mixed or equivalent to trigger random selection
    if category == "Mixed" or (not category and not query):
        return random_initiatives(limit=3, category=None, exclude_names=exclude_names)

    # 1. strict category search
    if category in ["Animals", "Environment", "Community"]:
        results = search_mixed(category=category, query=query, exclude_names=exclude_names)
        if results:
            return results
        # fallback ONLY same category
        return random_initiatives(limit=3, category=category, exclude_names=exclude_names)

    # 2. fallback: mixed/tag-based
    results = search_mixed(category=None, query=query, exclude_names=exclude_names)
    if results:
        return results

    return random_initiatives(limit=3, category=None, exclude_names=exclude_names)