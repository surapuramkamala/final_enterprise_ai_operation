
from app.rag import answer_question

GOLDEN_DATASET = [
    {
        "question": "How do I request production access?",
        "expected_terms": ["IT service desk", "approval"],
        "expected_source": "employee_policy.txt",
    },
    {
        "question": "Is password sharing allowed?",
        "expected_terms": ["prohibited"],
        "expected_source": "employee_policy.txt",
    },
]


def evaluate_rag():
    report = []

    for case in GOLDEN_DATASET:
        response = answer_question(case["question"])
        answer = response["answer"].lower()

        term_coverage = sum(
            term.lower() in answer
            for term in case["expected_terms"]
        ) / len(case["expected_terms"])

        source_found = any(
            item["source"] == case["expected_source"]
            for item in response["citations"]
        )

        report.append({
            "question": case["question"],
            "term_coverage": round(term_coverage, 2),
            "source_found": source_found,
        })

    return report


if __name__ == "__main__":
    for item in evaluate_rag():
        print(item)
