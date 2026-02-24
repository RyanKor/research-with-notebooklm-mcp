"""MCP Prompts for NotebookLM research workflows."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register MCP prompts for guided research workflows."""

    @mcp.prompt()
    def research_deep_dive(topic: str, num_sources: int = 3) -> str:
        """Guide an in-depth research session on a topic.

        Args:
            topic: The research topic to investigate.
            num_sources: Number of initial sources to find.
        """
        return (
            f"I want to conduct a deep research session on: {topic}\n\n"
            f"Please follow these steps:\n"
            f"1. Create a new notebook titled 'Research: {topic}'\n"
            f"2. Search the web for {num_sources} high-quality sources on this topic "
            f"using research_web with mode='deep'\n"
            f"3. Add any additional relevant URLs as sources\n"
            f"4. Ask comprehensive questions to extract key insights:\n"
            f"   - What are the main themes and findings?\n"
            f"   - What are the different perspectives or approaches?\n"
            f"   - What are the key data points or evidence?\n"
            f"   - What are the gaps or limitations?\n"
            f"5. Generate a briefing document report\n"
            f"6. Summarize the key findings for me\n\n"
            f"Start by creating the notebook and running web research."
        )

    @mcp.prompt()
    def comparative_analysis(
        topic: str,
        source_urls: str,
    ) -> str:
        """Guide a comparative analysis across multiple sources.

        Args:
            topic: The topic/question for comparison.
            source_urls: Comma-separated URLs to compare.
        """
        urls = [u.strip() for u in source_urls.split(",")]
        url_list = "\n".join(f"   - {u}" for u in urls)

        return (
            f"I want to do a comparative analysis on: {topic}\n\n"
            f"Sources to compare:\n{url_list}\n\n"
            f"Steps:\n"
            f"1. Create a notebook for this analysis\n"
            f"2. Add all {len(urls)} URLs as sources\n"
            f"3. Ask these comparison questions:\n"
            f"   - What are the similarities across these sources?\n"
            f"   - What are the key differences?\n"
            f"   - Where do they agree and disagree?\n"
            f"   - What unique insights does each source provide?\n"
            f"4. Generate a data table comparing key aspects\n"
            f"5. Generate a mind map of the relationships\n"
            f"6. Create a briefing document with the comparison\n\n"
            f"Start by creating the notebook and adding the sources."
        )

    @mcp.prompt()
    def content_brief(
        topic: str,
        content_type: str = "blog_post",
    ) -> str:
        """Guide content creation from research sources.

        Args:
            topic: The topic for content creation.
            content_type: Type of content - "blog_post", "report", "presentation".
        """
        return (
            f"I want to create a {content_type} about: {topic}\n\n"
            f"Steps:\n"
            f"1. Create a research notebook for '{topic}'\n"
            f"2. Run web research to find authoritative sources\n"
            f"3. Analyze the sources with Q&A to extract key points\n"
            f"4. Generate a {content_type} report from the sources\n"
            f"5. Also generate:\n"
            f"   - A mind map for structure overview\n"
            f"   - Key flashcards for quick reference\n"
            f"6. Download all generated artifacts\n\n"
            f"Start with research and then generate the content."
        )

    @mcp.prompt()
    def rag_setup(
        knowledge_base_name: str,
        source_urls: str = "",
    ) -> str:
        """Set up a RAG knowledge base notebook for ongoing Q&A.

        Args:
            knowledge_base_name: Name for the knowledge base.
            source_urls: Optional comma-separated URLs to pre-load.
        """
        setup_steps = (
            f"I want to set up a RAG knowledge base called: {knowledge_base_name}\n\n"
            f"Steps:\n"
            f"1. Create a notebook titled '{knowledge_base_name}'\n"
        )

        if source_urls:
            urls = [u.strip() for u in source_urls.split(",")]
            url_list = "\n".join(f"   - {u}" for u in urls)
            setup_steps += f"2. Add these initial sources:\n{url_list}\n"
        else:
            setup_steps += "2. (No initial sources - I'll add them later)\n"

        setup_steps += (
            f"3. Configure the chat persona for Q&A:\n"
            f"   - Set a custom prompt for accurate, citation-heavy responses\n"
            f"4. Test with a sample question to verify it's working\n"
            f"5. Return the notebook ID so I can use it for future Q&A\n\n"
            f"This notebook will be used as a persistent RAG backend. "
            f"I'll query it using chat_ask for source-grounded answers."
        )

        return setup_steps
