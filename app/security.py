
import re
import jwt

from app.config import JWT_SECRET

BLOCKED_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"show\s+me\s+.*secret",
]


def validate_input(question: str) -> str:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty")

    if len(question) > 3000:
        raise ValueError("Question exceeds 3000 characters")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            raise ValueError("Potential prompt injection detected")

    return question


def validate_output(answer: str) -> str:
    if not answer.strip():
        return "No answer could be generated."

    if re.search(
        r"(?i)(api[_ -]?key|password|access[_ -]?token)\s*[:=]\s*\S+",
        answer,
    ):
        return "Response blocked by output security."

    return answer


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=["HS256"],
    )
