"""Source comparison tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register source comparison tools."""

    @mcp.tool()
    async def source_compare(
        notebook_id: str,
        source_ids: list[str],
        aspect: str | None = None,
    ) -> str:
        """Compare multiple sources in a notebook side by side.

        Uses NotebookLM's RAG capabilities to analyze commonalities,
        differences, and unique contributions of each source.

        Args:
            notebook_id: The ID of the notebook.
            source_ids: List of source IDs to compare (minimum 2).
            aspect: Optional specific aspect to focus the comparison on
                   (e.g., "methodology", "conclusions", "data sources").

        Returns:
            Structured comparison of the sources.
        """
        if len(source_ids) < 2:
            return "Error: At least 2 source IDs are required for comparison."

        # Build comparison prompt
        if aspect:
            prompt = (
                f"Compare the following {len(source_ids)} sources, "
                f"focusing specifically on: {aspect}.\n\n"
                f"Structure your response as:\n"
                f"1. **Overview**: Brief description of each source\n"
                f"2. **Commonalities**: What the sources share regarding {aspect}\n"
                f"3. **Differences**: Key differences regarding {aspect}\n"
                f"4. **Unique Contributions**: What each source uniquely offers\n"
                f"5. **Synthesis**: Overall assessment"
            )
        else:
            prompt = (
                f"Compare the following {len(source_ids)} sources comprehensively.\n\n"
                f"Structure your response as:\n"
                f"1. **Overview**: Brief description of each source\n"
                f"2. **Commonalities**: Shared themes, arguments, or findings\n"
                f"3. **Differences**: Key disagreements or different perspectives\n"
                f"4. **Unique Contributions**: What each source uniquely offers\n"
                f"5. **Synthesis**: Overall assessment and how they complement each other"
            )

        client = await get_client()
        result = await client.chat.ask(
            notebook_id, prompt, source_ids=source_ids
        )

        response_parts = [
            f"Source Comparison ({len(source_ids)} sources):\n",
            result.answer,
        ]

        if hasattr(result, "references") and result.references:
            response_parts.append("\nReferences:")
            for ref in result.references:
                response_parts.append(f"  - {ref}")

        return "\n".join(response_parts)
