"""Path constants."""

from __future__ import annotations

import pathlib


SRC_FOLDER = pathlib.Path(__file__).parent
RESOURCES = SRC_FOLDER / "resources"
CFG_DEFAULT = RESOURCES / "mkdocs_basic.yml"
DEFAULT_BUILD_FN = "mknodes:MkDefaultWebsite.for_project"
