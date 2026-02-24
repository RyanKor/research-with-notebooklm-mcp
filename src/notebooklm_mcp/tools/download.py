"""Download/export tools for generated artifacts."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from notebooklm_mcp.client import get_client


# Default download directory
DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/notebooklm-downloads")


def register(mcp: FastMCP) -> None:
    """Register download tools."""

    @mcp.tool()
    async def download_artifact(
        notebook_id: str,
        artifact_type: str,
        output_path: str | None = None,
        output_format: str | None = None,
    ) -> str:
        """Download a generated artifact from a notebook.

        Args:
            notebook_id: The ID of the notebook.
            artifact_type: Type of artifact to download. One of:
                - "audio" (MP3)
                - "video" (MP4)
                - "report" (Markdown)
                - "quiz" (JSON/Markdown/HTML)
                - "flashcards" (JSON/Markdown/HTML)
                - "slide_deck" (PDF)
                - "infographic" (PNG)
                - "mind_map" (JSON)
                - "data_table" (CSV)
            output_path: Optional file path to save to. If not provided,
                        saves to ~/notebooklm-downloads/ with auto-generated name.
            output_format: For quiz/flashcards: "json", "markdown", or "html".
                          Defaults to "json".

        Returns:
            Path to the downloaded file.
        """
        client = await get_client()

        # Determine output path
        if not output_path:
            os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)
            ext_map = {
                "audio": "mp3",
                "video": "mp4",
                "report": "md",
                "quiz": output_format or "json",
                "flashcards": output_format or "json",
                "slide_deck": "pdf",
                "infographic": "png",
                "mind_map": "json",
                "data_table": "csv",
            }
            ext = ext_map.get(artifact_type, "bin")
            if ext in ("json", "markdown", "html"):
                ext_file = {"json": "json", "markdown": "md", "html": "html"}[ext]
            else:
                ext_file = ext
            output_path = os.path.join(
                DEFAULT_DOWNLOAD_DIR, f"{artifact_type}_{notebook_id[:8]}.{ext_file}"
            )

        # Download based on type
        download_methods = {
            "audio": lambda: client.artifacts.download_audio(notebook_id, output_path),
            "video": lambda: client.artifacts.download_video(notebook_id, output_path),
            "report": lambda: client.artifacts.download_report(
                notebook_id, output_path
            ),
            "quiz": lambda: client.artifacts.download_quiz(
                notebook_id, output_path, output_format=output_format or "json"
            ),
            "flashcards": lambda: client.artifacts.download_flashcards(
                notebook_id, output_path, output_format=output_format or "json"
            ),
            "slide_deck": lambda: client.artifacts.download_slide_deck(
                notebook_id, output_path
            ),
            "infographic": lambda: client.artifacts.download_infographic(
                notebook_id, output_path
            ),
            "mind_map": lambda: client.artifacts.download_mind_map(
                notebook_id, output_path
            ),
            "data_table": lambda: client.artifacts.download_data_table(
                notebook_id, output_path
            ),
        }

        method = download_methods.get(artifact_type)
        if not method:
            return (
                f"Unknown artifact type: {artifact_type}. "
                f"Valid types: {', '.join(download_methods.keys())}"
            )

        saved_path = await method()
        return f"Artifact downloaded successfully.\n  Type: {artifact_type}\n  Path: {saved_path}"

    @mcp.tool()
    async def list_artifacts(
        notebook_id: str,
        artifact_type: str | None = None,
    ) -> str:
        """List all generated artifacts in a notebook.

        Args:
            notebook_id: The ID of the notebook.
            artifact_type: Optional filter by type (e.g., "audio", "report", "quiz").

        Returns:
            List of artifacts with their IDs and types.
        """
        client = await get_client()

        if artifact_type:
            from notebooklm import ArtifactType

            type_map = {
                "audio": ArtifactType.AUDIO,
                "video": ArtifactType.VIDEO,
                "report": ArtifactType.REPORT,
                "quiz": ArtifactType.QUIZ,
                "flashcards": ArtifactType.FLASHCARDS,
                "slide_deck": ArtifactType.SLIDE_DECK,
                "infographic": ArtifactType.INFOGRAPHIC,
                "mind_map": ArtifactType.MIND_MAP,
                "data_table": ArtifactType.DATA_TABLE,
            }
            at = type_map.get(artifact_type)
            artifacts = await client.artifacts.list(notebook_id, artifact_type=at)
        else:
            artifacts = await client.artifacts.list(notebook_id)

        if not artifacts:
            return "No artifacts found. Generate some with generate_* tools."

        lines = [f"Found {len(artifacts)} artifact(s):\n"]
        for art in artifacts:
            lines.append(f"  - [{art.id}] type={art.artifact_type}, title={art.title}")
        return "\n".join(lines)
