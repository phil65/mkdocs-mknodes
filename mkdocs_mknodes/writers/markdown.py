"""Writer producing plain Markdown files (GitHub flavour by default).

The result is a folder of Markdown pages plus a `SUMMARY.md` table of contents, readable
on GitHub (or in any Markdown viewer) without a build step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mknodes.build import MarkdownExporter
from mknodes.build.exporter import SUMMARY_FILE
from mknodes.utils import log

from mkdocs_mknodes.writers.base import GeneratedFolder, Writer


if TYPE_CHECKING:
    import pathlib

    from mknodes.build import BuildOutput


logger = log.get_logger(__name__)


class MarkdownWriter(Writer):
    """Write a `BuildOutput` as plain Markdown files + `SUMMARY.md`.

    Uses the files of mknodes' `MarkdownExporter`, but never overwrites hand-written files
    (see `GeneratedFolder`).
    """

    name = "markdown"
    flavor = "github"

    def write(self, output: BuildOutput) -> pathlib.Path:
        gen_dir = self.settings.resolved_generated_dir
        folder = GeneratedFolder(gen_dir)
        for path, content in MarkdownExporter().get_files(output).items():
            folder.write(path, content)
        removed = folder.finish()
        if output.templates:
            logger.info("Ignoring %s theme templates (no theme)", len(output.templates))
        logger.info(
            "Wrote %s files (%s changed, %s removed, %s hand-written kept) to %s",
            len(folder.written),
            len(folder.changed),
            len(removed),
            len(folder.skipped),
            gen_dir,
        )
        self.folder = folder
        return gen_dir / SUMMARY_FILE

    def build_command(
        self, *, serve: bool = False, extra_args: list[str] | None = None
    ) -> list[str] | None:
        return None
