"""The Mkdocs Plugin."""

from __future__ import annotations

import collections
from collections.abc import Callable, Iterable
import contextlib
import datetime
import functools
import gzip
import logging
import os
import pathlib
import re
import time
from typing import TYPE_CHECKING, Any, TypeVar

from mkdocs import exceptions
from mkdocs.structure.files import File, Files, InclusionLevel, _file_sort_key
import pathspec
import upath

from mkdocs_mknodes import telemetry


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


logger = telemetry.get_plugin_logger(__name__)

_default_exclude = pathspec.gitignore.GitIgnoreSpec.from_lines([".*", "/templates/"])


T = TypeVar("T")


class CountHandler(logging.NullHandler):
    """Counts all logged messages >= level."""

    def __init__(self, **kwargs: Any) -> None:
        self.counts: dict[int, int] = collections.defaultdict(int)
        super().__init__(**kwargs)

    def handle(self, record):
        rv = self.filter(record)
        if rv:
            # Use levelno for keys so they can be sorted later
            self.counts[record.levelno] += 1
        return rv

    def get_counts(self) -> list[tuple[str, int]]:
        return [
            (logging.getLevelName(k), v)
            for k, v in sorted(self.counts.items(), reverse=True)
        ]


def count_warnings(fn: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(fn)
    def wrapped(config: MkDocsConfig, *args, **kwargs) -> T:
        start = time.monotonic()
        warning_counter = CountHandler()
        warning_counter.setLevel(logging.WARNING)
        if config.strict:
            logging.getLogger("mkdocs").addHandler(warning_counter)
        result = fn(config, *args, **kwargs)
        counts = warning_counter.get_counts()
        if counts:
            msg = ", ".join(f"{v} {k.lower()}s" for k, v in counts)
            msg = f"Aborted with {msg} in strict mode!"
            raise exceptions.Abort(msg)
        duration = time.monotonic() - start
        logger.info("Documentation built in %.2f seconds", duration)
        logging.getLogger("mkdocs").removeHandler(warning_counter)

        return result

    return wrapped


def handle_exceptions(fn: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(fn)
    def wrapped(config: MkDocsConfig, *args, **kwargs) -> T:
        try:
            return fn(config, *args, **kwargs)
        except Exception as e:
            # Run `build_error` plugin events.
            config.plugins.on_build_error(error=e)
            if isinstance(e, exceptions.BuildError):
                msg = "Aborted with a BuildError!"
                logger.exception(msg)
                raise exceptions.Abort(msg) from e
            raise
        # finally:
        # logging.getLogger("mkdocs").removeHandler(warning_counter)

    return wrapped


def set_exclusions(files: Iterable[File], config: MkDocsConfig) -> None:
    """Re-calculate which files are excluded, based on the patterns in the config."""
    exclude: pathspec.gitignore.GitIgnoreSpec | None = config.get("exclude_docs")
    exclude = _default_exclude + exclude if exclude else _default_exclude
    drafts: pathspec.gitignore.GitIgnoreSpec | None = config.get("draft_docs")
    nav_exclude: pathspec.gitignore.GitIgnoreSpec | None = config.get("not_in_nav")

    for file in files:
        if file.inclusion == InclusionLevel.UNDEFINED:
            if exclude.match_file(file.src_uri):
                file.inclusion = InclusionLevel.EXCLUDED
            elif drafts and drafts.match_file(file.src_uri):
                file.inclusion = InclusionLevel.DRAFT
            elif nav_exclude and nav_exclude.match_file(file.src_uri):
                file.inclusion = InclusionLevel.NOT_IN_NAV
            else:
                file.inclusion = InclusionLevel.INCLUDED

                file.inclusion = InclusionLevel.INCLUDED


def get_files(config: MkDocsConfig) -> Files:
    """Walk the `docs_dir` and return a Files collection."""
    files: list[File] = []
    conflicting_files: list[tuple[File, File]] = []
    for source_dir, dirnames, filenames in os.walk(config["docs_dir"], followlinks=True):
        relative_dir = os.path.relpath(source_dir, config["docs_dir"])
        dirnames.sort()
        filenames.sort(key=_file_sort_key)

        files_by_dest: dict[str, File] = {}
        for filename in filenames:
            path = pathlib.Path(relative_dir) / filename
            file = File(
                str(path),
                config["docs_dir"],
                config["site_dir"],
                config["use_directory_urls"],
            )
            # Skip README.md if an index file also exists in dir (part 1)
            prev_file = files_by_dest.setdefault(file.dest_uri, file)
            if prev_file is not file:
                conflicting_files.append((prev_file, file))
            files.append(file)
            prev_file = file

    set_exclusions(files, config)
    # Skip README.md if an index file also exists in dir (part 2)
    for a, b in conflicting_files:
        if b.inclusion.is_included():
            if a.inclusion.is_included():
                logger.warning(
                    "Excluding '%s' from site because it conflicts with '%s'.",
                    a.src_uri,
                    b.src_uri,
                )
            # avoid errors if attempting to remove the same file twice.
            with contextlib.suppress(ValueError):
                files.remove(a)
        else:
            with contextlib.suppress(ValueError):
                files.remove(b)
    return Files(files)


def write_gzip(output_path: str | os.PathLike[str], output: str, timestamp: int):
    """Build a gzipped version of the sitemap.

    Args:
        output_path: Path to the sitemap
        output: File content
        timestamp: Optional numeric timestamp to be written to the last modification time
                   field in the stream when compressing.
                   If omitted or None, the current time is used.
    """
    logger.debug("Gzipping %r", output_path)
    gz_filename = upath.UPath(output_path)
    with (
        gz_filename.open("wb") as f,
        gzip.GzipFile(gz_filename, fileobj=f, mode="wb", mtime=timestamp) as gz_buf,
    ):
        gz_buf.write(output.encode())


def get_build_datetime() -> datetime.datetime:
    """Get the build datetime, respecting SOURCE_DATE_EPOCH if set.

    Support SOURCE_DATE_EPOCH environment variable for reproducible builds.
    See https://reproducible-builds.org/specs/source-date-epoch/

    Returns:
        Aware datetime object
    """
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is None:
        return datetime.datetime.now(datetime.UTC)

    return datetime.datetime.fromtimestamp(int(source_date_epoch), datetime.UTC)


_ERROR_TEMPLATE_RE = re.compile(r"^\d{3}\.html?$")


def is_error_template(path: str) -> bool:
    """Check if a template path is an error code template (like "404.html").

    Args:
        path: Template path to check

    Returns:
        True if path matches error template pattern
    """
    return bool(_ERROR_TEMPLATE_RE.match(path))
