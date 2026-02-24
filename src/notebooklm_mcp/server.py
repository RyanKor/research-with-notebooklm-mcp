"""NotebookLM MCP Server - Main entry point.

Provides NotebookLM capabilities as MCP tools for AI agents.
Supports stdio (Claude Code) and SSE (web clients) transports.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import close_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manage server lifecycle - cleanup on shutdown."""
    logger.info("NotebookLM MCP Server starting...")
    try:
        yield {}
    finally:
        logger.info("NotebookLM MCP Server shutting down...")
        await close_client()


# Create the MCP server
mcp = FastMCP(
    "NotebookLM Research",
    instructions=(
        "Research, RAG, and Content Generation with Google NotebookLM. "
        "Add sources (URLs, PDFs, YouTube), ask questions with citations, "
        "run web research, and generate reports, podcasts, quizzes, and more."
    ),
    lifespan=server_lifespan,
)

# Register all tools
from notebooklm_mcp.tools import notebook, source, chat, research, generate, download, pipeline

notebook.register(mcp)
source.register(mcp)
chat.register(mcp)
research.register(mcp)
generate.register(mcp)
download.register(mcp)
pipeline.register(mcp)

# Register prompts
from notebooklm_mcp.prompts import register_prompts

register_prompts(mcp)

# Register resources
from notebooklm_mcp.resources import register_resources

register_resources(mcp)


def main():
    """Run the MCP server (stdio transport for Claude Code)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # MCP uses stdout for protocol, logs go to stderr
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
