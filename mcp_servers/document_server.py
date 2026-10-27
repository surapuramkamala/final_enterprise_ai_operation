
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KnowledgeDocuments")

DOCUMENT_PATH = Path("data/knowledge.txt")


@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Search the local knowledge document by keyword."""
    if not DOCUMENT_PATH.exists():
        return []

    text = DOCUMENT_PATH.read_text(encoding="utf-8")
    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    terms = query.lower().split()

    results = []
    for index, paragraph in enumerate(paragraphs):
        if any(term in paragraph.lower() for term in terms):
            results.append({
                "source": "knowledge.txt",
                "section": index + 1,
                "text": paragraph
            })

    return results[:5]


if __name__ == "__main__":
    mcp.run()
