from __future__ import annotations

from typing import TYPE_CHECKING

from mknodes.utils import log
import upath
from upathtools import helpers

from mkdocs_mknodes.backends import buildbackend


if TYPE_CHECKING:
    from upath.types import JoinablePathLike


logger = log.get_logger(__name__)


class MarkdownBackend(buildbackend.BuildBackend):
    def __init__(
        self,
        directory: JoinablePathLike | None = None,
        extension: str = ".md",
    ):
        """Constructor.

        Args:
            directory: build directory
            extension: Extention of files to generate
        """
        self.extension = extension
        self.directory = upath.UPath(directory or ".")
        self._files: dict[str, str | bytes] = {}

    def write_files(self, files: dict[str, str | bytes]):
        for k, v in files.items():
            logger.debug("%s: Writing file to %r", type(self).__name__, str(k))
            target_path = (self.directory / k).with_suffix(self.extension)
            self._files[target_path.as_posix()] = v
            helpers.write_file(v, target_path)

    # def write(self):
    #     for k, v in self._files.items():
    #         pathhelpers.write_file(v, k)


if __name__ == "__main__":
    cfg = MarkdownBackend()
