from __future__ import annotations

import pathlib
import tempfile

import mknodes as mk

from mkdocs_mknodes import buildcollector, mkdocsconfig
from mkdocs_mknodes.backends import markdownbackend, mkdocsbackend


_dir = tempfile.TemporaryDirectory(prefix="mknodes_")
build_folder = pathlib.Path(_dir.name)


def test_build():
    nav = mk.MkNav.with_context("Test")
    cfg = mkdocsconfig.Config()
    cfg.update_from_context(nav.ctx)
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
    build_info = collector.collect(nav, mk.MaterialTheme())
    assert build_info


def build(project):
    sub_nav = mk.MkNav("Sub nav")
    sub_nav.page_template.announcement_bar = "Hello"
    sub_nav += mk.MkPage("Test page")
    project.root += sub_nav


def test_templates():
    theme = mk.MaterialTheme()
    nav = mk.MkNav.with_context(repo_url=".")
    cfg = mkdocsconfig.Config()
    cfg.update_from_context(nav.ctx)
    mkdocs_backend = mkdocsbackend.MkDocsBackend(
        config=cfg,
        directory=build_folder,
    )
    collector = buildcollector.BuildCollector(backends=[mkdocs_backend])
    collector.collect(nav, theme)
    # assert len(build_info.templates) == 1


if __name__ == "__main__":
    test_templates()
