from __future__ import annotations

import pathlib
import tempfile

from mkdocs_mknodes import buildcollector, mkdocsconfig
from mkdocs_mknodes.backends import markdownbackend, mkdocsbackend


_dir = tempfile.TemporaryDirectory(prefix="mknodes_")
build_folder = pathlib.Path(_dir.name)


def test_build(project):
    project.build()
    project.build()
    # now we add our stuff to the MkDocs build environment
    cfg = mkdocsconfig.Config()
    cfg.update_from_context(project.context)
    mkdocs_backend = mkdocsbackend.MkDocsBackend(
        config=cfg,
        directory=build_folder,
    )

    markdown_backend = markdownbackend.MarkdownBackend(
        directory=pathlib.Path(cfg.site_dir) / "src",
        extension=".original",
    )
    collector = buildcollector.BuildCollector(
        backends=[mkdocs_backend, markdown_backend],
        show_page_info=True,
    )
    assert project._root
    build_info = collector.collect(project._root, project.theme)
    assert build_info
