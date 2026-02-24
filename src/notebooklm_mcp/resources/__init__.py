"""MCP Resources for NotebookLM."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    """Register MCP resources."""

    @mcp.resource("notebooklm://notebooks")
    async def list_notebooks() -> str:
        """List all available notebooks."""
        from notebooklm_mcp.client import get_client

        client = await get_client()
        notebooks = await client.notebooks.list()

        if not notebooks:
            return "No notebooks found."

        lines = []
        for nb in notebooks:
            lines.append(f"- [{nb.id}] {nb.title}")
        return "\n".join(lines)

    @mcp.resource("notebooklm://status")
    async def server_status() -> str:
        """Check the NotebookLM MCP server status and authentication."""
        from notebooklm_mcp.client import get_client

        try:
            client = await get_client()
            notebooks = await client.notebooks.list()
            return (
                f"Status: Connected\n"
                f"Notebooks: {len(notebooks)}\n"
                f"Authentication: Valid"
            )
        except RuntimeError as e:
            return f"Status: Not connected\nError: {e}"
