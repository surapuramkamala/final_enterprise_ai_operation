
import re
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

from app.config import EMBEDDING_MODEL
from app.llm import generate_answer

import logging

logger = logging.getLogger(__name__)


DATA_DIR = Path("data")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

embedding_model = None
reranker = None
chunks = []
vector_index = None
bm25_index = None


def initialize_models():
    global embedding_model, reranker

    if embedding_model is None:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    if reranker is None:
        reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L6-v2"
        )


def split_text(text: str) -> list[str]:
    result = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            result.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return result


def load_documents() -> int:
    global chunks, vector_index, bm25_index

    initialize_models()
    chunks = []

    for path in DATA_DIR.glob("*"):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue

        text = path.read_text(encoding="utf-8")

        for number, chunk in enumerate(split_text(text), start=1):
            chunks.append({
                "text": chunk,
                "source": path.name,
                "chunk_id": number,
            })

    if not chunks:
        vector_index = None
        bm25_index = None
        return 0

    texts = [item["text"] for item in chunks]

    vectors = embedding_model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    vector_index = faiss.IndexFlatIP(vectors.shape[1])
    vector_index.add(vectors)

    tokenized = [
        re.findall(r"\w+", text.lower())
        for text in texts
    ]
    bm25_index = BM25Okapi(tokenized)

    return len(chunks)


def retrieve(question: str, top_k: int = 5) -> list[dict]:
    if not chunks or vector_index is None or bm25_index is None:
        return []

    query_vector = embedding_model.encode(
        [question],
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    k = min(top_k, len(chunks))
    _, vector_ids = vector_index.search(query_vector, k)

    keyword_scores = bm25_index.get_scores(
        re.findall(r"\w+", question.lower())
    )
    keyword_ids = np.argsort(keyword_scores)[::-1][:k]

    # Combine candidates without duplicating document chunks.
    candidate_ids = list(dict.fromkeys(
        list(vector_ids[0]) + list(keyword_ids)
    ))
    candidate_ids = [
        int(i) for i in candidate_ids if i >= 0
    ]

    candidates = [chunks[i] for i in candidate_ids]

    if not candidates:
        return []

    pairs = [
        (question, item["text"])
        for item in candidates
    ]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(candidates, scores),
        key=lambda pair: float(pair[1]),
        reverse=True,
    )

    return [
        {**item, "rerank_score": round(float(score), 4)}
        for item, score in ranked[:3]
    ]


def answer_question(question: str) -> dict:
    results = retrieve(question)

    if not results:
        return {
            "answer": "I don't know based on the indexed documents.",
            "citations": [],
            "usage": None,
        }

    context_parts = []
    for i, item in enumerate(results, start=1):
        context_parts.append(
            f"[{i}] Source: {item['source']}, "
            f"chunk: {item['chunk_id']}\n{item['text']}"
        )

    context = "\n\n".join(context_parts)
    
    logger.info("RAG question: %s", question)
    logger.info("RAG context length: %d", len(context or ""))
    logger.info("RAG context empty: %s", not bool((context or "").strip()))
    llm_result = generate_answer(question, context)
    answer = llm_result["answer"]

    # Keep only citations that correspond to retrieved evidence.
    citations = []
    for i, item in enumerate(results, start=1):
        if re.search(rf"\[{i}\]", answer):
            citations.append({
                "citation": f"[{i}]",
                "source": item["source"],
                "chunk_id": item["chunk_id"],
            })

    return {
        "answer": answer,
        "citations": citations,
        "usage": {
            "model": llm_result["model"],
            "prompt_tokens": llm_result["prompt_tokens"],
            "completion_tokens": llm_result["completion_tokens"],
        },
    }
