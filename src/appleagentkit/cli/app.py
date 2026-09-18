from __future__ import annotations

from argparse import ArgumentParser, Namespace, REMAINDER
from pathlib import Path
import json
import subprocess
import sys

from appleagentkit.artifact.manifest import ArtifactManifest
from appleagentkit.config.loader import load_settings
from appleagentkit.coreai.exporter import CoreAIExporter, ExportRequest
from appleagentkit.coreai.registry import CoreAIModelRegistry
from appleagentkit.coreai.tooling import CoreAITooling
from appleagentkit.doctor import run_doctor
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
        print(
            "\nCancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)
    except Exception as error:
        print(
            f"[ERROR] {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error

    raise SystemExit(exit_code)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="apple-agent-kit",
        description=(
            "Prepare Core AI language models "
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
        choices=[
            "macOS",
            "iOS",
        ],
    )

    download = subparsers.add_parser(
        "download",
        help="Download a Hugging Face model into the project cache.",
    )
    download.add_argument(
        "model",
        nargs="?",
    )
    download.add_argument(
        "--revision",
    )

    prepare = subparsers.add_parser(
        "prepare",
        help="Export a language model with Apple's Core AI model tooling.",
    )
    prepare.add_argument(
        "model",
        nargs="?",
    )
    prepare.add_argument(
        "--platform",
        choices=[
            "macOS",
            "iOS",
        ],
    )
    prepare.add_argument(
        "--compression",
    )
    prepare.add_argument(
        "--max-context-length",
        type=int,
    )
    prepare.add_argument(
        "--output-dir",
        type=Path,
    )
    prepare.add_argument(
        "--experimental",
        action="store_true",
    )
    prepare.add_argument(
        "--include-debug-info",
        action="store_true",
    )
    prepare.add_argument(
        "--dry-run",
        action="store_true",
    )

    inspect = subparsers.add_parser(
        "inspect",
        help="Inspect an exported Core AI resource directory.",
    )
    inspect.add_argument(
        "path",
        type=Path,
    )

    coreai_build = subparsers.add_parser(
        "coreai-build",
        help=(
            "Forward arguments to Apple's "
            "`xcrun coreai-build` command."
        ),
    )
    coreai_build.add_argument(
        "arguments",
        nargs=REMAINDER,
    )

    return parser


def _run_command(
    arguments: Namespace,
    *,
    settings,
    runner: CommandRunner,
) -> int:
    if arguments.command == "doctor":
        result = run_doctor(
            settings
        )
        return 0 if result.ok else 1

    if arguments.command == "models":
        registry = CoreAIModelRegistry(
            tooling=CoreAITooling.discover(),
            runner=runner,
        )
        registry.list_models(
            model_type=arguments.model_type,
            platform=arguments.platform,
        )
        return 0

    if arguments.command == "download":
        model = (
            arguments.model
            or settings.default_model
        )
        path = ModelDownloader(
            settings=settings
        ).download(
            model,
            revision=arguments.revision,
        )
        print(
            f"[OK] Model downloaded: {path}"
        )
        return 0

    if arguments.command == "prepare":
        request = _export_request(
            arguments,
            settings,
        )
        exporter = CoreAIExporter(
            settings=settings,
            tooling=CoreAITooling.discover(),
            runner=runner,
        )
        manifest = exporter.export(
            request
        )

        if request.dry_run:
            print(
                "[OK] Dry run completed."
            )
        else:
            print(
                "[OK] Export completed."
            )
            print(
                f"Output: {request.output_dir}"
            )
            print(
                "Manifest: "
                f"{request.output_dir / 'appleagentkit-build.json'}"
            )

        return 0

    if arguments.command == "inspect":
        _inspect(
            arguments.path
        )
        return 0

    if arguments.command == "coreai-build":
        command = [
            "xcrun",
            "coreai-build",
            *arguments.arguments,
        ]
        completed = subprocess.run(
            command,
            check=False,
        )
        return completed.returncode

    raise RuntimeError(
        f"Unknown command: {arguments.command}"
    )


def _export_request(
    arguments: Namespace,
    settings,
) -> ExportRequest:
    model = (
        arguments.model
        or settings.default_model
    )
    platform = (
        arguments.platform
        or settings.default_platform
    )

    compression = arguments.compression

    if compression is None:
        compression = (
            settings.default_compression
        )

    max_context_length = (
        arguments.max_context_length
    )

    if max_context_length is None:
        max_context_length = (
            settings.default_context_length
        )

    output_dir = arguments.output_dir

    if output_dir is None:
        output_dir = (
            settings.artifacts_dir
            / _safe_model_name(model)
            / platform
        )
    elif not output_dir.is_absolute():
        output_dir = (
            settings.project_root
            / output_dir
        )

    return ExportRequest(
        model=model,
        platform=platform,
        compression=compression,
        max_context_length=max_context_length,
        output_dir=output_dir.resolve(),
        experimental=arguments.experimental,
        include_debug_info=arguments.include_debug_info,
        dry_run=arguments.dry_run,
    )


def _safe_model_name(
    model: str,
) -> str:
    return (
        model.replace("/", "--")
        .replace(":", "-")
        .replace(" ", "-")
    )


def _inspect(
    path: Path,
) -> None:
    target = path.expanduser().resolve()

    if not target.exists():
        raise FileNotFoundError(
            target
        )

    manifest_path = (
        target
        / "appleagentkit-build.json"
    )

    if manifest_path.is_file():
        manifest = ArtifactManifest.read(
            manifest_path
        )
        print(
            json.dumps(
                {
                    "model": manifest.model,
                    "platform": manifest.platform,
                    "compression": manifest.compression,
                    "max_context_length": (
                        manifest.max_context_length
                    ),
                    "resources": [
                        {
                            "path": resource.path,
                            "kind": resource.kind,
                        }
                        for resource
                        in manifest.resources
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    resources: list[dict[str, str]] = []

    for resource in sorted(
        target.rglob("*")
    ):
        if not resource.is_file():
            continue

        if (
            resource.suffix == ".aimodel"
            or resource.name == "metadata.json"
            or "tokenizer" in resource.name.lower()
        ):
            resources.append(
                {
                    "path": str(
                        resource.relative_to(
                            target
                        )
                    ),
                    "kind": (
                        "aimodel"
                        if resource.suffix == ".aimodel"
                        else (
                            "metadata"
                            if resource.name == "metadata.json"
                            else "tokenizer"
                        )
                    ),
                }
            )

    print(
        json.dumps(
            {
                "path": str(target),
                "resources": resources,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
