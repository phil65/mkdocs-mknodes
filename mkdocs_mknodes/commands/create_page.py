from __future__ import annotations

import mknodes as mk

from mknodes import paths
from mknodes.utils import log


logger = log.get_logger(__name__)


def build_page(path, repo_path: str = ".", build_fn: str = paths.DEFAULT_BUILD_FN):
    skin = mk.Theme("material")
    proj = mk.Project(
        base_url="",
        use_directory_urls=True,
        theme=skin,
        repo=repo_path,
        build_fn=build_fn,
        clone_depth=1,
    )
    proj.build()
    proj.env.add_template(path)
    node = mk.MkJinjaTemplate(path, context=proj.context)
    return str(node)


if __name__ == "__main__":
    text = build_page("mkdocs_mknodes/resources/github_index.jinja")
    print(text)
