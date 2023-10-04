from __future__ import annotations

import os
import pathlib

from mknodes.utils import log, pathhelpers

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
        self.directory = pathlib.Path(directory or ".")
        self._files: dict[str, str | bytes] = {}

    def collect_files(self, files: dict[str, str | bytes]):
        for k, v in files.items():
            logger.debug("%s: Writing file to %r", type(self).__name__, str(k))
            target_path = (self.directory / k).with_suffix(self.extension).as_posix()
            self._files[str(target_path)] = v
            pathhelpers.write_file(v, str(target_path))

    # def write(self):
    #     for k, v in self._files.items():
    #         pathhelpers.write_file(v, k)


if __name__ == "__main__":
    cfg = MarkdownBackend()
