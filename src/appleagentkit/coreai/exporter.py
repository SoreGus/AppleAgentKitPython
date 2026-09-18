from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from appleagentkit.artifact.manifest import ArtifactManifest
from appleagentkit.config.loader import Settings
from appleagentkit.coreai.tooling import CoreAITooling
from appleagentkit.process.runner import CommandRunner


@dataclass(frozen=True, slots=True)
class ExportRequest:
    model: str
    platform: str
    compression: str | None
    max_context_length: int | None
    output_dir: Path
    experimental: bool = False
    include_debug_info: bool = False
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class CoreAIExporter:
    settings: Settings
    tooling: CoreAITooling
    runner: CommandRunner

    def export(
        self,
        request: ExportRequest,
    ) -> ArtifactManifest:
        request.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = [
            str(self.tooling.llm_export),
            request.model,
            "--platform",
            request.platform,
            "--output-dir",
            str(request.output_dir),
        ]

        if request.compression:
            command.extend(
                [
                    "--compression",
                    request.compression,
                ]
            )

        if request.max_context_length is not None:
            command.extend(
                [
                    "--max-context-length",
                    str(request.max_context_length),
                ]
            )

        if request.experimental:
            command.append("--experimental")

        if request.include_debug_info:
            command.append("--include-debug-info")

        if request.dry_run:
            command.append("--dry-run")

        environment = self._environment()

        self.runner.run(
            command,
            cwd=self.settings.project_root,
            environment=environment,
        )

        manifest = ArtifactManifest.create(
            export_root=request.output_dir,
            model=request.model,
            platform=request.platform,
            compression=request.compression,
            max_context_length=request.max_context_length,
            dry_run=request.dry_run,
            command=command,
        )

        if not request.dry_run:
            manifest.write()

        return manifest

    def _environment(self) -> dict[str, str]:
        environment = {
            "HF_HOME": str(
                self.settings.cache_dir / "huggingface"
            )
        }

        if self.settings.hf_token:
            environment["HF_TOKEN"] = self.settings.hf_token

        return environment
