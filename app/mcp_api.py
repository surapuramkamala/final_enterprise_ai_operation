
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agent_workflow import run_agent_workflow

app = FastAPI(title="Enterprise AI MCP and A2A Demo")


class AskRequest(BaseModel):
    question: str


@app.post("/mcp-a2a/ask")
async def ask(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    try:
        return await run_agent_workflow(question)
    except Exception:
        # Log the exception server-side in production.
        raise HTTPException(
            status_code=500,
            detail="The MCP/A2A workflow failed. Check server logs.",
        )
