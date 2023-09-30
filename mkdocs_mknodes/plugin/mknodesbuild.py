"""The Mkdocs Plugin."""

from __future__ import annotations

import pathlib
import tempfile

from typing import TYPE_CHECKING, Literal
import urllib.parse

from mkdocs.plugins import get_plugin_logger
from mknodes import mkdocsconfig, project
from mknodes.pages import mkpage
from mknodes.theme import theme

from mkdocs_mknodes.plugin import linkreplacer, markdownbackend, mkdocsbackend


if TYPE_CHECKING:

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page

    # from mkdocs.utils.templates import TemplateContext


logger = get_plugin_logger(__name__)

CommandStr = Literal["build", "serve", "gh-deploy"]


class MkNodesBuild:
    def __init__(self, build_folder, build_fn):
        self.link_replacer = linkreplacer.LinkReplacer()
        logger.debug("Finished initializing plugin")
        if build_folder:
            self.build_folder = pathlib.Path(build_folder)
        else:
            self._dir = tempfile.TemporaryDirectory(prefix="mknodes_")
            self.build_folder = pathlib.Path(self._dir.name)
            logger.debug("Creating temporary dir %s", self._dir.name)
        if not build_fn:
            return
        skin = theme.Theme.get_theme(
            theme_name=config.theme.name or "material",
            data=config.theme._vars,  # type: ignore[attr-defined]
        )
        self.project = project.Project(
            base_url=config.site_url or "",
            use_directory_urls=config.use_directory_urls,
            theme=skin,
            repo=self.config.repo_path,
            build_fn=build_fn,
            build_kwargs=self.config.kwargs,
            clone_depth=self.config.clone_depth,
        )
        logger.info("Generating pages...")
        self.build_info = self.project.build(self.config.show_page_info)

    def on_files(self, files: Files, config: MkDocsConfig) -> Files:
        """Create the node tree and write files to build folder.

        In this step we aggregate all files and info we need to build the website.
        This includes:

          - Markdown pages (MkPages)
          - Templates
          - CSS files
        """
        if not self.config.build_fn:
            return files

        # now we add our stuff to the MkDocs build environment
        cfg = mkdocsconfig.Config(config)

        logger.info("Updating MkDocs config metadata...")
        cfg.update_from_context(self.project.context)
        logger.info("Setting up build backends...")
        mkdocs_backend = mkdocsbackend.MkDocsBackend(
            files=files,
            config=config,
            directory=self.build_folder,
        )

        markdown_backend = markdownbackend.MarkdownBackend(
            directory=pathlib.Path(config.site_dir) / "src",
            extension=".original",
        )
        self.backends = [mkdocs_backend, markdown_backend]

        for backend in self.backends:
            logger.info("%s: Collecting data..", type(self).__name__)
            backend.collect(self.build_info.build_files, self.build_info.resources)
        return mkdocs_backend.files

    def on_nav(
        self,
        nav: Navigation,
        files: Files,
        config: MkDocsConfig,
    ) -> Navigation | None:
        """Populate LinkReplacer and build path->MkPage mapping for following steps."""
        for file_ in files:
            filename = pathlib.Path(file_.abs_src_path).name
            url = urllib.parse.unquote(file_.src_uri)
            self.link_replacer.mapping[filename].append(url)
        return nav

    def on_pre_page(
        self,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> Page | None:
        """During this phase we set the edit paths."""
        node = self.build_info.page_mapping.get(page.file.src_uri)
        edit_path = node._edit_path if isinstance(node, mkpage.MkPage) else None
        cfg = mkdocsconfig.Config(config)
        if path := cfg.get_edit_url(edit_path):
            page.edit_url = path
        return page

    def on_page_markdown(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str | None:
        """During this phase links get replaced and `jinja2` stuff get rendered."""
        node = self.build_info.page_mapping.get(page.file.src_uri)
        if node is None:
            return markdown
        markdown = node.env.render_string(markdown)
        return self.link_replacer.replace(markdown, page.file.src_uri)

    def on_post_build(self, config: MkDocsConfig):
        """Delete the temporary template files."""
        if not config.theme.custom_dir:
            return
        if not self.config.build_fn:
            return
