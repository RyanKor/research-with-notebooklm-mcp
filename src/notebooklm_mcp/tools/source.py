"""Source management tools."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client

logger = logging.getLogger(__name__)

# Supported file extensions for batch upload
# Reference: https://support.google.com/notebooklm/answer/16215270
SUPPORTED_EXTENSIONS = {
    # Documents
    ".pdf", ".txt", ".md", ".markdown", ".docx", ".pptx", ".xlsx",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    # Audio
    ".mp3", ".wav", ".m4a",
}


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
    async def source_add_batch(
        notebook_id: str,
        urls: list[str] | None = None,
        file_paths: list[str] | None = None,
        directory_path: str | None = None,
        file_pattern: str = "*",
    ) -> str:
        """Add multiple sources to a notebook at once (batch operation).

        Supports adding multiple URLs, files, and/or all matching files
        from a directory simultaneously.

        Args:
            notebook_id: The ID of the notebook.
            urls: Optional list of URLs to add as sources.
            file_paths: Optional list of local file paths to upload.
            directory_path: Optional directory path to scan for files.
            file_pattern: Glob pattern for directory scan (default "*").
                         Examples: "*.pdf", "*.md", "report_*".

        Returns:
            Summary of batch operation with success/failure counts.
        """
        client = await get_client()
        all_urls = list(urls or [])
        all_files = list(file_paths or [])

        # Scan directory if provided
        if directory_path:
            dir_path = Path(directory_path)
            if not dir_path.is_dir():
                return f"Error: Directory not found: {directory_path}"

            for f in dir_path.glob(file_pattern):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                    all_files.append(str(f))

        if not all_urls and not all_files:
            return "Error: No sources to add. Provide urls, file_paths, or directory_path."

        # Build coroutines for concurrent execution
        results: list[dict] = []

        async def add_url(url: str) -> dict:
            try:
                source = await client.sources.add_url(notebook_id, url, wait=False)
                return {"type": "url", "name": url, "id": source.id, "ok": True}
            except Exception as e:
                return {"type": "url", "name": url, "error": str(e), "ok": False}

        async def add_file(fp: str) -> dict:
            try:
                source = await client.sources.add_file(notebook_id, fp, wait=False)
                return {"type": "file", "name": fp, "id": source.id, "ok": True}
            except Exception as e:
                return {"type": "file", "name": fp, "error": str(e), "ok": False}

        coros = [add_url(u) for u in all_urls] + [add_file(f) for f in all_files]
        results = await asyncio.gather(*coros, return_exceptions=True)

        # Separate successes and failures
        succeeded = []
        failed = []
        for r in results:
            if isinstance(r, Exception):
                failed.append({"name": "unknown", "error": str(r)})
            elif r["ok"]:
                succeeded.append(r)
            else:
                failed.append(r)

        # Wait for successful sources to finish processing
        if succeeded:
            source_ids = [s["id"] for s in succeeded]
            try:
                await client.sources.wait_for_sources(notebook_id, source_ids)
            except Exception as e:
                logger.warning(f"Error waiting for sources: {e}")

        # Build summary
        lines = [f"Batch add complete: {len(succeeded)} succeeded, {len(failed)} failed.\n"]

        if succeeded:
            lines.append("Succeeded:")
            for s in succeeded:
                lines.append(f"  + [{s['id']}] {s['name']} ({s['type']})")

        if failed:
            lines.append("\nFailed:")
            for f in failed:
                lines.append(f"  - {f.get('name', 'unknown')}: {f.get('error', 'unknown error')}")

        return "\n".join(lines)

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
