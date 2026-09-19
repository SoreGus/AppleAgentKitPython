from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass(frozen=True, slots=True)
class ArtifactResource:
    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    version: int
    created_at: str
    model: str
    base_model: str | None
    platform: str
    export_root: str
    command: tuple[str, ...]
    resources: tuple[ArtifactResource, ...]

    @classmethod
    def create(
        cls,
        *,
        export_root: Path,
        model: str,
        base_model: str | None,
        platform: str,
        command: Sequence[str],
    ) -> "ArtifactManifest":
        return cls(
            version=1,
            created_at=_now(),
            model=model,
            base_model=base_model,
            platform=platform,
            export_root=str(export_root),
            command=tuple(command),
            resources=tuple(
                _discover_resources(export_root)
            ),
        )

    @classmethod
    def read(
        cls,
        path: Path,
    ) -> "ArtifactManifest":
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return cls(
            version=data["version"],
            created_at=data["created_at"],
            model=data["model"],
            base_model=data.get("base_model"),
            platform=data["platform"],
            export_root=data["export_root"],
            command=tuple(
                data.get("command", [])
            ),
            resources=tuple(
                ArtifactResource(**resource)
                for resource in data.get(
                    "resources",
                    [],
                )
            ),
        )

    def write(
        self,
    ) -> Path:
        path = (
            Path(self.export_root)
            / "appleagentkit-build.json"
        )
        _write_json(
            path,
            asdict(self),
        )
        return path


@dataclass(frozen=True, slots=True)
class ModelVariant:
    platform: str
    path: str
    base_model: str | None


@dataclass(frozen=True, slots=True)
class ModelArtifactManifest:
    version: int
    updated_at: str
    model: str
    variants: tuple[ModelVariant, ...]

    @classmethod
    def read(
        cls,
        path: Path,
    ) -> "ModelArtifactManifest":
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return cls(
            version=data["version"],
            updated_at=data["updated_at"],
            model=data["model"],
            variants=tuple(
                ModelVariant(**variant)
                for variant in data.get(
                    "variants",
                    [],
                )
            ),
        )

    def write(
        self,
        path: Path,
    ) -> Path:
        _write_json(
            path,
            asdict(self),
        )
        return path


def _discover_resources(
    root: Path,
) -> list[ArtifactResource]:
    resources: list[ArtifactResource] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.name == "appleagentkit-build.json":
            continue

        resources.append(
            ArtifactResource(
                path=str(
                    path.relative_to(root)
                ),
                kind=_resource_kind(path),
            )
        )

    return resources


def _resource_kind(
    path: Path,
) -> str:
    if ".aimodel" in path.parts or path.suffix == ".aimodel":
        return "aimodel"

    if path.name == "metadata.json":
        return "metadata"

    if "tokenizer" in path.as_posix().lower():
        return "tokenizer"

    return "resource"


def _write_json(
    path: Path,
    data: object,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()
