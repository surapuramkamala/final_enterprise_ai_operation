
from app.rag import answer_question
from app.tools import create_change_request


def rag_agent(question: str) -> dict:
    return answer_question(question)


def operations_agent(question: str, user_id: str) -> dict:
    return create_change_request(question, user_id)


def supervisor_agent(question: str, user_id: str) -> dict:
    normalized = question.lower()

    sensitive_actions = [
        "delete production",
        "remove production",
        "modify production records",
    ]

    if any(action in normalized for action in sensitive_actions):
        return {
            "agent": "operations_agent",
            "result": operations_agent(question, user_id),
        }

    return {
        "agent": "rag_agent",
        "result": rag_agent(question),
    }
