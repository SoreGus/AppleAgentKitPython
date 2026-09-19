from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelPreset:
    short_name: str
    platform: str
    compression: str
    context_length: int
    hf_id: str
