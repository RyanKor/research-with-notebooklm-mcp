"""Automated research pipeline tool."""

from __future__ import annotations

import asyncio
import json

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


def register(mcp: FastMCP) -> None:
    """Register pipeline tools."""

    @mcp.tool()
    async def research_pipeline(
        topic: str,
        urls: list[str] | None = None,
        web_research: bool = True,
        research_mode: str = "fast",
        generate_report: bool = True,
        report_format: str = "briefing_doc",
        language: str = "en",
    ) -> str:
        """Run an automated research pipeline: create notebook, add sources, research, and generate report.

        This is the all-in-one research tool that combines multiple steps:
        1. Creates a new notebook with the topic as title
        2. Adds provided URLs as sources (if any)
        3. Runs web research to discover more sources (optional)
        4. Asks NotebookLM to summarize findings
        5. Generates a report (optional)

        Args:
            topic: The research topic/question.
            urls: Optional list of URLs to add as initial sources.
            web_research: Whether to run web research for additional sources (default True).
            research_mode: Research depth - "fast" or "deep" (default "fast").
            generate_report: Whether to generate a final report (default True).
            report_format: Report type - "briefing_doc", "study_guide", "blog_post" (default "briefing_doc").
            language: Language code (default "en").

        Returns:
            Complete research results including notebook ID, sources, summary, and report status.
        """
        client = await get_client()
        results = []

        # Step 1: Create notebook
        nb = await client.notebooks.create(f"Research: {topic}")
        results.append(f"[1/5] Notebook created: {nb.title} (ID: {nb.id})")

        # Step 2: Add URL sources
        source_ids = []
        if urls:
            for url in urls:
                try:
                    src = await client.sources.add_url(nb.id, url, wait=True, wait_timeout=120.0)
                    source_ids.append(src.id)
                    results.append(f"  + Source added: {src.title} ({url})")
                except Exception as e:
                    results.append(f"  ! Failed to add {url}: {e}")

            results.append(f"[2/5] Added {len(source_ids)} source(s) from URLs")
        else:
            results.append("[2/5] No URLs provided, skipping")

        # Step 3: Web research
        if web_research:
            try:
                research_result = await client.research.start(
                    nb.id, topic, source="web", mode=research_mode
                )
                results.append(f"[3/5] Web research completed ({research_mode} mode)")
                if research_result:
                    results.append(f"  Research result: {json.dumps(research_result, default=str, ensure_ascii=False)[:500]}")
            except Exception as e:
                results.append(f"[3/5] Web research failed: {e}")
        else:
            results.append("[3/5] Web research skipped")

        # Step 4: Ask for summary
        try:
            summary_result = await client.chat.ask(
                nb.id,
                f"Based on all available sources, provide a comprehensive summary of: {topic}. "
                f"Include key findings, main themes, and important details.",
            )
            results.append(f"[4/5] Summary generated")
            results.append(f"\n--- Summary ---\n{summary_result.answer}\n--- End Summary ---")
        except Exception as e:
            results.append(f"[4/5] Summary generation failed: {e}")

        # Step 5: Generate report
        if generate_report:
            try:
                from notebooklm import ReportFormat

                format_map = {
                    "briefing_doc": ReportFormat.BRIEFING_DOC,
                    "study_guide": ReportFormat.STUDY_GUIDE,
                    "blog_post": ReportFormat.BLOG_POST,
                }
                fmt = format_map.get(report_format, ReportFormat.BRIEFING_DOC)

                status = await client.artifacts.generate_report(
                    nb.id, report_format=fmt, language=language
                )
                final = await client.artifacts.wait_for_completion(
                    nb.id, status.task_id, timeout=300.0
                )
                results.append(f"[5/5] Report generated (format: {report_format}, status: {final.status})")
                results.append(f"  Use download_artifact(notebook_id='{nb.id}', artifact_type='report') to download")
            except Exception as e:
                results.append(f"[5/5] Report generation failed: {e}")
        else:
            results.append("[5/5] Report generation skipped")

        # Final summary
        results.append(f"\n=== Pipeline Complete ===")
        results.append(f"Notebook ID: {nb.id}")
        results.append(f"Topic: {topic}")
        results.append(f"Sources: {len(source_ids)} URL(s) + web research")

        return "\n".join(results)
