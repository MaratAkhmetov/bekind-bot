from typing import TypedDict


class AgentState(TypedDict, total=False):

    user_input: str

    intent: str
    category: str
    action_type: str

    intent_confidence: float

    clarification_needed: bool
    is_invalid: bool
    is_unsupported: bool

    local_results: list
    web_results: list

    final_answer: str