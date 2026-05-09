from app.services.llm import generate_text


def synthesize_answer(user_input, local_data, web_data):

    prompt = f"""
You are a kindness assistant.

User request:
{user_input}

---

LOCAL DATABASE RESULTS (trusted sources):
{local_data}

---

WEB RESULTS (fallback, less reliable):
{web_data}

---

RULES:
- Prefer local data first
- Suggest real-world actions
- Always explain how user can participate
- Include links if available
- Be concrete, not abstract

Return helpful structured answer.
"""

    return generate_text(prompt)