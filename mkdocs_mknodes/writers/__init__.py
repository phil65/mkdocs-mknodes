"""Writers turning a `BuildOutput` into the input of a static site engine."""

from __future__ import annotations

from mkdocs_mknodes.writers.base import GeneratedFolder, Writer
from mkdocs_mknodes.writers.markdown import MarkdownWriter
from mkdocs_mknodes.writers.zensical import ZensicalWriter


WRITERS: dict[str, type[Writer]] = {"zensical": ZensicalWriter, "markdown": MarkdownWriter}


def get_writer(engine: str) -> type[Writer]:
    """Return the writer class for given engine name."""
    try:
        return WRITERS[engine]
    except KeyError:
        msg = f"Unknown engine {engine!r}. Available: {', '.join(WRITERS)}"
        raise ValueError(msg) from None


__all__ = [
    "WRITERS",
    "GeneratedFolder",
    "MarkdownWriter",
    "Writer",
    "ZensicalWriter",
    "get_writer",
]
