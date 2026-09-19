# AppleAgentKitPython

Build-time tooling for preparing and publishing local language models for AppleAgentKit with Apple's Core AI toolchain.

AppleAgentKitPython does not implement its own model converter. Apple's `coreai-models` registry and exporters remain the source of truth for supported models, platform presets, compression recipes, precision, and context configuration.

## Requirements

- Apple Silicon Mac
- Xcode 27+
- Python 3.11–3.13
- `uv`
- Git

Python 3.14 is intentionally excluded because the current `coreai-opt` dependency requires Python `<3.14`.

Install `uv` if necessary:

```bash
brew install uv
```

## Setup

Create the local environment file:

```bash
cp .env-example .env
```

Adjust `PYTHON_BIN` if necessary:

```env
PYTHON_BIN=/opt/homebrew/opt/python@3.13/bin/python3.13

APPLE_AGENT_KIT_CACHE_DIR=.cache
APPLE_AGENT_KIT_ARTIFACTS_DIR=Artifacts
APPLE_AGENT_KIT_DEFAULT_MODEL=qwen3-1.7b

HF_TOKEN=
```

Bootstrap and validate everything:

```bash
make
```

`make` validates Python and `uv`, synchronizes `.venv` from `pyproject.toml` / `uv.lock`, and runs `apple-agent-kit doctor`.

Activation is optional. The Makefile calls the virtual-environment executables directly. Activate only for interactive use:

```bash
source .venv/bin/activate
```

## Core AI model registry

List all Apple-registered LLM presets:

```bash
apple-agent-kit models
```

Filter by platform:

```bash
apple-agent-kit models --platform macOS
apple-agent-kit models --platform iOS
```

Use registry short names such as `qwen3-1.7b`. Apple resolves the Hugging Face model ID and tested platform-specific export defaults.

## Download

Download the upstream Hugging Face model into the configured cache without exporting it:

```bash
apple-agent-kit download qwen3-1.7b
```

The short name is resolved through Apple's registry. A raw Hugging Face model ID is also accepted:

```bash
apple-agent-kit download Qwen/Qwen3-1.7B
```

## Prepare

Export the default model for macOS:

```bash
apple-agent-kit prepare
```

Export a specific registered model:

```bash
apple-agent-kit prepare qwen3-1.7b --platform macOS
```

Export the iOS/iPadOS variant:

```bash
apple-agent-kit prepare qwen3-1.7b --platform iOS
```

Export both Apple-platform variants:

```bash
apple-agent-kit prepare-all qwen3-1.7b
```

For registered models, compression and context configuration are intentionally left to Apple's registry. Advanced exporter flags can still be forwarded when explicitly needed:

```bash
apple-agent-kit prepare qwen3-1.7b \
  --platform macOS \
  --max-context-length 4096
```

A dry run resolves the Apple exporter configuration without conversion:

```bash
apple-agent-kit prepare qwen3-1.7b --platform macOS --dry-run
```

Artifacts are organized as:

```text
Artifacts/
└── qwen3-1.7b/
    ├── manifest.json
    ├── macOS/
    │   ├── appleagentkit-build.json
    │   └── <Core AI resources>
    └── iOS/
        ├── appleagentkit-build.json
        └── <Core AI resources>
```

## Inspect

Inspect all prepared variants:

```bash
apple-agent-kit inspect qwen3-1.7b
```

Inspect one platform:

```bash
apple-agent-kit inspect qwen3-1.7b --platform macOS
```

## Hugging Face authentication

Create a Hugging Face account and authenticate once locally:

```bash
apple-agent-kit login
```

The underlying Hugging Face credential is stored by `huggingface-hub`. `HF_TOKEN` is optional and is mainly useful for CI or explicit environment-based authentication.

Verify authentication:

```bash
apple-agent-kit whoami
```

## Publish

After preparing one or both variants, publish the artifact root to a Hugging Face model repository:

```bash
apple-agent-kit publish qwen3-1.7b \
  --repo SoreGus/Qwen3-1.7B-CoreAI
```

The command:

1. validates local Hugging Face authentication;
2. validates the prepared artifact manifest;
3. generates a model card from the Apple registry/build metadata;
4. attempts to copy the upstream model license into the publication root;
5. creates the Hugging Face model repository when necessary;
6. uploads the folder with `huggingface-hub`.

Create a private repository with:

```bash
apple-agent-kit publish qwen3-1.7b \
  --repo SoreGus/Qwen3-1.7B-CoreAI \
  --private
```

## Swift integration

A prepared/downloaded Core AI resource folder can be loaded directly by Apple's runtime:

```swift
import CoreAILanguageModels
import FoundationModels

let model = try await CoreAILanguageModel(
    resourcesAt: modelURL
)

let session = LanguageModelSession(
    model: model
)
```

AppleAgentKit can use that `CoreAILanguageModel` anywhere it accepts a `LanguageModel`.

## Design

```text
Apple Core AI registry
        ↓
AppleAgentKitPython
        ↓
coreai.llm.export
        ↓
Core AI resource bundles
        ↓
Hugging Face repository
        ↓
AppleAgentKit Swift
        ↓
CoreAILanguageModel
        ↓
FoundationModels
```

Responsibilities are deliberately separated:

- Apple's Core AI tooling owns model conversion semantics and tested presets.
- AppleAgentKitPython owns build workflow, local artifact organization, inspection, and publication.
- Hugging Face stores and distributes prepared Core AI artifacts.
- AppleAgentKit owns Swift-side model acquisition/composition.
- FoundationModels/Core AI own inference, sessions, tools, guided generation, and agentic execution.

AppleAgentKitPython does not implement an alternative converter, tokenizer, inference runtime, tool-calling loop, or model format.
