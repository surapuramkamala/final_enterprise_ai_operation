
from contextlib import asynccontextmanager

import logging

logger = logging.getLogger(__name__)

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.config import JWT_SECRET, validate_config
from app.agents import supervisor_agent
from app.observability import trace_request
from app.rag import load_documents
from app.security import validate_input, validate_output
from app.tools import approve_change

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings, validate_config

import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.auth_routes import router as auth_router


app = FastAPI(
    title="Enterprise AI Platform",
    version="1.0.0"
)
frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_config()
    count = load_documents()
    print(f"Indexed {count} document chunks")
    yield


app = FastAPI(
    title="Enterprise AI Operations Platform",
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=3000)


class ApprovalRequest(BaseModel):
    request_id: str = Field(min_length=1)


def current_user(authorization: str = Header(...)):
    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Bearer token required")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
        )
        if not payload.get("sub") or not payload.get("role"):
            raise HTTPException(401, "Invalid token claims")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")


security = HTTPBearer()


security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
        )

        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid token")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(
    request: AskRequest,
    user=Depends(get_current_user),
):
    try:
        question = validate_input(request.question)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    try:
        result = trace_request(
            question,
            lambda: supervisor_agent(
                question,
                str(user["sub"]),
            ),
        )
    except Exception:
        logger.exception("AI provider request failed")
        # Avoid leaking provider credentials or stack traces.
        raise HTTPException(
            502,
            "AI request failed. Check server logs and provider configuration.",
        )

    if result["agent"] == "rag_agent":
        result["result"]["answer"] = validate_output(
            result["result"]["answer"]
        )

    return result


@app.post("/approvals/approve")
def approve(
    request: ApprovalRequest,
    user=Depends(get_current_user),
):
    if user.get("role") != "approver":
        raise HTTPException(403, "Approver role required")

    result = approve_change(
        request.request_id,
        str(user["sub"]),
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    return result


@app.post("/admin/reindex")
def reindex(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin role required")

    try:
        count = load_documents()
    except Exception:
        raise HTTPException(500, "Document indexing failed")

    return {"status": "indexed", "chunks": count}
