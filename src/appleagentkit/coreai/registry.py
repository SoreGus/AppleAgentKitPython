from __future__ import annotations

from dataclasses import dataclass

from appleagentkit.coreai.tooling import CoreAITooling
from appleagentkit.models.descriptor import ModelPreset
from appleagentkit.process.runner import CommandRunner


@dataclass(frozen=True, slots=True)
class CoreAIModelRegistry:
    tooling: CoreAITooling
    runner: CommandRunner

    def list_models(
        self,
        *,
        model_type: str = "llm",
        platform: str | None = None,
    ) -> None:
        self.runner.run(
            self._list_command(
                model_type=model_type,
                platform=platform,
            )
        )

    def presets(
        self,
        *,
        model_type: str = "llm",
        platform: str | None = None,
    ) -> tuple[ModelPreset, ...]:
        result = self.runner.capture(
            self._list_command(
                model_type=model_type,
                platform=platform,
            ),
            timeout=120,
        )

        return tuple(
            _parse_presets(result.stdout)
        )

    def resolve(
        self,
        model: str,
        *,
        platform: str | None = None,
    ) -> ModelPreset | None:
        normalized = model.casefold()

        for preset in self.presets(
            platform=platform,
        ):
            if preset.short_name.casefold() == normalized:
                return preset

            if preset.hf_id.casefold() == normalized:
                return preset

        return None

    def platforms_for(
        self,
        model: str,
    ) -> tuple[str, ...]:
        normalized = model.casefold()
        platforms: list[str] = []

        for preset in self.presets():
            if (
                preset.short_name.casefold() == normalized
                or preset.hf_id.casefold() == normalized
            ):
                if preset.platform not in platforms:
                    platforms.append(
                        preset.platform
                    )

        return tuple(platforms)

    def _list_command(
        self,
        *,
        model_type: str,
        platform: str | None,
    ) -> list[str]:
        command = self.tooling.command(
            "coreai.model.registry",
            "--list-models",
            "--type",
            model_type,
        )

        if platform is not None:
            command.extend(
                [
                    "--platform",
                    platform,
                ]
            )

        return command


def _parse_presets(
    output: str,
) -> list[ModelPreset]:
    presets: list[ModelPreset] = []

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("SHORT_NAME"):
            continue

        parts = line.split()

        if len(parts) < 5:
            continue

        short_name = parts[0]
        platform = parts[1]
        compression = parts[2]
        context = parts[3]
        hf_id = parts[4]

        try:
            context_length = int(context)
        except ValueError:
            continue

        presets.append(
            ModelPreset(
                short_name=short_name,
                platform=platform,
                compression=compression,
                context_length=context_length,
                hf_id=hf_id,
            )
        )

    return presets
