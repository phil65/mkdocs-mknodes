"""The Mkdocs Plugin."""

from __future__ import annotations

import pathlib

from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import File, Files


logger = get_plugin_logger(__name__)


def file_sorter(f: File):
    parts = pathlib.PurePath(f.src_path).parts
    return tuple(
        chr(f.name != "index" if i == len(parts) - 1 else 2) + p
        for i, p in enumerate(parts)
    )


def merge_files(*files: Files) -> Files:
    file_list = [i for j in files for i in j]
    return Files(sorted(file_list, key=file_sorter))
