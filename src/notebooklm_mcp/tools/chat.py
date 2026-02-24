"""RAG Q&A / Chat tools - the core research capability."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register chat/RAG tools."""

    @mcp.tool()
    async def chat_ask(
        notebook_id: str,
        question: str,
        source_ids: list[str] | None = None,
    ) -> str:
        """Ask a question about the sources in a notebook (RAG Q&A).

        This is the primary research tool. NotebookLM will answer based on
        the indexed sources in the notebook, with citations.

        Args:
            notebook_id: The ID of the notebook containing sources.
            question: The question to ask about the sources.
            source_ids: Optional list of specific source IDs to query against.
                       If None, all sources in the notebook are used.

        Returns:
            NotebookLM's answer with citations from the sources.
        """
        client = await get_client()
        result = await client.chat.ask(
            notebook_id, question, source_ids=source_ids
        )

        response_parts = [f"Answer:\n{result.answer}"]

        if hasattr(result, "references") and result.references:
            response_parts.append("\nReferences:")
            for ref in result.references:
                response_parts.append(f"  - {ref}")

        return "\n".join(response_parts)

    @mcp.tool()
    async def chat_ask_specific_sources(
        notebook_id: str,
        question: str,
        source_ids: list[str],
    ) -> str:
        """Ask a question targeting specific sources only (focused RAG).

        Use this when you want answers from only a subset of sources,
        e.g., comparing two specific papers.

        Args:
            notebook_id: The ID of the notebook.
            question: The question to ask.
            source_ids: List of source IDs to limit the query to.

        Returns:
            NotebookLM's answer based only on the specified sources.
        """
        client = await get_client()
        result = await client.chat.ask(
            notebook_id, question, source_ids=source_ids
        )

        response_parts = [
            f"Answer (from {len(source_ids)} selected source(s)):\n{result.answer}"
        ]

        if hasattr(result, "references") and result.references:
            response_parts.append("\nReferences:")
            for ref in result.references:
                response_parts.append(f"  - {ref}")

        return "\n".join(response_parts)

    @mcp.tool()
    async def chat_configure(
        notebook_id: str,
        custom_prompt: str | None = None,
    ) -> str:
        """Configure the chat persona/behavior for a notebook.

        Set a custom system prompt to guide how NotebookLM responds to questions.

        Args:
            notebook_id: The ID of the notebook.
            custom_prompt: Custom system prompt for the chat persona (e.g.,
                          "You are an expert in machine learning. Always provide
                          technical details and cite specific papers.").

        Returns:
            Confirmation of configuration update.
        """
        client = await get_client()
        await client.chat.configure(
            notebook_id, custom_prompt=custom_prompt
        )
        return (
            f"Chat configured for notebook {notebook_id}.\n"
            f"Custom prompt: {custom_prompt or '(default)'}"
        )
