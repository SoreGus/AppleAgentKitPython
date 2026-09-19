from __future__ import annotations

from argparse import ArgumentParser, Namespace, REMAINDER
from pathlib import Path
import json
import subprocess
import sys

from appleagentkit.artifact.manifest import ArtifactManifest
from appleagentkit.artifact.store import ArtifactStore
from appleagentkit.config.loader import Settings, load_settings
from appleagentkit.coreai.exporter import CoreAIExporter, ExportRequest
from appleagentkit.coreai.registry import CoreAIModelRegistry
from appleagentkit.coreai.tooling import CoreAITooling
from appleagentkit.doctor import run_doctor
from appleagentkit.huggingface.client import HuggingFaceClient
from appleagentkit.huggingface.publisher import ModelPublisher, PublishRequest
from appleagentkit.models.downloader import ModelDownloader
from appleagentkit.process.runner import CommandRunner


def main() -> None:
    parser = _build_parser()
    arguments = parser.parse_args()

    if arguments.command is None:
        parser.print_help()
        return

    settings = load_settings()
    runner = CommandRunner()

    try:
        exit_code = _run_command(
            arguments,
            settings=settings,
            runner=runner,
        )
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        raise SystemExit(1) from error

    raise SystemExit(exit_code)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="apple-agent-kit",
        description=(
            "Prepare and publish Core AI language models "
            "for AppleAgentKit."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command"
    )

    subparsers.add_parser(
        "doctor",
        help="Validate the local Core AI toolchain.",
    )

    models = subparsers.add_parser(
        "models",
        help="List models registered by Apple's Core AI tooling.",
    )
    models.add_argument(
        "--type",
        default="llm",
        dest="model_type",
    )
    models.add_argument(
        "--platform",
        choices=["macOS", "iOS"],
    )

    download = subparsers.add_parser(
        "download",
        help="Download a registered or raw Hugging Face model.",
    )
    download.add_argument(
        "model",
        nargs="?",
    )
    download.add_argument(
        "--platform",
        choices=["macOS", "iOS"],
    )
    download.add_argument("--revision")

    prepare = subparsers.add_parser(
        "prepare",
        help="Export one Core AI platform variant.",
    )
    _add_prepare_arguments(prepare)

    prepare_all = subparsers.add_parser(
        "prepare-all",
        help="Export all registered Apple platform variants.",
    )
    prepare_all.add_argument(
        "model",
        nargs="?",
    )
    prepare_all.add_argument(
        "--include-debug-info",
        action="store_true",
    )

    inspect = subparsers.add_parser(
        "inspect",
        help="Inspect prepared Core AI artifacts.",
    )
    inspect.add_argument(
        "model",
        nargs="?",
    )
    inspect.add_argument(
        "--platform",
        choices=["macOS", "iOS"],
    )

    subparsers.add_parser(
        "login",
        help="Authenticate with Hugging Face interactively.",
    )
    subparsers.add_parser(
        "whoami",
        help="Show the current Hugging Face identity.",
    )

    publish = subparsers.add_parser(
        "publish",
        help="Publish prepared Core AI artifacts to Hugging Face.",
    )
    publish.add_argument(
        "model",
        nargs="?",
    )
    publish.add_argument(
        "--repo",
        required=True,
        dest="repo_id",
    )
    publish.add_argument(
        "--private",
        action="store_true",
    )
    publish.add_argument(
        "--commit-message",
    )

    coreai_build = subparsers.add_parser(
        "coreai-build",
        help="Forward arguments to Apple's xcrun coreai-build command.",
    )
    coreai_build.add_argument(
        "arguments",
        nargs=REMAINDER,
    )

    return parser


def _add_prepare_arguments(
    parser: ArgumentParser,
) -> None:
    parser.add_argument(
        "model",
        nargs="?",
    )
    parser.add_argument(
        "--platform",
        choices=["macOS", "iOS"],
        default="macOS",
    )
    parser.add_argument(
        "--max-context-length",
        type=int,
    )
    parser.add_argument("--compression")
    parser.add_argument(
        "--compression-config",
        type=Path,
    )
    parser.add_argument(
        "--experimental",
        action="store_true",
    )
    parser.add_argument(
        "--include-debug-info",
        action="store_true",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )


