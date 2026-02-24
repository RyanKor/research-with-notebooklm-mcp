"""Shared NotebookLM client management.

Provides a singleton-like async client that tools can share.
The client is initialized once and reused across all tool invocations.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from notebooklm import NotebookLMClient

logger = logging.getLogger(__name__)

# Global client instance
_client: NotebookLMClient | None = None


async def get_client() -> NotebookLMClient:
    """Get or create the shared NotebookLM client.

    Returns:
        Connected NotebookLMClient instance.

    Raises:
        RuntimeError: If authentication is not set up (run `notebooklm login` first).
    """
    global _client

    if _client is not None and _client.is_connected:
        return _client

    try:
        _client = await NotebookLMClient.from_storage()
        await _client.__aenter__()
        logger.info("NotebookLM client connected successfully")
        return _client
    except FileNotFoundError:
        raise RuntimeError(
            "NotebookLM authentication not found. "
            "Run `notebooklm login` first to authenticate with Google."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to connect to NotebookLM: {e}")


async def close_client() -> None:
    """Close the shared client connection."""
    global _client
    if _client is not None:
        try:
            await _client.__aexit__(None, None, None)
        except Exception:
            pass
        _client = None
        logger.info("NotebookLM client closed")


@asynccontextmanager
async def client_lifespan() -> AsyncIterator[None]:
    """Context manager for client lifecycle (used with MCP server lifespan)."""
    yield
    await close_client()
