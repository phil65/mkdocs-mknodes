"""The Mkdocs Plugin."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import os
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import jinja2
from jinja2.exceptions import TemplateNotFound
from jinjarope import htmlfilters
import logfire
from mkdocs import exceptions
from mkdocs.structure.files import Files, InclusionLevel
from mkdocs.structure.nav import Navigation, get_navigation
from mkdocs.structure.pages import Page
from mknodes.utils import pathhelpers
import upath

from mkdocs_mknodes import telemetry
from mkdocs_mknodes.builders import configbuilder
from mkdocs_mknodes.commands import templatecontext, utils
from mkdocs_mknodes.plugin.mknodesconfig import MkNodesConfig


if TYPE_CHECKING:
    from mkdocs.structure.files import File


logger = telemetry.get_plugin_logger(__name__)


DRAFT_CONTENT = (
    '<div class="mkdocs-draft-marker" title="This page wont be included into the site.">'
    "DRAFT"
    "</div>"
)


class MarkdownBuilder:
    """Handles the initial phase of building Websites.

    File collection and markdown processing.
    """

    def __init__(self, config: MkNodesConfig | None = None):
        """Initialize the markdown builder.

        Args:
            config: Optional MkDocs configuration
        """
        self.config = config or MkNodesConfig()

    def build_from_config(
        self,
        config_path: str | os.PathLike[str],
        repo_path: str,
        build_fn: str | None,
        *,
        site_dir: str | None = None,
        clone_depth: int = 100,
        **kwargs: Any,
    ) -> tuple[Navigation, Files]:
        """Build markdown content from config file.

        Args:
            config_path: Path to the MkDocs config file
            repo_path: Repository path/URL to build docs for
            build_fn: Fully qualified name of build function to use
            site_dir: Output directory for built site
            clone_depth: Number of commits to fetch for Git repos
            kwargs: Additional config overrides passed to MkDocs

        Returns:
            Navigation structure
        """
        cfg_builder = configbuilder.ConfigBuilder(
            repo_path=repo_path, build_fn=build_fn, clone_depth=clone_depth
        )
        cfg_builder.add_config_file(config_path)
        self.config = cfg_builder.build_mkdocs_config(site_dir=site_dir, **kwargs)

        with logfire.span("plugins callback: on_startup", config=self.config):
            self.config.plugins.on_startup(command="build", dirty=False)

        nav, files = self.process_markdown()
        return nav, files

    @utils.handle_exceptions
    @utils.count_warnings
    def process_markdown(self, dirty: bool = False) -> tuple[Navigation, Files]:
        """Process markdown files and build navigation structure.

        Args:
            dirty: Do a dirty build

        Returns:
            Navigation structure
        """
        if self.config is None:
            msg = "Configuration must be set before processing markdown"
            raise ValueError(msg)

        with logfire.span("plugins callback: on_config", config=self.config):
            self.config = self.config.plugins.on_config(self.config)
        with logfire.span("plugins callback: on_pre_build", config=self.config):
            self.config.plugins.on_pre_build(config=self.config)

        if not dirty:
            logger.info("Cleaning site directory")
            pathhelpers.clean_directory(self.config.site_dir)

        files = utils.get_files(self.config)
        env = self.config.theme.get_env()
        files.add_files_from_theme(env, self.config)

        with logfire.span("plugins callback: on_files", files=files, config=self.config):
            files = self.config.plugins.on_files(files, config=self.config)

        utils.set_exclusions(files._files, self.config)
        nav = get_navigation(files, self.config)

        with logfire.span("plugins callback: on_nav", config=self.config, nav=nav):
            nav = self.config.plugins.on_nav(nav, config=self.config, files=files)

        self._process_pages(files)
        return nav, files

    @logfire.instrument("Populate pages")
    def _process_pages(self, files: Files) -> None:
        """Process all pages, reading their content and applying plugins.

        Args:
            files: Collection of files to process
        """
        for file in files.documentation_pages():
            logger.debug("Reading: %s", file.src_uri)
            if file.page is None and file.inclusion.is_not_in_nav():
                Page(None, file, self.config)
            assert file.page is not None
            self._populate_page(file.page, files)

    @logfire.instrument("populate page for {file.src_uri}")
    def _populate_page(self, page: Page, files: Files) -> None:
        """Read page content from docs_dir and render Markdown.

        Args:
            page: Page to populate
            files: Collection of files
        """
        self.config._current_page = page
        try:
            with logfire.span(
                "plugins callback: on_pre_page", page=page, config=self.config
            ):
                page = self.config.plugins.on_pre_page(
                    page, config=self.config, files=files
                )

            with logfire.span("read_source", page=page):
                page.read_source(self.config)
            assert page.markdown is not None

            with logfire.span(
                "plugins callback: on_page_markdown", page=page, config=self.config
            ):
                page.markdown = self.config.plugins.on_page_markdown(
                    page.markdown, page=page, config=self.config, files=files
                )

            with logfire.span("render", page=page, config=self.config):
                page.render(self.config, files)
            assert page.content is not None

            with logfire.span(
                "plugins callback: on_page_content", page=page, config=self.config
            ):
                page.content = self.config.plugins.on_page_content(
                    page.content, page=page, config=self.config, files=files
                )
        except Exception as e:
            message = f"Error reading page '{page.file.src_uri}':"
            if not isinstance(e, exceptions.BuildError):
                message += f" {e}"
            logger.exception(message)
            raise
        finally:
            self.config._current_page = None


class HTMLBuilder:
    """Handles the HTML generation phase of building MkDocs sites."""

    def __init__(self, config: MkNodesConfig):
        """Initialize the HTML builder.

        Args:
            config: MkDocs configuration
        """
        self.config = config

    def build_html(
        self,
        nav: Navigation,
        files: Files,
        live_server_url: str | None = None,
        dirty: bool = False,
    ) -> None:
        """Build HTML files from processed markdown.

        Args:
            nav: Navigation structure
            files: Collection of files
            live_server_url: An optional URL of the live server to use
            dirty: Whether this is a dirty build
        """
        env = self.config.theme.get_env()
        with logfire.span("plugins callback: on_env", env=env, config=self.config):
            env = self.config.plugins.on_env(env, config=self.config, files=files)

        with logfire.span("copy_static_files"):
            inclusion = (
                InclusionLevel.is_in_serve
                if live_server_url
                else InclusionLevel.is_included
            )
            files.copy_static_files(dirty=dirty, inclusion=inclusion)

        self._build_templates(env, files, nav)
        self._build_pages(files, nav, env, dirty, inclusion)

        with logfire.span("plugins callback: on_post_build", config=self.config):
            self.config.plugins.on_post_build(config=self.config)

    @logfire.instrument("Build templates")
    def _build_templates(
        self, env: jinja2.Environment, files: Files, nav: Navigation
    ) -> None:
        """Build all templates.

        Args:
            env: Jinja environment
            files: Collection of files
            nav: Navigation structure
        """
        for template in self.config.theme.static_templates:
            self._build_theme_template(template, env, files, nav)
        for template in self.config.extra_templates:
            self._build_extra_template(template, files, nav)

    def _build_pages(
        self,
        files: Files,
        nav: Navigation,
        env: jinja2.Environment,
        dirty: bool,
        inclusion: Callable[[InclusionLevel], bool],
    ) -> None:
        """Build all pages.

        Args:
            files: Collection of files
            nav: Navigation structure
            env: Jinja environment
            dirty: Whether this is a dirty build
            inclusion: Inclusion level for pages
        """
        logger.debug("Building markdown pages.")
        doc_files = files.documentation_pages(inclusion=inclusion)

        with logfire.span("build_pages"):
            for file in doc_files:
                assert file.page
                excl = file.inclusion.is_excluded()
                with logfire.span(f"build_page {file.page.url}", page=file.page):
                    self._build_page(file.page, doc_files, nav, env, dirty, excl)

        log_level = self.config.validation.links.anchors
        with logfire.span("validate_anchor_links"):
            for file in doc_files:
                assert file.page is not None
                file.page.validate_anchor_links(files=files, log_level=log_level)

    def _build_page(
        self,
        page: Page,
        doc_files: Sequence[File],
        nav: Navigation,
        env: jinja2.Environment,
        dirty: bool = False,
        excluded: bool = False,
    ) -> None:
        """Build a single page.

        Args:
            page: Page to build
            doc_files: Collection of documentation files
            nav: Navigation structure
            env: Jinja environment
            dirty: Whether this is a dirty build
            excluded: Whether the page is excluded
        """
        self.config._current_page = page
        try:
            if dirty and not page.file.is_modified():
                return

            logger.debug("Building page %s", page.file.src_uri)
            page.active = True

            ctx = templatecontext.get_context(nav, doc_files, self.config, page)
            template = env.get_template(page.meta.get("template", "main.html"))
            ctx = self.config.plugins.on_page_context(
                ctx,  # type: ignore
                page=page,
                config=self.config,  # type: ignore
                nav=nav,
            )

            if excluded:
                page.content = DRAFT_CONTENT + (page.content or "")

            output = template.render(ctx)
            output = self.config.plugins.on_post_page(
                output, page=page, config=self.config
            )

            if output.strip():
                text = output.encode("utf-8", errors="xmlcharrefreplace")
                pathhelpers.write_file(text, page.file.abs_dest_path)
            else:
                logger.info(
                    "Page skipped: '%s'. Generated empty output.", page.file.src_uri
                )

        except Exception as e:
            message = f"Error building page '{page.file.src_uri}':"
            if not isinstance(e, exceptions.BuildError):
                message += f" {e}"
            logger.exception(message)
            raise
        finally:
            page.active = False
            self.config._current_page = None

    def _build_template(
        self,
        name: str,
        template: jinja2.Template,
        files: Files,
        nav: Navigation,
    ) -> str:
        """Build a template and return its rendered output.

        Args:
            name: Template name
            template: Template object
            files: Collection of files
            nav: Navigation structure

        Returns:
            Rendered template as string
        """
        template = self.config.plugins.on_pre_template(
            template, template_name=name, config=self.config
        )

        if utils.is_error_template(name):
            base_url = urlsplit(self.config.site_url or "/").path
        else:
            base_url = htmlfilters.relative_url_mkdocs(".", name)

        context = templatecontext.get_context(nav, files, self.config, base_url=base_url)
        ctx = self.config.plugins.on_template_context(
            context,  # type: ignore
            template_name=name,
            config=self.config,  # type: ignore
        )
        output = template.render(ctx)
        return self.config.plugins.on_post_template(
            output, template_name=name, config=self.config
        )

    def _build_theme_template(
        self,
        template_name: str,
        env: jinja2.Environment,
        files: Files,
        nav: Navigation,
    ) -> None:
        """Build a theme template.

        Args:
            template_name: Name of the template
            env: Jinja environment
            files: Collection of files
            nav: Navigation structure
        """
        logger.debug("Building theme template: %s", template_name)

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            logger.warning("Template skipped: %r not found in theme dirs.", template_name)
            return

        output = self._build_template(template_name, template, files, nav)

        if output.strip():
            output_path = upath.UPath(self.config.site_dir) / template_name
            pathhelpers.write_file(output.encode(), output_path)
            if template_name == "sitemap.xml":
                docs = files.documentation_pages()
                pages = [f.page for f in docs if f.page is not None]
                ts = utils.get_build_timestamp(pages=pages)
                utils.write_gzip(f"{output_path}.gz", output, timestamp=ts)
        else:
            logger.info("Template skipped: %r generated empty output.", template_name)

    def _build_extra_template(
        self,
        template_name: str,
        files: Files,
        nav: Navigation,
    ) -> None:
        """Build a user template not part of the theme.

        Args:
            template_name: Name of the template
            files: Collection of files
            nav: Navigation structure
        """
        logger.debug("Building extra template: %s", template_name)

        file = files.get_file_from_path(template_name)
        if file is None:
            logger.warning("Template skipped: %r not found in docs_dir.", template_name)
            return

        try:
            template = jinja2.Template(file.content_string)
        except Exception:
            logger.exception("Error reading template %r", template_name)
            return

        output = self._build_template(template_name, template, files, nav)
        if output.strip():
            pathhelpers.write_file(output.encode(), file.abs_dest_path)
        else:
            logger.info("Template skipped: %r generated empty output.", template_name)


# Backward compatibility functions
def build(
    config_path: str | os.PathLike[str],
    repo_path: str,
    build_fn: str | None,
    *,
    site_dir: str | None = None,
    clone_depth: int = 100,
    **kwargs: Any,
) -> None:
    """Build a MkNodes-based website.

    Args:
        config_path: Path to the MkDocs config file
        repo_path: Repository path/URL to build docs for
        build_fn: Fully qualified name of build function to use
        site_dir: Output directory for built site
        clone_depth: Number of commits to fetch for Git repos
        kwargs: Additional config overrides passed to MkDocs
    """
    md_builder = MarkdownBuilder()
    nav, files = md_builder.build_from_config(
        config_path=config_path,
        repo_path=repo_path,
        build_fn=build_fn,
        site_dir=site_dir,
        clone_depth=clone_depth,
        **kwargs,
    )

    html_builder = HTMLBuilder(md_builder.config)
    html_builder.build_html(nav, files)


def _build(
    config: MkNodesConfig,
    live_server_url: str | None = None,
    dirty: bool = False,
) -> None:
    """Build a MkNodes-based website. Also used for serving.

    Args:
        config: Config to use
        live_server_url: An optional URL of the live server to use
        dirty: Do a dirty build
    """
    md_builder = MarkdownBuilder(config)
    nav, files = md_builder.process_markdown(dirty=dirty)

    html_builder = HTMLBuilder(config)
    html_builder.build_html(
        nav=nav,
        files=files,
        live_server_url=live_server_url,
        dirty=dirty,
    )


if __name__ == "__main__":
    from mkdocs_mknodes.appconfig import appconfig

    app_cfg = appconfig.AppConfig.from_yaml_file("mkdocs.yml")
    print(app_cfg.model_dump())
    build("mkdocs.yml", ".", "mkdocs_mknodes.manual.root:Build.build")
