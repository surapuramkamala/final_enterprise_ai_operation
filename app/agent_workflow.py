
import json

from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def server_parameters(filename: str):
    return StdioServerParameters(
        command=__import__("sys").executable,
        args=[str(PROJECT_ROOT / "mcp_servers" / filename)],
    )


async def call_mcp_tool(filename: str, tool_name: str, arguments: dict):
    """Start an MCP server, call its tool, and return the result."""
    params = server_parameters(filename)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            if result.isError:
                raise RuntimeError(f"MCP tool failed: {tool_name}")

            structured = getattr(result, "structuredContent", None)
            if structured is not None:
                return structured

            return [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ]


async def research_agent(question: str) -> dict:
    """Agent 1: Collect evidence using two MCP tools."""

    incidents = await call_mcp_tool(
        "incident_server.py",
        "search_incidents",
        {"keyword": question},
    )

    documents = await call_mcp_tool(
        "document_server.py",
        "search_documents",
        {"query": question},
    )

    return {
        "agent": "research_agent",
        "question": question,
        "incidents": incidents,
        "documents": documents,
    }


async def rca_agent(research_result: dict) -> dict:
    """Agent 2: Analyze the evidence passed by Agent 1."""

    incident_data = research_result["incidents"]
    document_data = research_result["documents"]

    evidence = json.dumps({
        "incidents": incident_data,
        "documents": document_data,
    }, indent=2)

    # This is a rule-based demonstration, not an LLM diagnosis.
    if not incident_data and not document_data:
        analysis = (
            "Insufficient evidence. Retrieve relevant incident "
            "records and documents before recommending a fix."
        )
    elif incident_data:
        analysis = (
            "Review the incident description, recorded resolution, "
            "and relevant policy evidence before confirming the root cause."
        )
    else:
        analysis = (
            "Relevant policy information was found, but no matching "
            "incident record was returned."
        )

    return {
        "agent": "rca_agent",
        "received_from": research_result["agent"],
        "analysis": analysis,
        "evidence": evidence,
    }


async def run_agent_workflow(question: str) -> dict:
    # Agent 1 researches using both MCP integrations.
    research_result = await research_agent(question)

    # A2A handoff: Agent 1 passes its results to Agent 2.
    rca_result = await rca_agent(research_result)

    return {
        "workflow": "research_to_rca",
        "research": research_result,
        "root_cause_analysis": rca_result,
    }