def _run_command(
    arguments: Namespace,
    *,
    settings: Settings,
    runner: CommandRunner,
) -> int:
    if arguments.command == "doctor":
        result = run_doctor(settings)
        return 0 if result.ok else 1

    tooling = CoreAITooling.discover()
    registry = CoreAIModelRegistry(
        tooling=tooling,
        runner=runner,
    )
    store = ArtifactStore(settings)

    if arguments.command == "models":
        registry.list_models(
            model_type=arguments.model_type,
            platform=arguments.platform,
        )
        return 0

    if arguments.command == "download":
        model = arguments.model or settings.default_model
        path = ModelDownloader(
            settings=settings,
            registry=registry,
        ).download(
            model,
            platform=arguments.platform,
            revision=arguments.revision,
        )
        print(f"[OK] Model downloaded: {path}")
        return 0

    if arguments.command == "prepare":
        model = arguments.model or settings.default_model
        exporter = _exporter(
            settings,
            tooling,
            registry,
            store,
            runner,
        )
        build = exporter.export(
            ExportRequest(
                model=model,
                platform=arguments.platform,
                max_context_length=arguments.max_context_length,
                compression=arguments.compression,
                compression_config=arguments.compression_config,
                experimental=arguments.experimental,
                include_debug_info=arguments.include_debug_info,
                dry_run=arguments.dry_run,
            )
        )

        if build is None:
            print("[OK] Dry run completed.")
        else:
            print(
                "[OK] Export completed: "
                f"{build.export_root}"
            )
        return 0

    if arguments.command == "prepare-all":
        model = arguments.model or settings.default_model
        platforms = registry.platforms_for(model)

        if not platforms:
            raise RuntimeError(
                f"No registered Core AI presets were found for '{model}'."
            )

        exporter = _exporter(
            settings,
            tooling,
            registry,
            store,
            runner,
        )

        for platform_name in platforms:
            print(
                f"[INFO] Preparing {model} for {platform_name}..."
            )
            exporter.export(
                ExportRequest(
                    model=model,
                    platform=platform_name,
                    include_debug_info=arguments.include_debug_info,
                )
            )

        print(
            "[OK] Prepared variants: "
            f"{', '.join(platforms)}"
        )
        return 0

    if arguments.command == "inspect":
        model = arguments.model or settings.default_model
        _inspect(
            store,
            model,
            arguments.platform,
        )
        return 0

    if arguments.command == "login":
        HuggingFaceClient(settings).login()
        return 0

    if arguments.command == "whoami":
        identity = HuggingFaceClient(settings).whoami()
        print(
            json.dumps(
                identity,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
        return 0

    if arguments.command == "publish":
        model = arguments.model or settings.default_model
        url = ModelPublisher(
            settings=settings,
            store=store,
            client=HuggingFaceClient(settings),
        ).publish(
            PublishRequest(
                model=model,
                repo_id=arguments.repo_id,
                private=arguments.private,
                commit_message=arguments.commit_message,
            )
        )
        print(f"[OK] Published: {url}")
        return 0

    if arguments.command == "coreai-build":
        completed = subprocess.run(
            [
                "xcrun",
                "coreai-build",
                *arguments.arguments,
            ],
            check=False,
        )
        return completed.returncode

    raise RuntimeError(
        f"Unknown command: {arguments.command}"
    )


def _exporter(
    settings: Settings,
    tooling: CoreAITooling,
    registry: CoreAIModelRegistry,
    store: ArtifactStore,
    runner: CommandRunner,
) -> CoreAIExporter:
    return CoreAIExporter(
        settings=settings,
        tooling=tooling,
        registry=registry,
        store=store,
        runner=runner,
    )


def _inspect(
    store: ArtifactStore,
    model: str,
    platform: str | None,
) -> None:
    if platform is not None:
        path = store.build_manifest_path(
            model,
            platform,
        )

        if not path.is_file():
            raise FileNotFoundError(path)

        manifest = ArtifactManifest.read(path)
        print(
            json.dumps(
                {
                    "model": manifest.model,
                    "base_model": manifest.base_model,
                    "platform": manifest.platform,
                    "export_root": manifest.export_root,
                    "resources": [
                        {
                            "path": resource.path,
                            "kind": resource.kind,
                        }
                        for resource in manifest.resources
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    manifest = store.require_model_manifest(model)
    print(
        json.dumps(
            {
                "model": manifest.model,
                "updated_at": manifest.updated_at,
                "variants": [
                    {
                        "platform": variant.platform,
                        "path": variant.path,
                        "base_model": variant.base_model,
                    }
                    for variant in manifest.variants
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
