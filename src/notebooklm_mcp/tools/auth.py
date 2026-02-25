"""Authentication management tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register authentication tools."""

    @mcp.tool()
    async def auth_check() -> str:
        """Check if NotebookLM authentication is valid and working.

        Performs a lightweight API call (listing notebooks) to verify
        that the current credentials are valid.

        Returns:
            Authentication status and account info.
        """
        try:
            client = await get_client()
            notebooks = await client.notebooks.list()
            return (
                f"Authentication is valid.\n"
                f"  Status: Connected\n"
                f"  Notebooks accessible: {len(notebooks)}"
            )
        except RuntimeError as e:
            return f"Authentication failed.\n  Error: {e}"

    @mcp.tool()
    async def auth_refresh() -> str:
        """Refresh the NotebookLM authentication token.

        Forces a token refresh to resolve authentication issues.
        The notebooklm-py library handles token refresh automatically,
        but this tool allows explicit refresh when needed.

        Returns:
            Confirmation of token refresh.
        """
        try:
            client = await get_client()
            await client.refresh_auth()
            return "Authentication token refreshed successfully."
        except RuntimeError as e:
            return f"Failed to refresh authentication.\n  Error: {e}"
        except AttributeError:
            # If refresh_auth is not available, reconnect
            from notebooklm_mcp.client import close_client

            await close_client()
            try:
                client = await get_client()
                return "Authentication refreshed by reconnecting."
            except RuntimeError as e:
                return f"Failed to refresh authentication.\n  Error: {e}"
