from app.agent.workflow import run_workflow
from app.agent.nodes.intent import analyze_intent


def test_vague_request():

    result = run_workflow("i want to help")

    assert result["type"] == "clarification"


def test_invalid_input():

    result = analyze_intent("asdasdasd")

    assert result["is_invalid"] is True


def test_unsupported_request():

    result = analyze_intent("find me a job")

    assert result["is_unsupported"] is True


def test_animals_request():

    result = analyze_intent("help stray cats")

    assert result["category"] == "Animals"


def test_environment_request():

    result = analyze_intent("cleanup rivers")

    assert result["category"] == "Environment"