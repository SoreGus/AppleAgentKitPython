from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import sys


@dataclass(frozen=True, slots=True)
class CoreAITooling:
    llm_export: Path
    model_registry: Path
    xcrun: Path | None

    @classmethod
    def discover(cls) -> CoreAITooling:
        return cls(
            llm_export=_required_executable(
                "coreai.llm.export"
            ),
            model_registry=_required_executable(
                "coreai.model.registry"
            ),
            xcrun=_optional_executable("xcrun"),
        )


def current_python() -> Path:
    return Path(sys.executable).resolve()


def _required_executable(
    name: str,
) -> Path:
    value = shutil.which(name)

    if value is None:
        raise RuntimeError(
            f"Required executable '{name}' was not found. "
            "Run `make` to install the project dependencies."
        )

    return Path(value).resolve()


def _optional_executable(
    name: str,
) -> Path | None:
    value = shutil.which(name)

    if value is None:
        return None

    return Path(value).resolve()
