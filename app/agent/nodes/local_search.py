from app.database.search import search_mixed, random_initiatives


def local_search(category=None, query=None):

    # 🧠 1. если есть сигнал — используем structured search
    if category or query:
        results = search_mixed(category=category, query=query)

        # fallback если ничего не найдено
        if results and len(results) > 0:
            return results

    # 🌱 2. fallback — random inspiration
    return random_initiatives(limit=3)