from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None, exclude_names=None):

    if category:
        category = category.lower().strip()

    if category == "mixed" or (not category and not query):
        return random_initiatives(
            limit=3,
            category=None,
            exclude_names=exclude_names
        )

    results = search_mixed(
        category=category,
        query=query,
        exclude_names=exclude_names
    )

    return results or []