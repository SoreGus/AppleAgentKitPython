# AppleAgentKitPython

Build-time tooling for preparing local language models for AppleAgentKit with Apple's Core AI toolchain.

AppleAgentKitPython does not implement its own model converter. It composes Apple's official `coreai-models`, `coreai-torch`, and `coreai-opt` tooling and produces Core AI resource bundles that can be loaded by `CoreAILanguageModel(resourcesAt:)` from Swift.

## Requirements

- Apple Silicon Mac
- macOS 27+
- Xcode 27+
- Python 3.11–3.13
- Git
- Hugging Face access for the selected model

Python 3.14 is intentionally not supported by this project at the moment because the current `coreai-opt` package requires Python `<3.14`.

## Setup

Create the local environment file:

```bash
cp .env.example .env
```

Adjust `PYTHON_BIN` to the Python executable installed on your Mac. The default is:

```text
/opt/homebrew/opt/python@3.13/bin/python3.13
```

Bootstrap the project:

```bash
make
```

Activate the environment:

```bash
source .venv/bin/activate
```

Validate the machine and toolchain:

```bash
apple-agent-kit doctor
```

## Configuration

`.env`:

```env
PYTHON_BIN=/opt/homebrew/opt/python@3.13/bin/python3.13

APPLE_AGENT_KIT_CACHE_DIR=.cache
APPLE_AGENT_KIT_ARTIFACTS_DIR=Artifacts

APPLE_AGENT_KIT_DEFAULT_MODEL=Qwen/Qwen2.5-1.5B-Instruct
APPLE_AGENT_KIT_DEFAULT_PLATFORM=macOS
APPLE_AGENT_KIT_DEFAULT_COMPRESSION=4bit
APPLE_AGENT_KIT_DEFAULT_CONTEXT_LENGTH=4096

HF_TOKEN=
```

`HF_TOKEN` is optional for public models but is recommended to avoid anonymous Hugging Face rate limits.

## Commands

Validate the environment:

```bash
apple-agent-kit doctor
```

List models registered by Apple's Core AI model tooling:

```bash
apple-agent-kit models
```

List macOS LLM presets:

```bash
apple-agent-kit models --platform macOS
```

Download the default model into the configured cache:

```bash
apple-agent-kit download
```

Download another Hugging Face model:

```bash
apple-agent-kit download Qwen/Qwen3-0.6B
```

Export the configured default model:

```bash
apple-agent-kit prepare
```

Export Qwen 3:

```bash
apple-agent-kit prepare Qwen/Qwen3-0.6B
```

Export for iOS:

```bash
apple-agent-kit prepare Qwen/Qwen2.5-1.5B-Instruct \
  --platform iOS \
  --max-context-length 4096
```

Override compression:

```bash
apple-agent-kit prepare Qwen/Qwen2.5-1.5B-Instruct \
  --compression 4bit_weights_8bit_kv_cache
```

Preview the resolved Apple export configuration without converting:

```bash
apple-agent-kit prepare --dry-run
```

Inspect a generated bundle:

```bash
apple-agent-kit inspect Artifacts/<bundle>
```

Forward arguments to Apple's ahead-of-time compiler:

```bash
apple-agent-kit coreai-build compile --help
```

The `coreai-build` command intentionally forwards arguments directly to Apple's `xcrun coreai-build` tool so Apple remains the source of truth for compiler options.

## Output

Exports are written below:

```text
Artifacts/
```

Apple's LLM exporter produces a resource folder containing the `.aimodel` asset and resources required by the language model, such as tokenizer data and metadata.

AppleAgentKitPython also writes an `appleagentkit-build.json` manifest in the configured export root containing the requested model, target platform, compression, context length, command, and discovered output resources.

## Swift integration

The resulting Core AI resource folder is consumed directly by Apple's runtime:

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
Hugging Face model
        ↓
Apple coreai-models
        ↓
coreai-torch / coreai-opt
        ↓
Core AI resource bundle
        ↓
CoreAILanguageModel
        ↓
FoundationModels
        ↓
AppleAgentKit
```

Responsibilities are deliberately separated:

- AppleAgentKitPython: download, export, optimize, inspect, and prepare artifacts.
- Apple's Core AI tooling: conversion and optimization semantics.
- AppleAgentKit: Swift runtime composition.
- FoundationModels: sessions, tools, guided generation, transcript, and agentic execution.

AppleAgentKitPython does not implement an alternative converter, tokenizer, inference runtime, tool-calling loop, or model format.
