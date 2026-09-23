from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

from appleagentkit.artifact.manifest import ArtifactManifest
from appleagentkit.artifact.store import ArtifactStore
from appleagentkit.config.loader import Settings
from appleagentkit.coreai.registry import CoreAIModelRegistry
from appleagentkit.coreai.resources import resolve_coreai_resource
from appleagentkit.coreai.tooling import CoreAITooling
from appleagentkit.process.runner import (
    CommandExecutionError,
    CommandResult,
    CommandRunner,
)


@dataclass(frozen=True, slots=True)
class ExportRequest:
    model: str
    platform: str
    max_context_length: int | None = None
    compression: str | None = None
    compression_config: Path | None = None
    experimental: bool = False
    include_debug_info: bool = False
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class CoreAIExporter:
    settings: Settings
    tooling: CoreAITooling
    registry: CoreAIModelRegistry
    store: ArtifactStore
    runner: CommandRunner

    def export(
        self,
        request: ExportRequest,
    ) -> ArtifactManifest | None:
        preset = self.registry.resolve(
            request.model,
            platform=request.platform,
        )

        if preset is None and not request.experimental:
            platforms = self.registry.platforms_for(
                request.model
            )

            suffix = (
                f" Available platforms: {', '.join(platforms)}."
                if platforms
                else ""
            )

            raise RuntimeError(
                f"'{request.model}' is not registered for "
                f"{request.platform}.{suffix} "
                "Use --experimental only for an unregistered model "
                "whose Core AI Python implementation exists."
            )

        export_root = self.store.variant_root(
            request.model,
            request.platform,
        )

        export_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = self.tooling.command(
            "coreai.llm.export",
            request.model,
            "--platform",
            request.platform,
            "--output-dir",
            str(export_root),
        )

        if request.max_context_length is not None:
            command.extend(
                [
                    "--max-context-length",
                    str(request.max_context_length),
                ]
            )

        if request.compression is not None:
            command.extend(
                [
                    "--compression",
                    request.compression,
                ]
            )

        if request.compression_config is not None:
            command.extend(
                [
                    "--compression-config",
                    str(
                        request.compression_config.resolve()
                    ),
                ]
            )

        if request.experimental:
            command.append(
                "--experimental"
            )

        if request.include_debug_info:
            command.append(
                "--include-debug-info"
            )

        if request.dry_run:
            command.append(
                "--dry-run"
            )

        executed_command = self._run_export_command(
            command,
            request=request,
        )

        if request.dry_run:
            return None

        build = ArtifactManifest.create(
            export_root=export_root,
            model=request.model,
            base_model=(
                preset.hf_id
                if preset is not None
                else None
            ),
            platform=request.platform,
            command=executed_command,
        )

        build.write()

        self.store.register_variant(
            build
        )

        return build

    def _run_export_command(
        self,
        command: list[str],
        *,
        request: ExportRequest,
    ) -> list[str]:
        try:
            result = self.runner.capture(
                command,
                cwd=self.settings.project_root,
                environment=self._environment(),
            )

            self._emit_output(result)

            return command

        except CommandExecutionError as error:
            if request.compression_config is not None:
                raise

            relative_resource = (
                self._missing_registry_resource(
                    error.result
                )
            )

            if relative_resource is None:
                raise

            resource = resolve_coreai_resource(
                relative_resource
            )

            retry_command = [
                *command,
                "--compression-config",
                str(resource),
            ]

            print(
                "[INFO] Core AI registry resource resolved: "
                f"{relative_resource}"
            )

            self.runner.run(
                retry_command,
                cwd=self.settings.project_root,
                environment=self._environment(),
            )

            return retry_command

    def _missing_registry_resource(
        self,
        result: CommandResult,
    ) -> str | None:
        output = "\n".join(
            part
            for part in (
                result.stdout,
                result.stderr,
            )
            if part
        )

        match = re.search(
            r"Registry preset references\s+"
            r"([^\s,]+\.ya?ml)",
            output,
        )

        if match is None:
            return None

        return match.group(1)

    def _emit_output(
        self,
        result: CommandResult,
    ) -> None:
        if result.stdout:
            print(
                result.stdout,
                end="",
                file=sys.stdout,
            )

        if result.stderr:
            print(
                result.stderr,
                end="",
                file=sys.stderr,
            )

    def _environment(
        self,
    ) -> dict[str, str]:
        huggingface_cache = (
            self.settings.cache_dir
            / "huggingface"
        )

        huggingface_cache.mkdir(
            parents=True,
            exist_ok=True,
        )

        environment = {
            "HF_HUB_CACHE": str(
                huggingface_cache
            ),
        }

        if self.settings.hf_token:
            environment["HF_TOKEN"] = (
                self.settings.hf_token
            )

        return environment