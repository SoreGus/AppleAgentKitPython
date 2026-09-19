from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from huggingface_hub import hf_hub_download

from appleagentkit.artifact.store import ArtifactStore
from appleagentkit.config.loader import Settings
from appleagentkit.huggingface.client import HuggingFaceClient
from appleagentkit.huggingface.model_card import build_model_card


@dataclass(frozen=True, slots=True)
class PublishRequest:
    model: str
    repo_id: str
    private: bool = False
    commit_message: str | None = None


@dataclass(frozen=True, slots=True)
class ModelPublisher:
    settings: Settings
    store: ArtifactStore
    client: HuggingFaceClient

    def publish(
        self,
        request: PublishRequest,
    ) -> str:
        identity = self.client.whoami()
        name = identity.get("name") or identity.get("fullname")

        if name:
            print(
                f"[OK] Hugging Face: authenticated as {name}"
            )
        else:
            print(
                "[OK] Hugging Face: authenticated"
            )

        manifest = self.store.require_model_manifest(
            request.model
        )
        root = self.store.model_root(
            request.model
        )
        self._validate_variants(
            root,
            manifest,
        )

        base_model = _base_model(manifest)
        license_name = self._license_for(
            base_model
        )

        card = build_model_card(
            manifest=manifest,
            base_model=base_model,
            license_name=license_name,
        )
        (root / "README.md").write_text(
            card,
            encoding="utf-8",
        )

        self._copy_upstream_license(
            base_model,
            root,
        )

        self.client.create_model_repo(
            request.repo_id,
            private=request.private,
        )

        return self.client.upload_model_folder(
            request.repo_id,
            root,
            commit_message=(
                request.commit_message
                or f"Publish {request.model} Core AI artifacts"
            ),
        )

    def _validate_variants(
        self,
        root: Path,
        manifest,
    ) -> None:
        if not manifest.variants:
            raise RuntimeError(
                "The model manifest contains no prepared variants."
            )

        for variant in manifest.variants:
            variant_root = root / variant.path
            build_manifest = (
                variant_root
                / "appleagentkit-build.json"
            )

            if not build_manifest.is_file():
                raise RuntimeError(
                    "Missing build manifest for "
                    f"{variant.platform}: {build_manifest}"
                )

            has_aimodel = any(
                ".aimodel" in path.parts
                or path.suffix == ".aimodel"
                for path in variant_root.rglob("*")
            )

            if not has_aimodel:
                raise RuntimeError(
                    "No .aimodel resources were found for "
                    f"{variant.platform} in {variant_root}."
                )

    def _license_for(
        self,
        base_model: str | None,
    ) -> str | None:
        if base_model is None:
            return None

        try:
            info = self.client.upstream_model_info(
                base_model
            )
        except Exception:
            return None

        card_data = getattr(
            info,
            "card_data",
            None,
        )

        if card_data is None:
            return None

        license_name = getattr(
            card_data,
            "license",
            None,
        )

        if isinstance(license_name, str):
            return license_name

        return None

    def _copy_upstream_license(
        self,
        base_model: str | None,
        root: Path,
    ) -> None:
        if base_model is None:
            return

        for filename in (
            "LICENSE",
            "LICENSE.txt",
            "LICENSE.md",
        ):
            try:
                source = hf_hub_download(
                    repo_id=base_model,
                    filename=filename,
                    token=self.settings.hf_token,
                    cache_dir=(
                        self.settings.cache_dir
                        / "huggingface"
                    ),
                )
            except Exception:
                continue

            destination = root / filename
            shutil.copy2(
                source,
                destination,
            )
            return


def _base_model(
    manifest,
) -> str | None:
    values = {
        variant.base_model
        for variant in manifest.variants
        if variant.base_model is not None
    }

    if not values:
        return None

    if len(values) > 1:
        raise RuntimeError(
            "Prepared variants do not reference the same upstream model."
        )

    return next(iter(values))
