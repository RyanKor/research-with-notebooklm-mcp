"""RAG Q&A / Chat tools - the core research capability."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client

logger = logging.getLogger(__name__)

# Module-level conversation state: notebook_id → conversation_id
_active_conversations: dict[str, str] = {}


def register(mcp: FastMCP) -> None:
    """Register chat/RAG tools."""

    @mcp.tool()
    async def chat_ask(
        notebook_id: str,
        question: str,
        source_ids: list[str] | None = None,
        continue_conversation: bool = False,
    ) -> str:
        """Ask a question about the sources in a notebook (RAG Q&A).

        This is the primary research tool. NotebookLM will answer based on
        the indexed sources in the notebook, with citations.

        Args:
            notebook_id: The ID of the notebook containing sources.
            question: The question to ask about the sources.
            source_ids: Optional list of specific source IDs to query against.
                       If None, all sources in the notebook are used.
            continue_conversation: If True, continues the previous conversation
                                  in this notebook (maintains context from prior Q&A).

        Returns:
            NotebookLM's answer with citations from the sources.
        """
        client = await get_client()

        kwargs: dict = {"source_ids": source_ids}

        # Use existing conversation if continuing
        if continue_conversation and notebook_id in _active_conversations:
            kwargs["conversation_id"] = _active_conversations[notebook_id]

        result = await client.chat.ask(notebook_id, question, **kwargs)

        # Store conversation_id for future use
        if hasattr(result, "conversation_id") and result.conversation_id:
            _active_conversations[notebook_id] = result.conversation_id

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
        continue_conversation: bool = False,
    ) -> str:
        """Ask a question targeting specific sources only (focused RAG).

        Use this when you want answers from only a subset of sources,
        e.g., comparing two specific papers.

        Args:
            notebook_id: The ID of the notebook.
            question: The question to ask.
            source_ids: List of source IDs to limit the query to.
            continue_conversation: If True, continues the previous conversation
                                  in this notebook.

        Returns:
            NotebookLM's answer based only on the specified sources.
        """
        client = await get_client()

        kwargs: dict = {"source_ids": source_ids}

        if continue_conversation and notebook_id in _active_conversations:
            kwargs["conversation_id"] = _active_conversations[notebook_id]

        result = await client.chat.ask(notebook_id, question, **kwargs)

        if hasattr(result, "conversation_id") and result.conversation_id:
            _active_conversations[notebook_id] = result.conversation_id

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

    @mcp.tool()
    async def chat_history(notebook_id: str, limit: int = 10) -> str:
        """Get recent chat history for a notebook.

        Retrieves the conversation turns from the active conversation
        in the specified notebook.

        Args:
            notebook_id: The ID of the notebook.
            limit: Maximum number of recent turns to return (default 10).

        Returns:
            Formatted chat history with questions and answers.
        """
        if notebook_id not in _active_conversations:
            return "No active conversation for this notebook. Start one with chat_ask."

        conversation_id = _active_conversations[notebook_id]
        client = await get_client()

        try:
            turns = await client.chat.get_cached_turns(conversation_id)
        except (AttributeError, Exception) as e:
            logger.debug(f"get_cached_turns failed: {e}")
            return (
                f"Active conversation exists (ID: {conversation_id}), "
                f"but history retrieval is not supported by the current library version."
            )

        if not turns:
            return f"No turns found in conversation {conversation_id}."

        # Limit results
        if limit and limit > 0:
            turns = turns[-limit:]

        lines = [f"Chat History (last {len(turns)} turn(s)):\n"]
        for i, turn in enumerate(turns, 1):
            q = getattr(turn, "question", getattr(turn, "query", "N/A"))
            a = getattr(turn, "answer", getattr(turn, "response", "N/A"))
            lines.append(f"--- Turn {i} ---")
            lines.append(f"Q: {q}")
            lines.append(f"A: {a}\n")

        return "\n".join(lines)

    @mcp.tool()
    async def chat_clear(notebook_id: str) -> str:
        """Clear the active conversation for a notebook.

        Removes the stored conversation state so the next chat_ask
        starts a fresh conversation.

        Args:
            notebook_id: The ID of the notebook.

        Returns:
            Confirmation that the conversation was cleared.
        """
        if notebook_id not in _active_conversations:
            return "No active conversation for this notebook."

        conversation_id = _active_conversations.pop(notebook_id)

        # Try to clear server-side cache if available
        client = await get_client()
        try:
            await client.chat.clear_cache(notebook_id)
        except (AttributeError, Exception):
            pass  # Not all library versions support this

        return (
            f"Conversation cleared for notebook {notebook_id}.\n"
            f"  Previous conversation ID: {conversation_id}\n"
            f"Next chat_ask will start a fresh conversation."
        )
