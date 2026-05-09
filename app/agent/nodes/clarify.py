def ask_clarification(intent: dict):

    category = intent.get("category", "unclear")

    if category == "animals":
        return {
            "type": "clarification",
            "message": "Would you like to help animals via volunteering, donations, or fostering?"
        }

    if category == "environment":
        return {
            "type": "clarification",
            "message": "Are you interested in cleanups, tree planting, or environmental education?"
        }

    if category == "community":
        return {
            "type": "clarification",
            "message": "Do you want to help elderly people, homeless support, or community initiatives?"
        }

    return {
        "type": "clarification",
        "message": "What kind of good deed would you like to do?"
    }