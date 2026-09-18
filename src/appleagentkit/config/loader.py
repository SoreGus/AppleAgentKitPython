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
    default_platform: str
    default_compression: str
    default_context_length: int
    hf_token: str | None


def load_settings(
    project_root: Path | None = None,
) -> Settings:
    root = (project_root or Path.cwd()).resolve()
    load_dotenv(root / ".env")

    cache_dir = _resolve_path(
        root,
        os.getenv(
            "APPLE_AGENT_KIT_CACHE_DIR",
            ".cache",
        ),
    )
    artifacts_dir = _resolve_path(
        root,
        os.getenv(
            "APPLE_AGENT_KIT_ARTIFACTS_DIR",
            "Artifacts",
        ),
    )

    return Settings(
        project_root=root,
        cache_dir=cache_dir,
        artifacts_dir=artifacts_dir,
        default_model=os.getenv(
            "APPLE_AGENT_KIT_DEFAULT_MODEL",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ),
        default_platform=os.getenv(
            "APPLE_AGENT_KIT_DEFAULT_PLATFORM",
            "macOS",
        ),
        default_compression=os.getenv(
            "APPLE_AGENT_KIT_DEFAULT_COMPRESSION",
            "4bit",
        ),
        default_context_length=_int_env(
            "APPLE_AGENT_KIT_DEFAULT_CONTEXT_LENGTH",
            4096,
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


def _int_env(
    name: str,
    default: int,
) -> int:
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(
            f"{name} must be an integer."
        ) from error

    if parsed <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return parsed


def _optional_env(
    name: str,
) -> str | None:
    value = os.getenv(name)

    if value is None:
        return None

    value = value.strip()
    return value or None
