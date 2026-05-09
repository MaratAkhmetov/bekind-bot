from app.database.search import search_by_category, search_by_tag, random_initiatives


def local_search(category=None, query=None):

    if category and category != "unclear":
        return search_by_category(category)

    if query:
        return search_by_tag(query)

    return random_initiatives()