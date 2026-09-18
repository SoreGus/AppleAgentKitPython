from __future__ import annotations

from dataclasses import dataclass

from appleagentkit.coreai.tooling import CoreAITooling
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
        command = [
            str(self.tooling.model_registry),
            "--list-models",
            "--type",
            model_type,
        ]

        if platform is not None:
            command.extend(
                [
                    "--platform",
                    platform,
                ]
            )

        self.runner.run(command)
