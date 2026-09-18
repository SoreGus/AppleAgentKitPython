from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Sequence
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
    platform: str
    compression: str | None
    max_context_length: int | None
    dry_run: bool
    export_root: str
    command: tuple[str, ...]
    resources: tuple[ArtifactResource, ...]

    @classmethod
    def create(
        cls,
        *,
        export_root: Path,
        model: str,
        platform: str,
        compression: str | None,
        max_context_length: int | None,
        dry_run: bool,
        command: Sequence[str],
    ) -> ArtifactManifest:
        resources = ()

        if not dry_run:
            resources = tuple(
                _discover_resources(export_root)
            )

        return cls(
            version=1,
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            model=model,
            platform=platform,
            compression=compression,
            max_context_length=max_context_length,
            dry_run=dry_run,
            export_root=str(export_root),
            command=tuple(command),
            resources=resources,
        )

    @classmethod
    def read(
        cls,
        path: Path,
    ) -> ArtifactManifest:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        resources = tuple(
            ArtifactResource(**resource)
            for resource in data.get(
                "resources",
                []
            )
        )

        return cls(
            version=data["version"],
            created_at=data["created_at"],
            model=data["model"],
            platform=data["platform"],
            compression=data.get("compression"),
            max_context_length=data.get(
                "max_context_length"
            ),
            dry_run=data.get(
                "dry_run",
                False,
            ),
            export_root=data["export_root"],
            command=tuple(
                data.get(
                    "command",
                    [],
                )
            ),
            resources=resources,
        )

    def write(
        self,
    ) -> Path:
        root = Path(self.export_root)
        root.mkdir(
            parents=True,
            exist_ok=True,
        )
        path = (
            root
            / "appleagentkit-build.json"
        )

        path.write_text(
            json.dumps(
                asdict(self),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return path


def _discover_resources(
    root: Path,
) -> list[ArtifactResource]:
    resources: list[ArtifactResource] = []

    for path in sorted(
        root.rglob("*")
    ):
        if not path.is_file():
            continue

        kind = _resource_kind(path)

        if kind is None:
            continue

        resources.append(
            ArtifactResource(
                path=str(
                    path.relative_to(root)
                ),
                kind=kind,
            )
        )

    return resources


def _resource_kind(
    path: Path,
) -> str | None:
    if path.suffix == ".aimodel":
        return "aimodel"

    if path.name == "metadata.json":
        return "metadata"

    if "tokenizer" in path.name.lower():
        return "tokenizer"

    return None
