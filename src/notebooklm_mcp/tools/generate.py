"""Content generation tools."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:
    """Register content generation tools."""

    @mcp.tool()
    async def generate_report(
        notebook_id: str,
        report_format: str = "briefing_doc",
        language: str = "en",
        custom_prompt: str | None = None,
        wait: bool = True,
    ) -> str:
        """Generate a report/document from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            report_format: Report type - one of: "briefing_doc", "study_guide",
                          "blog_post", "custom". Use "custom" with custom_prompt.
            language: Language code (e.g., "en", "ko", "ja").
            custom_prompt: Custom instructions for report generation (used with "custom" format).
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status with task ID for polling/downloading.
        """
        from notebooklm import ReportFormat

        format_map = {
            "briefing_doc": ReportFormat.BRIEFING_DOC,
            "study_guide": ReportFormat.STUDY_GUIDE,
            "blog_post": ReportFormat.BLOG_POST,
            "custom": ReportFormat.CUSTOM,
        }
        fmt = format_map.get(report_format, ReportFormat.BRIEFING_DOC)

        client = await get_client()
        status = await client.artifacts.generate_report(
            notebook_id,
            report_format=fmt,
            language=language,
            custom_prompt=custom_prompt,
        )

        if not wait:
            return (
                f"Report generation started.\n"
                f"  Task ID: {status.task_id}\n"
                f"  Format: {report_format}\n\n"
                f"Use generation_status to check progress, or download_artifact when ready."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=300.0
        )

        return (
            f"Report generated successfully.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Format: {report_format}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact to download the report."
        )

    @mcp.tool()
    async def generate_audio(
        notebook_id: str,
        instructions: str | None = None,
        language: str = "en",
        audio_format: str | None = None,
        audio_length: str | None = None,
        wait: bool = True,
    ) -> str:
        """Generate an audio overview (podcast) from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Custom instructions for audio generation
                         (e.g., "make it engaging and conversational").
            language: Language code (e.g., "en", "ko", "ja").
            audio_format: Format - "deep_dive", "brief", "critique", or "debate".
            audio_length: Length - "short", "medium", or "long".
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status. Audio generation takes 2-5 minutes.
        """
        from notebooklm import AudioFormat, AudioLength

        kwargs: dict = {
            "language": language,
        }
        if instructions:
            kwargs["instructions"] = instructions
        if audio_format:
            fmt_map = {
                "deep_dive": AudioFormat.DEEP_DIVE,
                "brief": AudioFormat.BRIEF,
                "critique": AudioFormat.CRITIQUE,
                "debate": AudioFormat.DEBATE,
            }
            kwargs["audio_format"] = fmt_map.get(audio_format)
        if audio_length:
            len_map = {
                "short": AudioLength.SHORT,
                "medium": AudioLength.DEFAULT,
                "long": AudioLength.LONG,
            }
            kwargs["audio_length"] = len_map.get(audio_length)

        client = await get_client()
        status = await client.artifacts.generate_audio(notebook_id, **kwargs)

        if not wait:
            return (
                f"Audio generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Audio takes 2-5 minutes. Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=600.0
        )

        return (
            f"Audio overview generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='audio' to download."
        )

    @mcp.tool()
    async def generate_quiz(
        notebook_id: str,
        instructions: str | None = None,
        quantity: str | None = None,
        difficulty: str | None = None,
        wait: bool = True,
    ) -> str:
        """Generate a quiz from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Custom instructions for quiz generation.
            quantity: Number of questions - "fewer", "default", or "more".
            difficulty: Difficulty level - "easy", "medium", or "hard".
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status with task ID.
        """
        from notebooklm import QuizDifficulty, QuizQuantity

        kwargs: dict = {}
        if instructions:
            kwargs["instructions"] = instructions
        if quantity:
            q_map = {
                "fewer": QuizQuantity.FEWER,
                "standard": QuizQuantity.STANDARD,
            }
            kwargs["quantity"] = q_map.get(quantity)
        if difficulty:
            d_map = {
                "easy": QuizDifficulty.EASY,
                "medium": QuizDifficulty.MEDIUM,
                "hard": QuizDifficulty.HARD,
            }
            kwargs["difficulty"] = d_map.get(difficulty)

        client = await get_client()
        status = await client.artifacts.generate_quiz(notebook_id, **kwargs)

        if not wait:
            return (
                f"Quiz generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=300.0
        )

        return (
            f"Quiz generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='quiz' to download (JSON/Markdown/HTML)."
        )

    @mcp.tool()
    async def generate_mindmap(notebook_id: str) -> str:
        """Generate a mind map from notebook sources.

        Args:
            notebook_id: The ID of the notebook.

        Returns:
            Mind map data in JSON format (hierarchical structure).
        """
        import json

        client = await get_client()
        result = await client.artifacts.generate_mind_map(notebook_id)

        if isinstance(result, dict):
            return f"Mind map generated:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
        return f"Mind map generated:\n{result}"

    @mcp.tool()
    async def generate_flashcards(
        notebook_id: str,
        instructions: str | None = None,
        quantity: str | None = None,
        difficulty: str | None = None,
        wait: bool = True,
    ) -> str:
        """Generate flashcards from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Custom instructions for flashcard generation.
            quantity: Number of flashcards - "fewer", "default", or "more".
            difficulty: Difficulty level - "easy", "medium", or "hard".
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status with task ID.
        """
        from notebooklm import QuizDifficulty, QuizQuantity

        kwargs: dict = {}
        if instructions:
            kwargs["instructions"] = instructions
        if quantity:
            q_map = {
                "fewer": QuizQuantity.FEWER,
                "standard": QuizQuantity.STANDARD,
            }
            kwargs["quantity"] = q_map.get(quantity)
        if difficulty:
            d_map = {
                "easy": QuizDifficulty.EASY,
                "medium": QuizDifficulty.MEDIUM,
                "hard": QuizDifficulty.HARD,
            }
            kwargs["difficulty"] = d_map.get(difficulty)

        client = await get_client()
        status = await client.artifacts.generate_flashcards(notebook_id, **kwargs)

        if not wait:
            return (
                f"Flashcard generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=300.0
        )

        return (
            f"Flashcards generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='flashcards' to download."
        )

    @mcp.tool()
    async def generate_slides(
        notebook_id: str,
        instructions: str | None = None,
        language: str = "en",
        wait: bool = True,
    ) -> str:
        """Generate a slide deck from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Custom instructions for slide generation.
            language: Language code (e.g., "en", "ko").
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status with task ID.
        """
        client = await get_client()
        kwargs: dict = {"language": language}
        if instructions:
            kwargs["instructions"] = instructions

        status = await client.artifacts.generate_slide_deck(notebook_id, **kwargs)

        if not wait:
            return (
                f"Slide deck generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=300.0
        )

        return (
            f"Slide deck generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='slide_deck' to download as PDF."
        )

    @mcp.tool()
    async def generate_video(
        notebook_id: str,
        instructions: str | None = None,
        language: str = "en",
        style: str | None = None,
        wait: bool = True,
    ) -> str:
        """Generate a video overview from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Custom instructions for video generation.
            language: Language code.
            style: Visual style - "classic", "whiteboard", "kawaii", "anime", etc.
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status. Video generation takes several minutes.
        """
        from notebooklm import VideoStyle

        kwargs: dict = {"language": language}
        if instructions:
            kwargs["instructions"] = instructions
        if style:
            style_map = {
                "classic": VideoStyle.CLASSIC,
                "whiteboard": VideoStyle.WHITEBOARD,
            }
            # Try to map known styles, fall back to CLASSIC
            kwargs["video_style"] = style_map.get(style, VideoStyle.CLASSIC)

        client = await get_client()
        status = await client.artifacts.generate_video(notebook_id, **kwargs)

        if not wait:
            return (
                f"Video generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Video takes several minutes. Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=600.0
        )

        return (
            f"Video overview generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='video' to download."
        )

    @mcp.tool()
    async def generate_infographic(
        notebook_id: str,
        instructions: str | None = None,
        language: str = "en",
        orientation: str | None = None,
        wait: bool = True,
    ) -> str:
        """Generate an infographic from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Custom instructions for infographic generation.
            language: Language code.
            orientation: Orientation - "portrait", "landscape", or "square".
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status with task ID.
        """
        from notebooklm import InfographicOrientation

        kwargs: dict = {"language": language}
        if instructions:
            kwargs["instructions"] = instructions
        if orientation:
            o_map = {
                "portrait": InfographicOrientation.PORTRAIT,
                "landscape": InfographicOrientation.LANDSCAPE,
                "square": InfographicOrientation.SQUARE,
            }
            kwargs["orientation"] = o_map.get(orientation)

        client = await get_client()
        status = await client.artifacts.generate_infographic(notebook_id, **kwargs)

        if not wait:
            return (
                f"Infographic generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=300.0
        )

        return (
            f"Infographic generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='infographic' to download as PNG."
        )

    @mcp.tool()
    async def generate_data_table(
        notebook_id: str,
        instructions: str | None = None,
        language: str = "en",
        wait: bool = True,
    ) -> str:
        """Generate a data table from notebook sources.

        Args:
            notebook_id: The ID of the notebook.
            instructions: Natural language instructions describing the desired table
                         structure (e.g., "compare key concepts across papers").
            language: Language code.
            wait: If True (default), wait for completion. If False, return task ID immediately.

        Returns:
            Generation status with task ID.
        """
        client = await get_client()
        kwargs: dict = {"language": language}
        if instructions:
            kwargs["instructions"] = instructions

        status = await client.artifacts.generate_data_table(notebook_id, **kwargs)

        if not wait:
            return (
                f"Data table generation started.\n"
                f"  Task ID: {status.task_id}\n\n"
                f"Use generation_status to check progress."
            )

        final = await client.artifacts.wait_for_completion(
            notebook_id, status.task_id, timeout=300.0
        )

        return (
            f"Data table generated.\n"
            f"  Task ID: {status.task_id}\n"
            f"  Status: {final.status}\n\n"
            f"Use download_artifact with type='data_table' to download as CSV."
        )

    @mcp.tool()
    async def generation_status(notebook_id: str, task_id: str) -> str:
        """Check the status of an ongoing generation task.

        Use this to poll the progress of a non-blocking generation
        (started with wait=False).

        Args:
            notebook_id: The ID of the notebook.
            task_id: The task ID returned by a generate_* tool.

        Returns:
            Current status of the generation task.
        """
        client = await get_client()

        try:
            artifacts = await client.artifacts.list(notebook_id)
            for artifact in artifacts:
                if hasattr(artifact, "task_id") and artifact.task_id == task_id:
                    return (
                        f"Generation task status:\n"
                        f"  Task ID: {task_id}\n"
                        f"  Type: {getattr(artifact, 'artifact_type', 'unknown')}\n"
                        f"  Status: {getattr(artifact, 'status', 'unknown')}"
                    )
        except Exception as e:
            logger.debug(f"Artifact list check failed: {e}")

        # Fallback: try wait_for_completion with a short timeout
        try:
            final = await client.artifacts.wait_for_completion(
                notebook_id, task_id, timeout=5.0
            )
            return (
                f"Generation task status:\n"
                f"  Task ID: {task_id}\n"
                f"  Status: {final.status}"
            )
        except TimeoutError:
            return (
                f"Generation task status:\n"
                f"  Task ID: {task_id}\n"
                f"  Status: still in progress\n\n"
                f"Try again later or use download_artifact when ready."
            )
        except Exception as e:
            return (
                f"Generation task status:\n"
                f"  Task ID: {task_id}\n"
                f"  Status: unknown (error checking: {e})"
            )
