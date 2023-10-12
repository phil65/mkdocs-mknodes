"""The Mkdocs Plugin."""

from __future__ import annotations

from collections.abc import Callable
import pathlib
import urllib.parse
import tempfile
from typing import TYPE_CHECKING, Literal

from mkdocs import livereload
from mkdocs.plugins import BasePlugin, get_plugin_logger
import mknodes as mk
from mknodes.utils import linkreplacer

from mkdocs_mknodes import buildcollector, mkdocsconfig
from mkdocs_mknodes.backends import markdownbackend, mkdocsbackend
from mkdocs_mknodes.plugin import pluginconfig

if TYPE_CHECKING:
    import jinja2
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page

    # from mkdocs.utils.templates import TemplateContext


logger = get_plugin_logger(__name__)

CommandStr = Literal["build", "serve", "gh-deploy"]


class MkNodesPlugin(BasePlugin[pluginconfig.PluginConfig]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.link_replacer = linkreplacer.LinkReplacer()
        logger.debug("Finished initializing plugin")

    def on_startup(self, command: CommandStr, dirty: bool = False):
        """Activates new-style MkDocs plugin lifecycle."""
        if self.config.build_folder:
            self.build_folder = pathlib.Path(self.config.build_folder)
        else:
            self._dir = tempfile.TemporaryDirectory(prefix="mknodes_")
            self.build_folder = pathlib.Path(self._dir.name)
            logger.debug("Creating temporary dir %s", self._dir.name)

    def on_config(self, config: MkDocsConfig):
        """Create the project based on MkDocs config."""
        if not self.config.build_fn:
            return
        skin = mk.Theme.get_theme(
            theme_name=config.theme.name or "material",
            data=config.theme._vars,  # type: ignore[attr-defined]
        )
        self.project = mk.Project(
            base_url=config.site_url or "",
            use_directory_urls=config.use_directory_urls,
            theme=skin,
            repo=self.config.repo_path,
            build_fn=self.config.build_fn,
            build_kwargs=self.config.kwargs,
            clone_depth=self.config.clone_depth,
        )

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

        logger.info("Generating pages...")
        self.project.build()
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
        collector = buildcollector.BuildCollector(
            backends=[mkdocs_backend, markdown_backend],
            show_page_info=self.config.show_page_info,
        )
        assert self.project._root
        self.build_info = collector.collect(self.project._root, self.project.theme)
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

    def on_env(self, env: jinja2.Environment, config: MkDocsConfig, files: Files):
        """Add our own info to the MkDocs environment."""
        node_env = self.project.context.env
        env.globals["mknodes"] = node_env.globals
        env.filters |= node_env.filters
        logger.debug("Added macros / filters to MkDocs jinja2 environment.")

    def on_pre_page(
        self,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> Page | None:
        """During this phase we set the edit paths."""
        node = self.build_info.page_mapping.get(page.file.src_uri)
        edit_path = node._edit_path if isinstance(node, mk.MkPage) else None
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
        for template in self.build_info.resources.templates:
            path = pathlib.Path(config.theme.custom_dir) / template.filename
            path.unlink(missing_ok=True)

    def on_serve(
        self,
        server: livereload.LiveReloadServer,
        config: MkDocsConfig,
        builder: Callable,
    ):
        """Remove all watched paths in case MkNodes is used to build the website."""
        if self.config.build_fn:
            server._watched_paths = {}
