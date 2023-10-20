from __future__ import annotations

import pathlib
import tempfile

import mknodes as mk

from mkdocs_mknodes import buildcollector, mkdocsconfig
from mkdocs_mknodes.backends import markdownbackend, mkdocsbackend


_dir = tempfile.TemporaryDirectory(prefix="mknodes_")
build_folder = pathlib.Path(_dir.name)


def test_build(mkdocs_mknodes_project):
    project = mkdocs_mknodes_project
    project.build()
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


def build(project):
    root = project.get_root()
    sub_nav = mk.MkNav("Sub nav")
    sub_nav.page_template.announcement_bar = "Hello"
    sub_nav += mk.MkPage("Test page")
    root += sub_nav


def test_templates():
    theme = mk.MaterialTheme()
    project = mk.Project(theme=theme, repo=".", build_fn=build)
    project.build()
    cfg = mkdocsconfig.Config()
    cfg.update_from_context(project.context)
    mkdocs_backend = mkdocsbackend.MkDocsBackend(
        config=cfg,
        directory=build_folder,
    )
    collector = buildcollector.BuildCollector(backends=[mkdocs_backend])
    assert project._root
    collector.collect(project._root, project.theme)
    # assert len(build_info.templates) == 1


if __name__ == "__main__":
    test_templates()
