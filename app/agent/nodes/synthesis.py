def synthesize_answer(user_input, local_data, web_data):

    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    text = "Here are real initiatives you can support:\n\n"

    for i, item in enumerate(data[:5], start=1):

        name = item.get("name", "Unknown")
        description = item.get("description", "")

        website = item.get("website")
        instagram = item.get("instagram")
        facebook = item.get("facebook")

        text += f"{i}. {name}\n"
        text += f"{description}\n"

        # =====================================
        # LINKS PRIORITY SYSTEM
        # =====================================
        if website:
            text += f"🌐 Website: {website}\n"

        if instagram:
            text += f"📸 Instagram: {instagram}\n"
        elif facebook:
            text += f"📘 Facebook: {facebook}\n"

        text += "\n"

    text += "💚 Small actions create real impact."

    return text