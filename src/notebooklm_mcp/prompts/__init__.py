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
    def multi_persona_research(
        topic: str,
        num_personas: int = 4,
        language: str = "ko",
    ) -> str:
        """Guide a multi-persona research session with diverse expert perspectives.

        Args:
            topic: The research topic to investigate from multiple angles.
            num_personas: Number of personas to use (1-4, default 4).
            language: Language for analysis — "ko", "en", etc. (default "ko").
        """
        return (
            f"'{topic}'에 대해 멀티 페르소나 기반 심층 리서치를 수행합니다.\n\n"
            f"이 워크플로우는 동일한 주제를 서로 다른 전문가 관점에서 분석하여\n"
            f"편향을 줄이고 다각적 인사이트를 도출합니다.\n\n"
            f"Steps:\n"
            f"1. persona_recommend(topic='{topic}', max_personas={num_personas}, language='{language}')로\n"
            f"   최적의 페르소나 조합을 추천받으세요\n"
            f"2. 추천 결과를 검토하고, 필요시 페르소나를 교체하거나 조정하세요\n"
            f"   (persona_list_available()로 전체 풀을 확인할 수 있습니다)\n"
            f"3. persona_setup()으로 리서치 환경을 구성하세요\n"
            f"   - 초기 URL 소스가 있다면 urls 파라미터로 전달\n"
            f"   - shared_sources=True로 모든 페르소나에 동일 소스 공유 권장\n"
            f"4. persona_query()로 핵심 질문을 다양한 전략으로 분석하세요:\n"
            f"   - strategy='independent': 모든 관점 동시 수집\n"
            f"   - strategy='cascading': 단계적 깊이 탐구\n"
            f"   - strategy='red_blue': 찬반 토론 구도\n"
            f"5. persona_synthesize()로 통합 보고서를 생성하세요:\n"
            f"   - 'comprehensive': 종합 분석 보고서\n"
            f"   - 'decision_matrix': 의사결정 매트릭스\n"
            f"   - 'debate_summary': 토론 요약\n\n"
            f"첫 단계로 persona_recommend를 실행하세요."
        )

    @mcp.prompt()
    def red_blue_analysis(
        topic: str,
        proposition: str,
        language: str = "ko",
    ) -> str:
        """Guide a Red/Blue Team analysis on a specific proposition.

        Args:
            topic: The broad research topic.
            proposition: The specific proposition/claim to debate (e.g. "NVIDIA's AI chip dominance will continue for 5+ years").
            language: Language for analysis (default "ko").
        """
        return (
            f"'{proposition}'에 대한 Red/Blue Team 분석을 수행합니다.\n"
            f"(주제 영역: {topic})\n\n"
            f"Red/Blue Team 분석은 특정 명제에 대해 지지(Blue)와 반대(Red) 관점을\n"
            f"체계적으로 대조하여 균형 잡힌 판단을 내리는 기법입니다.\n\n"
            f"Steps:\n"
            f"1. persona_recommend(topic='{topic}')로 페르소나를 추천받으세요\n"
            f"   - 추천 결과에서 [BLUE]/[RED] 배지를 확인하세요\n"
            f"   - 최소 1명의 RED와 1명의 BLUE가 포함되어야 합니다\n"
            f"2. persona_setup()으로 환경을 구성하세요\n"
            f"3. persona_query(strategy='red_blue')로 다음 질문을 분석하세요:\n"
            f"   '{proposition}'\n"
            f"4. 필요시 추가 질문으로 각 팀의 논거를 심화하세요:\n"
            f"   - Blue Team에: '가장 강력한 지지 근거 3가지는?'\n"
            f"   - Red Team에: '가장 치명적인 반론 3가지는?'\n"
            f"5. persona_synthesize(synthesis_type='debate_summary')로\n"
            f"   합의점/쟁점/미결사항을 정리하세요\n\n"
            f"첫 단계로 persona_recommend를 실행하세요."
        )

    @mcp.prompt()
    def cascading_deep_dive(
        topic: str,
        primary_focus: str = "",
        language: str = "ko",
    ) -> str:
        """Guide a cascading deep-dive research starting from the core perspective.

        Args:
            topic: The research topic.
            primary_focus: Optional primary focus area (e.g. "technical feasibility", "market opportunity").
            language: Language for analysis (default "ko").
        """
        focus_note = ""
        if primary_focus:
            focus_note = (
                f"핵심 관점: '{primary_focus}'\n"
                f"이 관점의 전문가가 첫 번째 분석을 수행하고,\n"
                f"후속 전문가들이 빈틈을 보완합니다.\n\n"
            )

        return (
            f"'{topic}'에 대한 단계적 심층 탐구(Cascading Deep-Dive)를 수행합니다.\n\n"
            f"{focus_note}"
            f"Cascading 전략은 한 전문가의 분석을 다음 전문가가 검증/보완하는\n"
            f"연쇄 분석 기법으로, 점진적으로 분석의 깊이를 더합니다.\n\n"
            f"Steps:\n"
            f"1. persona_recommend(topic='{topic}')로 페르소나를 추천받으세요\n"
            f"2. persona_setup()으로 환경을 구성하세요\n"
            f"3. persona_query(strategy='cascading')로 핵심 질문을 분석하세요\n"
            f"   - 1단계: 핵심 전문가가 초기 분석 수행\n"
            f"   - 2단계: 다음 전문가가 빈틈/대안 관점 보완\n"
            f"   - 3단계: 비판적 전문가가 리스크/약점 지적\n"
            f"   - 4단계: 통합 분석가가 전체를 종합\n"
            f"4. 필요시 persona_query(strategy='independent')로\n"
            f"   특정 세부 질문을 모든 관점에서 동시 분석\n"
            f"5. persona_synthesize(synthesis_type='comprehensive')로\n"
            f"   최종 통합 보고서를 생성하세요\n\n"
            f"첫 단계로 persona_recommend를 실행하세요."
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
