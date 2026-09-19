from __future__ import annotations

from appleagentkit.artifact.manifest import ModelArtifactManifest


def build_model_card(
    *,
    manifest: ModelArtifactManifest,
    base_model: str | None,
    license_name: str | None,
) -> str:
    metadata = [
        "---",
    ]

    if license_name:
        metadata.append(
            f"license: {license_name}"
        )

    if base_model:
        metadata.append(
            f"base_model: {base_model}"
        )

    metadata.extend(
        [
            "tags:",
            "- coreai",
            "- apple-silicon",
            "- on-device",
            "- foundation-models",
            "---",
            "",
        ]
    )

    title = manifest.model
    rows = []

    for variant in manifest.variants:
        rows.append(
            f"| {variant.platform} | `{variant.path}/` |"
        )

    body = [
        f"# {title} — Core AI",
        "",
        "Core AI conversion prepared with Apple's official `coreai-models` tooling and AppleAgentKitPython.",
        "",
    ]

    if base_model:
        body.extend(
            [
                f"Base model: `{base_model}`.",
                "",
            ]
        )

    body.extend(
        [
            "## Variants",
            "",
            "| Platform | Resources |",
            "| --- | --- |",
            *rows,
            "",
            "Each platform directory contains the Core AI resource bundle produced by `coreai.llm.export` plus `appleagentkit-build.json` with reproducibility metadata.",
            "",
            "## Swift",
            "",
            "```swift",
            "import CoreAILanguageModels",
            "import FoundationModels",
            "",
            "let model = try await CoreAILanguageModel(",
            "    resourcesAt: modelURL",
            ")",
            "",
            "let session = LanguageModelSession(",
            "    model: model",
            ")",
            "```",
            "",
            "## Attribution",
            "",
            "This repository contains a converted artifact of the upstream model. Review the upstream model card and license before redistribution or use.",
            "",
        ]
    )

    return "\n".join(
        [
            *metadata,
            *body,
        ]
    )
