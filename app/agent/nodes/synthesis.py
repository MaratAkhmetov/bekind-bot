def synthesize_answer(user_input, local_data, web_data):

    data = local_data or web_data or []

    if not data:
        return (
            "I couldn't find exact initiatives.\n\n"
            "Try:\n"
            "🐾 animals\n"
            "🌍 environment\n"
            "🤝 community"
        )

    text = "Here are real initiatives you can support:\n\n"

    for i, item in enumerate(data[:5], start=1):

        name = item.get("name", "Unknown")
        description = item.get("description", "No description available")

        website = item.get("website")
        instagram = item.get("instagram")
        facebook = item.get("facebook")

        text += f"{i}. {name}\n"
        text += f"{description}\n"

        # 🌐 LINKS (clean fallback logic)
        if website:
            text += f"🌐 Website: {website}\n"
        elif instagram:
            text += f"📸 Instagram: {instagram}\n"
        elif facebook:
            text += f"📘 Facebook: {facebook}\n"
        else:
            text += "🔗 No public links available\n"

        text += "\n"

    text += "💚 Small actions create real impact."

    return text