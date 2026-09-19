from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    cache_dir: Path
    artifacts_dir: Path
    default_model: str
    hf_token: str | None


def load_settings(
    project_root: Path | None = None,
) -> Settings:
    root = (project_root or Path.cwd()).resolve()
    load_dotenv(root / ".env")

    return Settings(
        project_root=root,
        cache_dir=_resolve_path(
            root,
            os.getenv(
                "APPLE_AGENT_KIT_CACHE_DIR",
                ".cache",
            ),
        ),
        artifacts_dir=_resolve_path(
            root,
            os.getenv(
                "APPLE_AGENT_KIT_ARTIFACTS_DIR",
                "Artifacts",
            ),
        ),
        default_model=os.getenv(
            "APPLE_AGENT_KIT_DEFAULT_MODEL",
            "qwen3-1.7b",
        ),
        hf_token=_optional_env("HF_TOKEN"),
    )


def _resolve_path(
    root: Path,
    value: str,
) -> Path:
    path = Path(value).expanduser()

    if not path.is_absolute():
        path = root / path

    return path.resolve()


def _optional_env(
    name: str,
) -> str | None:
    value = os.getenv(name)

    if value is None:
        return None

    value = value.strip()
    return value or None
