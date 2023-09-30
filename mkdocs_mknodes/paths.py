from __future__ import annotations

import pathlib


CFG_DEFAULT = "configs/mkdocs_basic.yml"
RESOURCES = pathlib.Path(__file__).parent / "resources"
DEFAULT_BUILD_FN = "mknodes.navs.mkdefaultwebsite:MkDefaultWebsite.for_project"
