"""Multi-Persona Research Agent tools.

Provides MCP tools for setting up and running multi-perspective research
using NotebookLM notebooks as persona-specific RAG backends.

Tools:
  - persona_recommend: Recommend optimal personas for a research topic
  - persona_setup: Create multi-persona notebooks in one shot
  - persona_query: Query all personas simultaneously with multiple strategies
  - persona_synthesize: Synthesize multi-persona results into unified reports
  - persona_list_sessions: List active research sessions
  - persona_get_session: Get session details
  - persona_list_available: Browse the pre-defined persona pool
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client
from notebooklm_mcp.persona_registry import (
    PERSONA_POOL,
    classify_domain,
    generate_system_prompt,
    get_persona,
    list_personas,
    recommend_personas,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session state management
# ---------------------------------------------------------------------------


@dataclass
class PersonaSession:
    """Tracks the state of a multi-persona research session."""

    session_id: str
    topic: str
    language: str
    created_at: str
    notebooks: dict[str, str]  # {persona_key: notebook_id}
    personas: dict[str, dict]  # {persona_key: persona_config}
    query_history: list[dict] = field(default_factory=list)
    last_results: dict[str, str] = field(
        default_factory=dict
    )  # {persona_key: last_answer}


# Module-level session store
_persona_sessions: dict[str, PersonaSession] = {}


def _generate_session_id() -> str:
    """Generate a short readable session ID."""
    return f"ps-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:
    """Register multi-persona research tools."""

    # === Tool 1: persona_recommend ===

    @mcp.tool()
    async def persona_recommend(
        topic: str,
        max_personas: int = 4,
        language: str = "ko",
    ) -> str:
        """Analyze a research topic and recommend optimal persona combinations (max 4).

        Examines the topic's domain (technology, business, policy, etc.) and
        recommends a diverse set of personas that provide complementary perspectives.
        Each persona comes with a customized system prompt tailored to the topic.

        Args:
            topic: The research topic/question to analyze.
            max_personas: Maximum number of personas to recommend (1-4, default 4).
            language: Language for system prompts - "ko", "en", etc. (default "ko").

        Returns:
            Recommended personas with roles, descriptions, and system prompts.
            Review the recommendations and pass them to persona_setup to create the environment.
        """
        max_personas = max(1, min(4, max_personas))
        domains = classify_domain(topic)
        recommendations = recommend_personas(
            topic, max_count=max_personas, language=language
        )

        lines = [
            f"=== Persona Recommendations for: {topic} ===\n",
            f"Detected domains: {', '.join(domains[:5])}\n",
            f"Recommended {len(recommendations)} persona(s):\n",
        ]

        for i, rec in enumerate(recommendations, 1):
            team_badge = {"red": "[RED]", "blue": "[BLUE]", "neutral": "[NEUTRAL]"}.get(
                rec["red_blue"], ""
            )
            lines.append(
                f"--- Persona {i}: {rec['name']} ({rec['name_ko']}) {team_badge} ---"
            )
            lines.append(f"  Key: {rec['key']}")
            lines.append(f"  Role: {rec['role']}")
            lines.append(f"  Description: {rec['description']}")
            lines.append(f"  Source bias: {rec['source_bias']}")
            lines.append(f"  System prompt preview: {rec['system_prompt'][:150]}...")
            lines.append("")

        lines.append("=== Next Step ===")
        lines.append(
            "Use persona_setup() with these personas to create the research environment."
        )
        lines.append("You can modify the list or swap personas before setup.")
        lines.append(f"\nAvailable persona keys: {', '.join(PERSONA_POOL.keys())}")

        return "\n".join(lines)

    # === Tool 2: persona_setup ===

    @mcp.tool()
    async def persona_setup(
        topic: str,
        persona_keys: list[str],
        urls: list[str] | None = None,
        shared_sources: bool = True,
        web_research: bool = True,
        research_mode: str = "fast",
        language: str = "ko",
    ) -> str:
        """Create a multi-persona research environment with notebooks and sources.

        Sets up everything needed for multi-perspective research:
        1. Creates a notebook for each persona (named with convention)
        2. Adds sources to all notebooks (shared) or selectively
        3. Configures each notebook with the persona's system prompt
        4. Optionally runs web research on the first notebook

        Args:
            topic: The research topic.
            persona_keys: List of persona keys to set up (e.g. ["tech_architect", "market_analyst", "devil_advocate"]).
                          Max 4 personas. Use persona_recommend to get suggestions.
            urls: Optional list of URLs to add as initial sources.
            shared_sources: If True, add the same sources to all notebooks (default True).
                           If False, sources are only added to the first notebook.
            web_research: Whether to run web research on the primary notebook (default True).
            research_mode: Research depth - "fast" or "deep" (default "fast").
            language: Language for prompts - "ko", "en", etc. (default "ko").

        Returns:
            Session ID and setup summary. Use the session_id for persona_query and persona_synthesize.
        """
        client = await get_client()
        persona_keys = persona_keys[:4]  # Enforce max 4

        # Validate persona keys
        valid_personas: list[dict] = []
        for key in persona_keys:
            persona = get_persona(key)
            if persona is None:
                return (
                    f"Error: Unknown persona key '{key}'.\n"
                    f"Available: {', '.join(PERSONA_POOL.keys())}"
                )
            valid_personas.append(
                {
                    "key": persona.key,
                    "name": persona.name,
                    "name_ko": persona.name_ko,
                    "role_ko": persona.role_ko,
                    "system_prompt": generate_system_prompt(key, topic, language),
                    "source_bias": persona.source_bias,
                    "red_blue": persona.red_blue,
                }
            )

        session_id = _generate_session_id()
        results = [f"=== Setting up Multi-Persona Research ==="]
        results.append(f"Session ID: {session_id}")
        results.append(f"Topic: {topic}")
        results.append(f"Personas: {len(valid_personas)}\n")

        # Step 1: Create notebooks for each persona
        notebooks: dict[str, str] = {}
        for p in valid_personas:
            try:
                nb = await client.notebooks.create(f"[persona:{p['key']}] {topic}")
                notebooks[p["key"]] = nb.id
                results.append(f"  [+] Notebook created: {p['name_ko']} (ID: {nb.id})")
            except Exception as e:
                results.append(
                    f"  [!] Failed to create notebook for {p['name_ko']}: {e}"
                )

        if not notebooks:
            return (
                "\n".join(results)
                + "\n\nError: No notebooks were created. Setup failed."
            )

        # Step 2: Add sources
        source_count = 0
        if urls:
            target_nbs = (
                list(notebooks.values())
                if shared_sources
                else [list(notebooks.values())[0]]
            )

            for nb_id in target_nbs:
                for url in urls:
                    try:
                        await client.sources.add_url(
                            nb_id, url, wait=True, wait_timeout=120.0
                        )
                        source_count += 1
                    except Exception as e:
                        results.append(f"  [!] Failed to add {url} to {nb_id}: {e}")

            results.append(
                f"\n  [+] Added {source_count} source(s) across {len(target_nbs)} notebook(s)"
            )
        else:
            results.append("\n  [*] No initial URLs provided")

        # Step 3: Configure chat personas
        for p in valid_personas:
            nb_id = notebooks.get(p["key"])
            if nb_id:
                try:
                    await client.chat.configure(nb_id, custom_prompt=p["system_prompt"])
                    results.append(f"  [+] Configured persona: {p['name_ko']}")
                except Exception as e:
                    results.append(f"  [!] Failed to configure {p['name_ko']}: {e}")

        # Step 4: Web research (on first notebook only to avoid rate limits)
        if web_research and notebooks:
            first_nb_id = list(notebooks.values())[0]
            try:
                await client.research.start(
                    first_nb_id, topic, source="web", mode=research_mode
                )
                results.append(f"\n  [+] Web research started ({research_mode} mode)")
            except Exception as e:
                results.append(f"\n  [!] Web research failed: {e}")

        # Save session
        session = PersonaSession(
            session_id=session_id,
            topic=topic,
            language=language,
            created_at=datetime.now(timezone.utc).isoformat(),
            notebooks=notebooks,
            personas={p["key"]: p for p in valid_personas},
        )
        _persona_sessions[session_id] = session

        results.append(f"\n=== Setup Complete ===")
        results.append(f"Session ID: {session_id}")
        results.append(f"Notebooks: {len(notebooks)}")
        results.append(
            f"\nUse persona_query(session_id='{session_id}', question='...') to start researching."
        )

        return "\n".join(results)

    # === Tool 3: persona_query ===

    @mcp.tool()
    async def persona_query(
        session_id: str,
        question: str,
        strategy: str = "independent",
        persona_keys: list[str] | None = None,
        continue_conversation: bool = False,
    ) -> str:
        """Query multiple personas simultaneously and collect diverse perspectives.

        Supports three research strategies:
        - "independent": All personas answer in parallel, results presented side-by-side
        - "cascading": Sequential deep-dive — each persona builds on the previous one's analysis
        - "red_blue": Splits personas into Blue Team (supportive) and Red Team (critical) for debate

        Args:
            session_id: The session ID from persona_setup.
            question: The research question to ask all personas.
            strategy: Query strategy — "independent", "cascading", or "red_blue" (default "independent").
            persona_keys: Optional subset of persona keys to query. If None, queries all personas in the session.
            continue_conversation: If True, continues previous conversation in each notebook.

        Returns:
            Structured multi-perspective analysis with each persona's answer and citations.
        """
        session = _persona_sessions.get(session_id)
        if not session:
            available = (
                ", ".join(_persona_sessions.keys()) if _persona_sessions else "(none)"
            )
            return f"Error: Session '{session_id}' not found. Available sessions: {available}"

        client = await get_client()

        # Determine which personas to query
        if persona_keys:
            active_personas = {
                k: session.notebooks[k] for k in persona_keys if k in session.notebooks
            }
        else:
            active_personas = session.notebooks

        if not active_personas:
            return "Error: No valid personas found for the query."

        # Dispatch based on strategy
        if strategy == "cascading":
            result = await _query_cascading(
                client, session, active_personas, question, continue_conversation
            )
        elif strategy == "red_blue":
            result = await _query_red_blue(
                client, session, active_personas, question, continue_conversation
            )
        else:  # "independent"
            result = await _query_independent(
                client, session, active_personas, question, continue_conversation
            )

        # Save to history
        session.query_history.append(
            {
                "question": question,
                "strategy": strategy,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "persona_count": len(active_personas),
            }
        )

        return result

    # === Tool 4: persona_synthesize ===

    @mcp.tool()
    async def persona_synthesize(
        session_id: str,
        synthesis_type: str = "comprehensive",
        custom_instruction: str | None = None,
        language: str = "ko",
    ) -> str:
        """Synthesize multi-persona analysis results into a unified report.

        Takes the most recent persona_query results and generates a
        structured synthesis report.

        Args:
            session_id: The session ID from persona_setup.
            synthesis_type: Report type:
                - "comprehensive": All perspectives merged into one cohesive analysis
                - "decision_matrix": Structured pro/con matrix with confidence scores
                - "debate_summary": Summarizes agreements, disagreements, and open questions
            custom_instruction: Optional additional instructions for the synthesis.
            language: Output language (default "ko").

        Returns:
            Synthesized report combining all persona perspectives.
        """
        session = _persona_sessions.get(session_id)
        if not session:
            return f"Error: Session '{session_id}' not found."

        if not session.last_results:
            return "Error: No query results to synthesize. Run persona_query first."

        client = await get_client()

        # Build synthesis prompt based on type
        synthesis_prompts = {
            "comprehensive": (
                "다음은 '{topic}'에 대해 서로 다른 전문가 관점에서 분석한 결과입니다.\n\n"
                "{persona_answers}\n\n"
                "위의 모든 관점을 종합하여 다음을 포함하는 통합 분석 보고서를 작성하세요:\n"
                "1. **핵심 합의점**: 모든 관점이 동의하는 사항\n"
                "2. **주요 쟁점**: 관점 간 의견이 갈리는 부분과 각 논거\n"
                "3. **종합 판단**: 모든 근거를 종합한 균형 잡힌 결론\n"
                "4. **추가 조사 필요 사항**: 아직 불확실하여 더 조사가 필요한 영역\n"
                "5. **실행 권고**: 현 시점에서 취할 수 있는 구체적 액션"
            ),
            "decision_matrix": (
                "다음은 '{topic}'에 대해 서로 다른 전문가 관점에서 분석한 결과입니다.\n\n"
                "{persona_answers}\n\n"
                "위의 분석을 기반으로 의사결정 매트릭스를 작성하세요:\n\n"
                "| 평가 항목 | 긍정적 근거 | 부정적 근거 | 확신도 (1-5) | 출처 |\n"
                "|-----------|------------|------------|-------------|------|\n\n"
                "매트릭스 후에 다음을 추가하세요:\n"
                "1. **총합 평가**: 전체적인 기회/위험 비율\n"
                "2. **핵심 판단 기준**: 의사결정에 가장 중요한 3가지 요소\n"
                "3. **조건부 추천**: '만약 X라면 A를, Y라면 B를' 형태의 조건부 권고"
            ),
            "debate_summary": (
                "다음은 '{topic}'에 대해 서로 다른 전문가 관점에서 분석한 결과입니다.\n\n"
                "{persona_answers}\n\n"
                "위의 다양한 관점을 토론 요약 형태로 정리하세요:\n\n"
                "## 합의 영역 (Consensus)\n"
                "모든 또는 대부분의 전문가가 동의하는 사항\n\n"
                "## 핵심 쟁점 (Key Debates)\n"
                "각 쟁점에 대해: 쟁점 설명 → 찬성 논거 → 반대 논거 → 근거 평가\n\n"
                "## 미결 사항 (Open Questions)\n"
                "현재 정보로는 결론 내리기 어려운 질문들\n\n"
                "## 종합 판정 (Verdict)\n"
                "사회자로서의 종합적 판단과 근거"
            ),
        }

        template = synthesis_prompts.get(
            synthesis_type, synthesis_prompts["comprehensive"]
        )

        # Format persona answers
        persona_answer_text = ""
        for key, answer in session.last_results.items():
            persona_info = session.personas.get(key, {})
            name = persona_info.get("name_ko", key)
            role = persona_info.get("role_ko", "")
            persona_answer_text += f"\n### [{name}] ({role})\n{answer}\n"

        synthesis_prompt = template.format(
            topic=session.topic,
            persona_answers=persona_answer_text,
        )

        if custom_instruction:
            synthesis_prompt += f"\n\n추가 지시사항: {custom_instruction}"

        # Use the first notebook to run synthesis query
        first_nb_id = list(session.notebooks.values())[0]

        # Add all persona answers as context via text source
        try:
            await client.sources.add_text(
                first_nb_id,
                f"Multi-Persona Analysis: {session.topic}",
                persona_answer_text,
                wait=True,
            )
        except Exception as e:
            logger.warning(f"Failed to add synthesis context as source: {e}")

        try:
            result = await client.chat.ask(first_nb_id, synthesis_prompt)
            answer = result.answer
        except Exception as e:
            return f"Error during synthesis: {e}"

        # Build output
        lines = [
            f"=== Synthesis Report ({synthesis_type}) ===",
            f"Topic: {session.topic}",
            f"Personas: {', '.join(session.last_results.keys())}",
            f"Based on: {len(session.query_history)} query round(s)\n",
            answer,
        ]

        return "\n".join(lines)

    # === Tool 5: persona_list_sessions ===

    @mcp.tool()
    async def persona_list_sessions() -> str:
        """List all active multi-persona research sessions.

        Returns:
            List of sessions with IDs, topics, persona counts, and creation times.
        """
        if not _persona_sessions:
            return "No active sessions. Use persona_setup to create one."

        lines = [f"Active Multi-Persona Sessions ({len(_persona_sessions)}):\n"]
        for sid, session in _persona_sessions.items():
            persona_names = [
                session.personas[k].get("name_ko", k) for k in session.notebooks
            ]
            lines.append(f"  [{sid}] {session.topic}")
            lines.append(f"    Personas: {', '.join(persona_names)}")
            lines.append(f"    Queries: {len(session.query_history)}")
            lines.append(f"    Created: {session.created_at}")
            lines.append("")

        return "\n".join(lines)

    # === Tool 6: persona_get_session ===

    @mcp.tool()
    async def persona_get_session(session_id: str) -> str:
        """Get detailed information about a multi-persona research session.

        Args:
            session_id: The session ID to inspect.

        Returns:
            Full session details including personas, notebooks, and query history.
        """
        session = _persona_sessions.get(session_id)
        if not session:
            return f"Error: Session '{session_id}' not found."

        lines = [
            f"=== Session: {session.session_id} ===",
            f"Topic: {session.topic}",
            f"Language: {session.language}",
            f"Created: {session.created_at}\n",
            "--- Personas & Notebooks ---",
        ]

        for key, nb_id in session.notebooks.items():
            p = session.personas.get(key, {})
            team = p.get("red_blue", "neutral")
            lines.append(f"  [{key}] {p.get('name_ko', key)}")
            lines.append(f"    Notebook ID: {nb_id}")
            lines.append(f"    Team: {team.upper()}")
            lines.append(f"    Source bias: {p.get('source_bias', 'N/A')}")
            lines.append("")

        if session.query_history:
            lines.append("--- Query History ---")
            for i, q in enumerate(session.query_history, 1):
                lines.append(
                    f"  {i}. [{q['strategy']}] {q['question'][:80]}... "
                    f"({q['persona_count']} personas, {q['timestamp']})"
                )
        else:
            lines.append("--- No queries yet ---")

        if session.last_results:
            lines.append("\n--- Last Results Preview ---")
            for key, answer in session.last_results.items():
                preview = answer[:200].replace("\n", " ")
                lines.append(f"  [{key}]: {preview}...")

        return "\n".join(lines)

    # === Tool 7: persona_list_available ===

    @mcp.tool()
    async def persona_list_available(domain: str | None = None) -> str:
        """Browse the pre-defined persona pool.

        Shows all available personas that can be used with persona_setup.
        Optionally filter by domain.

        Args:
            domain: Optional domain filter (e.g. "technology", "business", "academic",
                    "medical", "policy"). If None, shows all personas.

        Returns:
            List of available personas with keys, roles, and domain info.
        """
        personas = list_personas(domain)

        if not personas:
            return f"No personas found for domain '{domain}'."

        title = f"Available Personas" + (f" (domain: {domain})" if domain else " (all)")
        lines = [f"=== {title} ===\n"]

        for p in personas:
            team_badge = {"red": "[RED]", "blue": "[BLUE]", "neutral": ""}.get(
                p.red_blue, ""
            )
            domains_str = ", ".join(p.domains)
            lines.append(f"  {p.key} — {p.name_ko} ({p.name}) {team_badge}")
            lines.append(f"    {p.description_ko}")
            lines.append(f"    Domains: {domains_str}")
            lines.append("")

        lines.append(f"Total: {len(personas)} persona(s)")
        lines.append(
            f"\nAvailable domain filters: technology, engineering, business, finance, "
            f"investment, startup, academic, science, research, medical, healthcare, "
            f"policy, legal, regulation, education, social, geopolitics"
        )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Strategy implementations (private)
# ---------------------------------------------------------------------------


async def _query_independent(
    client,
    session: PersonaSession,
    active_personas: dict[str, str],
    question: str,
    continue_conversation: bool,
) -> str:
    """Independent strategy: Query all personas in parallel."""

    async def _ask_one(persona_key: str, nb_id: str) -> tuple[str, str]:
        try:
            kwargs: dict = {}
            if continue_conversation:
                # Check if there's an active conversation via the chat module
                from notebooklm_mcp.tools.chat import _active_conversations

                if nb_id in _active_conversations:
                    kwargs["conversation_id"] = _active_conversations[nb_id]

            result = await client.chat.ask(nb_id, question, **kwargs)

            # Update conversation state
            if hasattr(result, "conversation_id") and result.conversation_id:
                from notebooklm_mcp.tools.chat import _active_conversations

                _active_conversations[nb_id] = result.conversation_id

            return persona_key, result.answer
        except Exception as e:
            return persona_key, f"[Error: {e}]"

    # Run all queries in parallel
    tasks = [_ask_one(key, nb_id) for key, nb_id in active_personas.items()]
    results = await asyncio.gather(*tasks)

    # Build output
    lines = [
        f"=== Independent Analysis: {len(results)} Perspective(s) ===",
        f"Question: {question}\n",
    ]

    for persona_key, answer in results:
        p = session.personas.get(persona_key, {})
        name = p.get("name_ko", persona_key)
        role = p.get("role_ko", "")
        team = p.get("red_blue", "neutral")
        team_badge = {"red": "[RED]", "blue": "[BLUE]", "neutral": ""}.get(team, "")

        lines.append(f"{'=' * 60}")
        lines.append(f"### {name} ({role}) {team_badge}")
        lines.append(f"{'=' * 60}")
        lines.append(answer)
        lines.append("")

        # Store for later synthesis
        session.last_results[persona_key] = answer

    return "\n".join(lines)


async def _query_cascading(
    client,
    session: PersonaSession,
    active_personas: dict[str, str],
    question: str,
    continue_conversation: bool,
) -> str:
    """Cascading strategy: Sequential deep-dive with context passing."""

    persona_list = list(active_personas.items())
    lines = [
        f"=== Cascading Deep-Dive: {len(persona_list)} Stage(s) ===",
        f"Original Question: {question}\n",
    ]

    previous_answer = ""
    all_answers: dict[str, str] = {}

    for stage, (persona_key, nb_id) in enumerate(persona_list, 1):
        p = session.personas.get(persona_key, {})
        name = p.get("name_ko", persona_key)
        role = p.get("role_ko", "")

        # Build cascading prompt
        if stage == 1:
            prompt = question
        else:
            prompt = (
                f"이전 단계의 분석 결과입니다:\n"
                f"---\n{previous_answer[:2000]}\n---\n\n"
                f"당신의 전문 관점({role})에서 위 분석을 보완하고, "
                f"간과된 측면이나 다른 해석을 제시하며, "
                f"다음 질문에 답해주세요:\n\n{question}"
            )

        try:
            kwargs: dict = {}
            if continue_conversation:
                from notebooklm_mcp.tools.chat import _active_conversations

                if nb_id in _active_conversations:
                    kwargs["conversation_id"] = _active_conversations[nb_id]

            result = await client.chat.ask(nb_id, prompt, **kwargs)

            if hasattr(result, "conversation_id") and result.conversation_id:
                from notebooklm_mcp.tools.chat import _active_conversations

                _active_conversations[nb_id] = result.conversation_id

            answer = result.answer
        except Exception as e:
            answer = f"[Error at stage {stage}: {e}]"

        lines.append(f"{'=' * 60}")
        lines.append(f"### Stage {stage}: {name} ({role})")
        lines.append(f"{'=' * 60}")
        lines.append(answer)
        lines.append("")

        previous_answer = answer
        all_answers[persona_key] = answer

    # Store for synthesis
    session.last_results = all_answers

    lines.append(f"=== Cascading complete: {len(persona_list)} stages ===")
    return "\n".join(lines)


async def _query_red_blue(
    client,
    session: PersonaSession,
    active_personas: dict[str, str],
    question: str,
    continue_conversation: bool,
) -> str:
    """Red/Blue Team strategy: Split personas into opposing teams for structured debate."""

    # Classify into teams
    blue_team: dict[str, str] = {}
    red_team: dict[str, str] = {}

    for key, nb_id in active_personas.items():
        p = session.personas.get(key, {})
        team = p.get("red_blue", "neutral")
        if team == "red":
            red_team[key] = nb_id
        elif team == "blue":
            blue_team[key] = nb_id
        else:
            # Auto-assign neutrals based on source_bias
            bias = p.get("source_bias", "balanced")
            if bias in ("counter_evidence", "regulatory"):
                red_team[key] = nb_id
            else:
                blue_team[key] = nb_id

    # Ensure both teams have at least one member
    if not blue_team and red_team:
        # Move first red to blue
        first_key = next(iter(red_team))
        blue_team[first_key] = red_team.pop(first_key)
    elif not red_team and blue_team:
        # Move last blue to red
        last_key = list(blue_team.keys())[-1]
        red_team[last_key] = blue_team.pop(last_key)

    async def _ask_team(
        team: dict[str, str], team_name: str, stance: str
    ) -> list[tuple[str, str]]:
        team_prompt = (
            f"당신은 {team_name}의 일원입니다. "
            f"다음 주제에 대해 {stance}의 관점에서 분석하세요.\n\n"
            f"주제/질문: {question}\n\n"
            f"소스에 기반한 구체적 근거를 들어 {stance} 입장을 논리적으로 전개하세요. "
            f"각 논거에 확신도(높음/중간/낮음)를 표시하세요."
        )

        async def _ask_one(key: str, nb_id: str) -> tuple[str, str]:
            try:
                kwargs: dict = {}
                if continue_conversation:
                    from notebooklm_mcp.tools.chat import _active_conversations

                    if nb_id in _active_conversations:
                        kwargs["conversation_id"] = _active_conversations[nb_id]

                result = await client.chat.ask(nb_id, team_prompt, **kwargs)

                if hasattr(result, "conversation_id") and result.conversation_id:
                    from notebooklm_mcp.tools.chat import _active_conversations

                    _active_conversations[nb_id] = result.conversation_id

                return key, result.answer
            except Exception as e:
                return key, f"[Error: {e}]"

        tasks = [_ask_one(k, nid) for k, nid in team.items()]
        return await asyncio.gather(*tasks)

    # Query both teams in parallel
    blue_results, red_results = await asyncio.gather(
        _ask_team(blue_team, "Blue Team (지지 측)", "지지/긍정"),
        _ask_team(red_team, "Red Team (반대 측)", "반대/비판"),
    )

    # Build output
    lines = [
        f"=== Red/Blue Team Debate ===",
        f"Question: {question}\n",
    ]

    # Blue Team section
    lines.append(f"{'=' * 60}")
    lines.append(f"## BLUE TEAM (지지/기회 관점) — {len(blue_results)} member(s)")
    lines.append(f"{'=' * 60}")
    for key, answer in blue_results:
        p = session.personas.get(key, {})
        name = p.get("name_ko", key)
        lines.append(f"\n### [{name}]")
        lines.append(answer)
        session.last_results[key] = answer

    lines.append("")

    # Red Team section
    lines.append(f"{'=' * 60}")
    lines.append(f"## RED TEAM (반대/리스크 관점) — {len(red_results)} member(s)")
    lines.append(f"{'=' * 60}")
    for key, answer in red_results:
        p = session.personas.get(key, {})
        name = p.get("name_ko", key)
        lines.append(f"\n### [{name}]")
        lines.append(answer)
        session.last_results[key] = answer

    lines.append("")
    lines.append(f"{'=' * 60}")
    lines.append("## NEXT STEP")
    lines.append(
        f"Use persona_synthesize(session_id='{session.session_id}', synthesis_type='debate_summary') "
        f"to get a structured verdict."
    )

    return "\n".join(lines)
