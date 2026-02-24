"""Notebook management tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register notebook management tools."""

    @mcp.tool()
    async def notebook_create(title: str) -> str:
        """Create a new NotebookLM notebook.

        Args:
            title: The title for the new notebook.

        Returns:
            JSON with notebook id, title, and creation info.
        """
        client = await get_client()
        nb = await client.notebooks.create(title)
        return (
            f"Notebook created successfully.\n"
            f"  ID: {nb.id}\n"
            f"  Title: {nb.title}\n"
            f"  Created: {nb.created_at}\n\n"
            f"Use this notebook_id for subsequent operations."
        )

    @mcp.tool()
    async def notebook_list() -> str:
        """List all NotebookLM notebooks.

        Returns:
            A formatted list of all notebooks with their IDs and titles.
        """
        client = await get_client()
        notebooks = await client.notebooks.list()
        if not notebooks:
            return "No notebooks found. Create one with notebook_create."

        lines = [f"Found {len(notebooks)} notebook(s):\n"]
        for nb in notebooks:
            lines.append(f"  - [{nb.id}] {nb.title} (created: {nb.created_at})")
        return "\n".join(lines)

    @mcp.tool()
    async def notebook_get(notebook_id: str) -> str:
        """Get detailed information about a specific notebook.

        Args:
            notebook_id: The ID of the notebook.

        Returns:
            Detailed notebook info including summary and description.
        """
        client = await get_client()
        nb = await client.notebooks.get(notebook_id)
        summary = await client.notebooks.get_summary(notebook_id)

        result = [
            f"Notebook: {nb.title}",
            f"  ID: {nb.id}",
            f"  Created: {nb.created_at}",
        ]
        if summary:
            result.append(f"\nSummary:\n{summary}")
        return "\n".join(result)

    @mcp.tool()
    async def notebook_delete(notebook_id: str) -> str:
        """Delete a notebook.

        Args:
            notebook_id: The ID of the notebook to delete.

        Returns:
            Confirmation of deletion.
        """
        client = await get_client()
        success = await client.notebooks.delete(notebook_id)
        if success:
            return f"Notebook {notebook_id} deleted successfully."
        return f"Failed to delete notebook {notebook_id}."

    @mcp.tool()
    async def notebook_rename(notebook_id: str, new_title: str) -> str:
        """Rename a notebook.

        Args:
            notebook_id: The ID of the notebook to rename.
            new_title: The new title for the notebook.

        Returns:
            Confirmation with updated notebook info.
        """
        client = await get_client()
        nb = await client.notebooks.rename(notebook_id, new_title)
        return f"Notebook renamed to: {nb.title} (ID: {nb.id})"
