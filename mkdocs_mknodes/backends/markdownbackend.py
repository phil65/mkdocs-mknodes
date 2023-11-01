from __future__ import annotations

import os

from mknodes.utils import log, pathhelpers
import upath

from mkdocs_mknodes.backends import buildbackend


logger = log.get_logger(__name__)


class MarkdownBackend(buildbackend.BuildBackend):
    def __init__(
        self,
        directory: str | os.PathLike | None = None,
        extension: str = ".md",
    ):
        """Constructor.

        Arguments:
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
            pathhelpers.write_file(v, target_path)

    # def write(self):
    #     for k, v in self._files.items():
    #         pathhelpers.write_file(v, k)


if __name__ == "__main__":
    cfg = MarkdownBackend()
