from __future__ import annotations

from importlib.resources import files
from pathlib import Path


_RESOURCE_ROOT = "resources"


def resolve_coreai_resource(
    relative_path: str,
) -> Path:
    """
    Resolve a packaged Core AI resource into a concrete filesystem path.

    Example:
        models/qwen3/qwen3_1_7b_6bit.yaml
    """

    normalized_path = _normalize_relative_path(
        relative_path
    )

    resource = (
        files("appleagentkit")
        .joinpath(_RESOURCE_ROOT)
        .joinpath(normalized_path)
    )

    path = Path(
        str(resource)
    ).resolve()

    package_root = Path(
        str(
            files("appleagentkit")
            .joinpath(_RESOURCE_ROOT)
        )
    ).resolve()

    if not path.is_relative_to(package_root):
        raise RuntimeError(
            "Invalid Core AI resource path: "
            f"{relative_path}"
        )

    if not path.is_file():
        raise FileNotFoundError(
            "Core AI resource not found: "
            f"{relative_path}"
        )

    return path


def _normalize_relative_path(
    relative_path: str,
) -> str:
    path = Path(relative_path)

    if path.is_absolute():
        raise RuntimeError(
            "Core AI resource path must be relative: "
            f"{relative_path}"
        )

    if ".." in path.parts:
        raise RuntimeError(
            "Core AI resource path cannot contain '..': "
            f"{relative_path}"
        )

    normalized = path.as_posix().lstrip("/")

    if not normalized:
        raise RuntimeError(
            "Core AI resource path cannot be empty."
        )

    return normalized