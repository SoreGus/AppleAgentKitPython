from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib.metadata
import platform
import shutil
import subprocess
import sys

from appleagentkit.config.loader import Settings
from appleagentkit.coreai.tooling import CoreAITooling


@dataclass(frozen=True, slots=True)
class DoctorResult:
    ok: bool


def run_doctor(
    settings: Settings,
) -> DoctorResult:
    failures: list[str] = []

    _print_check(
        "Platform",
        f"{platform.system()} {platform.machine()}",
        platform.system() == "Darwin"
        and platform.machine() == "arm64",
        failures,
    )

    python_ok = (
        (3, 11)
        <= sys.version_info[:2]
        < (3, 14)
    )

    _print_check(
        "Python",
        (
            f"{sys.version_info.major}."
            f"{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        ),
        python_ok,
        failures,
    )

    for package in (
        "coreai-models",
        "coreai-core",
        "coreai-torch",
        "coreai-opt",
        "torch",
        "transformers",
        "huggingface-hub",
    ):
        _check_package(
            package,
            failures,
        )

    try:
        tooling = CoreAITooling.discover()
        _print_check(
            "coreai.llm.export",
            str(tooling.llm_export),
            True,
            failures,
        )
        _print_check(
            "coreai.model.registry",
            str(tooling.model_registry),
            True,
            failures,
        )
    except RuntimeError as error:
        print(
            f"[FAIL] Core AI CLI: {error}"
        )
        failures.append(
            "Core AI CLI"
        )
        tooling = None

    xcrun = shutil.which("xcrun")

    _print_check(
        "xcrun",
        xcrun or "not found",
        xcrun is not None,
        failures,
    )

    if xcrun is not None:
        _check_coreai_build(
            xcrun,
            failures,
        )

    _ensure_directory(
        settings.cache_dir,
        "Cache directory",
        failures,
    )
    _ensure_directory(
        settings.artifacts_dir,
        "Artifacts directory",
        failures,
    )

    if settings.hf_token:
        print("[OK] HF_TOKEN: configured")
    else:
        print(
            "[WARN] HF_TOKEN: not configured "
            "(public models still work, "
            "but anonymous rate limits apply)"
        )

    if failures:
        print()
        print(
            "[FAIL] Environment is not ready."
        )
        return DoctorResult(
            ok=False
        )

    print()
    print(
        "[OK] Environment is ready."
    )
    return DoctorResult(
        ok=True
    )


def _check_package(
    package: str,
    failures: list[str],
) -> None:
    try:
        version = importlib.metadata.version(
            package
        )
    except importlib.metadata.PackageNotFoundError:
        print(
            f"[FAIL] {package}: not installed"
        )
        failures.append(package)
        return

    print(
        f"[OK] {package}: {version}"
    )


def _check_coreai_build(
    xcrun: str,
    failures: list[str],
) -> None:
    completed = subprocess.run(
        [
            xcrun,
            "--find",
            "coreai-build",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode == 0:
        print(
            "[OK] coreai-build: "
            f"{completed.stdout.strip()}"
        )
        return

    print(
        "[FAIL] coreai-build: not available "
        "through xcrun"
    )
    failures.append(
        "coreai-build"
    )


def _ensure_directory(
    path: Path,
    label: str,
    failures: list[str],
) -> None:
    try:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as error:
        print(
            f"[FAIL] {label}: {error}"
        )
        failures.append(label)
        return

    print(
        f"[OK] {label}: {path}"
    )


def _print_check(
    label: str,
    value: str,
    ok: bool,
    failures: list[str],
) -> None:
    prefix = "OK" if ok else "FAIL"
    print(
        f"[{prefix}] {label}: {value}"
    )

    if not ok:
        failures.append(label)
