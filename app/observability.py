
import json
import logging
import os
import time
from uuid import uuid4

logger = logging.getLogger("enterprise_ai")
logging.basicConfig(level=logging.INFO)

# Configure these from your NVIDIA pricing information.
INPUT_COST_PER_MILLION = float(
    os.getenv("INPUT_COST_PER_MILLION", "0")
)
OUTPUT_COST_PER_MILLION = float(
    os.getenv("OUTPUT_COST_PER_MILLION", "0")
)


def estimate_cost(prompt_tokens, completion_tokens):
    if prompt_tokens is None or completion_tokens is None:
        return None

    return round(
        prompt_tokens * INPUT_COST_PER_MILLION / 1_000_000
        + completion_tokens * OUTPUT_COST_PER_MILLION / 1_000_000,
        8,
    )


def trace_request(question: str, operation):
    trace_id = str(uuid4())
    start = time.perf_counter()
    status = "error"
    result = None

    try:
        result = operation()
        status = "success"
        return result

    finally:
        latency_ms = round(
            (time.perf_counter() - start) * 1000, 2
        )

        usage = (
            result.get("result", {}).get("usage")
            if isinstance(result, dict)
            else None
        ) or {}

        event = {
            "trace_id": trace_id,
            "operation": "supervisor_request",
            "status": status,
            "latency_ms": latency_ms,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "estimated_cost": estimate_cost(
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
            ),
        }

        logger.info(json.dumps(event))

