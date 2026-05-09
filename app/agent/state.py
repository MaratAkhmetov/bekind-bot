from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    user_input: str
    intent: str
    clarification_needed: bool
    local_results: str
    web_results: str
    final_answer: str