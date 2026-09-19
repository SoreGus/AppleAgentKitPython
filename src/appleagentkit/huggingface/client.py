from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import HfApi, login

from appleagentkit.config.loader import Settings


@dataclass(frozen=True, slots=True)
class HuggingFaceClient:
    settings: Settings

    def login(
        self,
    ) -> None:
        login()

    def whoami(
        self,
    ) -> dict[str, object]:
        api = HfApi(
            token=self.settings.hf_token
        )
        return api.whoami()

    def create_model_repo(
        self,
        repo_id: str,
        *,
        private: bool,
    ) -> str:
        api = HfApi(
            token=self.settings.hf_token
        )
        result = api.create_repo(
            repo_id=repo_id,
            repo_type="model",
            private=private,
            exist_ok=True,
        )
        return str(result)

    def upload_model_folder(
        self,
        repo_id: str,
        folder: Path,
        *,
        commit_message: str | None,
    ) -> str:
        api = HfApi(
            token=self.settings.hf_token
        )
        result = api.upload_folder(
            repo_id=repo_id,
            repo_type="model",
            folder_path=folder,
            commit_message=commit_message,
            ignore_patterns=[
                ".cache/**",
                "**/.DS_Store",
            ],
        )
        return str(result.commit_url)

    def upstream_model_info(
        self,
        model_id: str,
    ):
        api = HfApi(
            token=self.settings.hf_token
        )
        return api.model_info(
            model_id,
            files_metadata=False,
        )
