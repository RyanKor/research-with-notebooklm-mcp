"""Web and Drive research tools."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register research tools."""

    @mcp.tool()
    async def research_web(
        notebook_id: str,
        query: str,
        mode: str = "fast",
    ) -> str:
        """Run a web research query and auto-import discovered sources.

        NotebookLM's research agent will search the web for relevant content
        and can automatically add discovered sources to the notebook.

        Args:
            notebook_id: The ID of the notebook.
            query: The research query/topic to search for.
            mode: Research mode - "fast" for quick results, "deep" for thorough research.

        Returns:
            Research results including discovered sources.
        """
        client = await get_client()
        result = await client.research.start(
            notebook_id, query, source="web", mode=mode
        )

        if result is None:
            return "Research started but no immediate results. Use research_poll to check status."

        return _format_research_result(result, query, "web", mode)

    @mcp.tool()
    async def research_drive(
        notebook_id: str,
        query: str,
        mode: str = "fast",
    ) -> str:
        """Run a Google Drive research query and auto-import discovered sources.

        Searches through your Google Drive for relevant documents.

        Args:
            notebook_id: The ID of the notebook.
            query: The research query/topic to search for.
            mode: Research mode - "fast" for quick results, "deep" for thorough research.

        Returns:
            Research results including discovered Drive documents.
        """
        client = await get_client()
        result = await client.research.start(
            notebook_id, query, source="drive", mode=mode
        )

        if result is None:
            return "Research started but no immediate results. Use research_poll to check status."

        return _format_research_result(result, query, "drive", mode)

    @mcp.tool()
    async def research_poll(notebook_id: str) -> str:
        """Poll the status of an ongoing research task.

        Args:
            notebook_id: The ID of the notebook with active research.

        Returns:
            Current research status and any available results.
        """
        client = await get_client()
        result = await client.research.poll(notebook_id)
        return f"Research status:\n{result}"

    @mcp.tool()
    async def research_import_sources(
        notebook_id: str,
        task_id: str,
        sources: list[dict],
    ) -> str:
        """Import specific sources discovered during research.

        After running research_web or research_drive, use this to selectively
        import discovered sources into the notebook.

        Args:
            notebook_id: The ID of the notebook.
            task_id: The task ID from the research result.
            sources: List of source dicts with 'url' and 'title' keys to import.

        Returns:
            Results of the import operation.
        """
        client = await get_client()
        result = await client.research.import_sources(notebook_id, task_id, sources)
        return f"Imported {len(result)} source(s) from research results."


def _format_research_result(
    result: dict, query: str, source_type: str, mode: str
) -> str:
    """Format research results for display."""
    lines = [
        f"Research completed ({source_type}, {mode} mode)",
        f"Query: {query}",
        f"\nResults:",
    ]

    if isinstance(result, dict):
        for key, value in result.items():
            lines.append(f"  {key}: {value}")
    else:
        lines.append(f"  {result}")

    return "\n".join(lines)
