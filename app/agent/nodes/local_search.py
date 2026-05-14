from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None, exclude_names=None):

    # normalize category
    if category:
        category = category.capitalize()

    # RANDOM MIXED
    if category == "Mixed" or (not category and not query):
        return random_initiatives(
            limit=3,
            category=None,
            exclude_names=exclude_names
        )

    # STRICT CATEGORY SEARCH
    if category in ["Animals", "Environment", "Community"]:

        results = search_mixed(
            category=category,
            query=query,
            exclude_names=exclude_names
        )

        # IMPORTANT:
        # if enough local results → use them
        if results and len(results) >= 3:
            return results

        # NOT ENOUGH RESULTS
        return results or []

    # GENERIC SEARCH
    results = search_mixed(
        category=None,
        query=query,
        exclude_names=exclude_names
    )

    if results:
        return results

    # IMPORTANT:
    # RETURN EMPTY
    return []