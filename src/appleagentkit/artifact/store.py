from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from appleagentkit.artifact.manifest import (
    ArtifactManifest,
    ModelArtifactManifest,
    ModelVariant,
)
from appleagentkit.config.loader import Settings


@dataclass(frozen=True, slots=True)
class ArtifactStore:
    settings: Settings

    def model_root(
        self,
        model: str,
    ) -> Path:
        return (
            self.settings.artifacts_dir
            / _safe_model_name(model)
        )

    def variant_root(
        self,
        model: str,
        platform: str,
    ) -> Path:
        return (
            self.model_root(model)
            / platform
        )

    def build_manifest_path(
        self,
        model: str,
        platform: str,
    ) -> Path:
        return (
            self.variant_root(
                model,
                platform,
            )
            / "appleagentkit-build.json"
        )

    def model_manifest_path(
        self,
        model: str,
    ) -> Path:
        return (
            self.model_root(model)
            / "manifest.json"
        )

    def register_variant(
        self,
        build: ArtifactManifest,
    ) -> ModelArtifactManifest:
        path = self.model_manifest_path(
            build.model
        )

        if path.is_file():
            current = ModelArtifactManifest.read(
                path
            )
            variants = {
                variant.platform: variant
                for variant in current.variants
            }
        else:
            variants = {}

        variants[build.platform] = ModelVariant(
            platform=build.platform,
            path=build.platform,
            base_model=build.base_model,
        )

        manifest = ModelArtifactManifest(
            version=1,
            updated_at=build.created_at,
            model=build.model,
            variants=tuple(
                variants[key]
                for key in sorted(variants)
            ),
        )
        manifest.write(path)
        return manifest

    def require_model_manifest(
        self,
        model: str,
    ) -> ModelArtifactManifest:
        path = self.model_manifest_path(model)

        if not path.is_file():
            raise FileNotFoundError(
                "No prepared artifact manifest was found for "
                f"'{model}' at {path}."
            )

        return ModelArtifactManifest.read(path)


def _safe_model_name(
    model: str,
) -> str:
    return (
        model.replace("/", "--")
        .replace(":", "-")
        .replace(" ", "-")
    )
