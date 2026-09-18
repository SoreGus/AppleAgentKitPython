from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping, Sequence
import os
import subprocess


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: tuple[str, ...]
    return_code: int


class CommandRunner:
    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        environment: Mapping[str, str] | None = None,
        check: bool = True,
    ) -> CommandResult:
        command_tuple = tuple(str(part) for part in command)
        merged_environment = os.environ.copy()

        if environment is not None:
            merged_environment.update(environment)

        completed = subprocess.run(
            command_tuple,
            cwd=cwd,
            env=merged_environment,
            check=False,
        )

        if check and completed.returncode != 0:
            raise RuntimeError(
                "Command failed with exit code "
                f"{completed.returncode}: "
                f"{' '.join(command_tuple)}"
            )

        return CommandResult(
            command=command_tuple,
            return_code=completed.returncode,
        )
