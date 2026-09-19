from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: tuple[str, ...]
    return_code: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner:
    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        environment: Mapping[str, str] | None = None,
        check: bool = True,
    ) -> CommandResult:
        return self._execute(
            command,
            cwd=cwd,
            environment=environment,
            check=check,
            capture_output=False,
        )

    def capture(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        environment: Mapping[str, str] | None = None,
        check: bool = True,
        timeout: float | None = None,
    ) -> CommandResult:
        return self._execute(
            command,
            cwd=cwd,
            environment=environment,
            check=check,
            capture_output=True,
            timeout=timeout,
        )

    def _execute(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None,
        environment: Mapping[str, str] | None,
        check: bool,
        capture_output: bool,
        timeout: float | None = None,
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
            capture_output=capture_output,
            text=capture_output,
            timeout=timeout,
        )

        stdout = completed.stdout or "" if capture_output else ""
        stderr = completed.stderr or "" if capture_output else ""

        if check and completed.returncode != 0:
            detail = stderr.strip() or stdout.strip()
            suffix = f"\n{detail}" if detail else ""

            raise RuntimeError(
                "Command failed with exit code "
                f"{completed.returncode}: "
                f"{' '.join(command_tuple)}"
                f"{suffix}"
            )

        return CommandResult(
            command=command_tuple,
            return_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
        )
