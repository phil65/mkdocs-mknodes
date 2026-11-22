"""Regenerate the site input when project sources change."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from mknodes.utils import log


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from mkdocs_mknodes.generator.settings import GeneratorSettings


logger = log.get_logger(__name__)

WATCHED_SUFFIXES = {".py", ".md", ".jinja", ".toml", ".yml", ".yaml", ".j2", ".html", ".css"}
SKIPPED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
    "dist",
    "build",
}


def iter_watched_files(settings: GeneratorSettings) -> Iterable[pathlib.Path]:
    """Yield the source files whose changes should trigger a regeneration.

    That is everything in the project with a relevant suffix (Python sources, README,
    pyproject / mkdocs.yml, hand-written docs and templates), except the site dir, the
    generated config and the folders the generator writes into.
    """
    root = settings.project_dir
    site_cfg_dir = settings.site_dir or settings.site_config.get("site_dir") or "site"
    excluded_dirs = {(root / site_cfg_dir).resolve()}
    gen_dir = settings.resolved_generated_dir.resolve()
    if gen_dir != settings.resolved_docs_dir.resolve():
        excluded_dirs.add(gen_dir)
    generated = _generated_files(settings)
    generated.add(settings.generated_config_path.resolve())
    for dirpath, dirs, files in os.walk(root):
        current = pathlib.Path(dirpath)
        dirs[:] = [
            d
            for d in dirs
            if d not in SKIPPED_DIRS
            and not d.startswith(".")
            and (current / d).resolve() not in excluded_dirs
        ]
        for name in files:
            path = current / name
            if path.suffix in WATCHED_SUFFIXES and path.resolve() not in generated:
                yield path


def _generated_files(settings: GeneratorSettings) -> set[pathlib.Path]:
    from mkdocs_mknodes.writers.base import GeneratedFolder

    result: set[pathlib.Path] = set()
    folders = [settings.resolved_generated_dir]
    theme = settings.site_config.get("theme")
    if isinstance(theme, dict) and theme.get("custom_dir"):
        folders.append(settings.project_dir / str(theme["custom_dir"]))
    folders.append(settings.project_dir / "overrides")
    for folder in folders:
        manifest = GeneratedFolder(folder)
        result |= {(folder / p).resolve() for p in manifest.previous}
    return result


def snapshot(settings: GeneratorSettings) -> dict[pathlib.Path, int]:
    """Return path -> mtime for all watched files."""
    result = {}
    for path in iter_watched_files(settings):
        try:
            result[path] = path.stat().st_mtime_ns
        except OSError:
            continue
    return result


def watch(
    settings: GeneratorSettings,
    regenerate: Callable[[], object],
    *,
    interval: float = 1.0,
    should_stop: Callable[[], bool] = lambda: False,
) -> None:
    """Poll the watched files and call `regenerate` after changes.

    Args:
        settings: Generator settings (determine which files are watched)
        regenerate: Callable doing the regeneration
        interval: Poll interval in seconds
        should_stop: Callable returning True when watching should end
    """
    state = snapshot(settings)
    logger.info("Watching %s files for changes...", len(state))
    while not should_stop():
        time.sleep(interval)
        new_state = snapshot(settings)
        if new_state == state:
            continue
        changed = sorted(
            str(p.relative_to(settings.project_dir))
            for p in set(state) ^ set(new_state)
            | {p for p in new_state if p in state and state[p] != new_state[p]}
        )
        logger.info("Changes detected (%s), regenerating...", ", ".join(changed[:5]))
        try:
            regenerate()
        except Exception:
            logger.exception("Regeneration failed")
        state = snapshot(settings)


def regenerate_in_subprocess(args: Sequence[str]) -> Callable[[], int]:
    """Return a callable running `mkdocs-mknodes generate <args>` in a fresh interpreter.

    A fresh process makes sure changed project modules (and the build function) get
    re-imported and no caches survive.
    """

    def regenerate() -> int:
        cmd = [sys.executable, "-m", "mkdocs_mknodes", "generate", *args]
        return subprocess.call(cmd)

    return regenerate
