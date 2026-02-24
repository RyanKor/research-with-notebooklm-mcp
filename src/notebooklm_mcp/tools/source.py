"""Source management tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register source management tools."""

    @mcp.tool()
    async def source_add_url(notebook_id: str, url: str) -> str:
        """Add a URL as a source to a notebook. Supports web pages, articles, etc.

        Args:
            notebook_id: The ID of the notebook.
            url: The URL to add as a source.

        Returns:
            Source info with ID and processing status.
        """
        client = await get_client()
        source = await client.sources.add_url(notebook_id, url, wait=True)
        return (
            f"Source added successfully.\n"
            f"  ID: {source.id}\n"
            f"  Title: {source.title}\n"
            f"  Type: {source.source_type}\n"
            f"  Status: {source.status}"
        )

    @mcp.tool()
    async def source_add_text(notebook_id: str, title: str, content: str) -> str:
        """Add plain text content as a source to a notebook.

        Args:
            notebook_id: The ID of the notebook.
            title: Title for the text source.
            content: The text content to add.

        Returns:
            Source info with ID and processing status.
        """
        client = await get_client()
        source = await client.sources.add_text(notebook_id, title, content, wait=True)
        return (
            f"Text source added successfully.\n"
            f"  ID: {source.id}\n"
            f"  Title: {source.title}\n"
            f"  Status: {source.status}"
        )

    @mcp.tool()
    async def source_add_file(notebook_id: str, file_path: str) -> str:
        """Add a local file as a source (PDF, text, Markdown, Word, audio, video, images).

        Args:
            notebook_id: The ID of the notebook.
            file_path: Path to the local file to upload.

        Returns:
            Source info with ID and processing status.
        """
        client = await get_client()
        source = await client.sources.add_file(notebook_id, file_path, wait=True)
        return (
            f"File source added successfully.\n"
            f"  ID: {source.id}\n"
            f"  Title: {source.title}\n"
            f"  Type: {source.source_type}\n"
            f"  Status: {source.status}"
        )

    @mcp.tool()
    async def source_list(notebook_id: str) -> str:
        """List all sources in a notebook.

        Args:
            notebook_id: The ID of the notebook.

        Returns:
            Formatted list of all sources with their IDs, titles, and types.
        """
        client = await get_client()
        sources = await client.sources.list(notebook_id)
        if not sources:
            return "No sources in this notebook. Add sources with source_add_url, source_add_text, or source_add_file."

        lines = [f"Found {len(sources)} source(s):\n"]
        for src in sources:
            lines.append(
                f"  - [{src.id}] {src.title} (type: {src.source_type}, status: {src.status})"
            )
        return "\n".join(lines)

    @mcp.tool()
    async def source_get_fulltext(notebook_id: str, source_id: str) -> str:
        """Get the full indexed text content of a source. Useful for RAG and analysis.

        Args:
            notebook_id: The ID of the notebook.
            source_id: The ID of the source.

        Returns:
            The full text content that NotebookLM has indexed from the source.
        """
        client = await get_client()
        fulltext = await client.sources.get_fulltext(notebook_id, source_id)
        return (
            f"Source Fulltext (ID: {source_id}):\n"
            f"Title: {fulltext.title}\n"
            f"Content length: {len(fulltext.content)} chars\n\n"
            f"{fulltext.content}"
        )

    @mcp.tool()
    async def source_get_guide(notebook_id: str, source_id: str) -> str:
        """Get the AI-generated study guide for a source.

        Args:
            notebook_id: The ID of the notebook.
            source_id: The ID of the source.

        Returns:
            The AI-generated guide/summary for the source.
        """
        client = await get_client()
        guide = await client.sources.get_guide(notebook_id, source_id)
        return f"Source Guide (ID: {source_id}):\n{guide}"

    @mcp.tool()
    async def source_delete(notebook_id: str, source_id: str) -> str:
        """Delete a source from a notebook.

        Args:
            notebook_id: The ID of the notebook.
            source_id: The ID of the source to delete.

        Returns:
            Confirmation of deletion.
        """
        client = await get_client()
        success = await client.sources.delete(notebook_id, source_id)
        if success:
            return f"Source {source_id} deleted successfully."
        return f"Failed to delete source {source_id}."
