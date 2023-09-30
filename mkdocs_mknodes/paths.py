from __future__ import annotations

import pathlib


CFG_DEFAULT = "configs/mkdocs_basic.yml"
TEST_RESOURCES = pathlib.Path(__file__).parent.parent / "tests" / "data"
RESOURCES = pathlib.Path(__file__).parent / "resources"
CSS_DIR = RESOURCES / "css"
DOCS_DIR = pathlib.Path(__file__).parent.parent / "docs"
DEFAULT_BUILD_FN = "mknodes.navs.mkdefaultwebsite:MkDefaultWebsite.for_project"
