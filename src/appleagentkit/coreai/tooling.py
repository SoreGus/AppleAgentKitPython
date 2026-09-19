from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil


@dataclass(frozen=True, slots=True)
class CoreAITooling:
    uv: Path
    xcrun: Path | None

    @classmethod
    def discover(cls) -> "CoreAITooling":
        return cls(
            uv=_required_executable("uv"),
            xcrun=_optional_executable("xcrun"),
        )

    def command(
        self,
        module: str,
        *arguments: str,
    ) -> list[str]:
        return [
            str(self.uv),
            "run",
            module,
            *arguments,
        ]


def _required_executable(
    name: str,
) -> Path:
    value = shutil.which(name)

    if value is None:
        raise RuntimeError(
            f"Required executable '{name}' was not found."
        )

    return Path(value).resolve()


def _optional_executable(
    name: str,
) -> Path | None:
    value = shutil.which(name)

    if value is None:
        return None

    return Path(value).resolve()
