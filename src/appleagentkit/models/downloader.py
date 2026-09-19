from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import snapshot_download

from appleagentkit.config.loader import Settings
from appleagentkit.coreai.registry import CoreAIModelRegistry


@dataclass(frozen=True, slots=True)
class ModelDownloader:
    settings: Settings
    registry: CoreAIModelRegistry

    def download(
        self,
        model: str,
        *,
        platform: str | None = None,
        revision: str | None = None,
    ) -> Path:
        preset = self.registry.resolve(
            model,
            platform=platform,
        )
        model_id = (
            preset.hf_id
            if preset is not None
            else model
        )

        cache_dir = (
            self.settings.cache_dir
            / "huggingface"
        )
        cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = snapshot_download(
            repo_id=model_id,
            revision=revision,
            cache_dir=cache_dir,
            token=self.settings.hf_token,
        )

        return Path(path).resolve()
