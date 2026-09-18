from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import snapshot_download

from appleagentkit.config.loader import Settings


@dataclass(frozen=True, slots=True)
class ModelDownloader:
    settings: Settings

    def download(
        self,
        model_id: str,
        *,
        revision: str | None = None,
    ) -> Path:
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
