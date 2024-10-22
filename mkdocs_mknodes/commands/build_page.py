"""The Mkdocs Plugin."""

from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import logfire
from mkdocs import exceptions
from mkdocs.commands import build as mkdocs_build
from mkdocs.config import load_config
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import InclusionLevel
from mkdocs.structure.nav import get_navigation
from mkdocs.structure.pages import Page
from mknodes.info import mkdocsconfigfile
from mknodes.utils import pathhelpers, yamlhelpers

from mkdocs_mknodes.commands import utils


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files


logger = get_plugin_logger(__name__)


def build(
    config_path: str | os.PathLike[str],
    repo_path: str,
    build_fn: str | None,
    site_dir: str | None = None,
    clone_depth: int = 100,
    **kwargs: Any,
):
    """Build a MkNodes-based website.

    Arguments:
        config_path: The path to the config file to use
        repo_path: Path to the repository a page should be built for
        build_fn: Callable to use for creating the webpage
        site_dir: Path for the website build
        clone_depth: If repository is remote, the amount of commits to fetch
        kwargs: Optional config values (overrides value from config)
    """

    def build_config():
        cfg = mkdocsconfigfile.MkDocsConfigFile(config_path)
        cfg.update_mknodes_section(
            repo_url=repo_path,
            build_fn=build_fn,
            clone_depth=clone_depth,
        )
        if site_dir:
            cfg["site_dir"] = site_dir
        text = yamlhelpers.dump_yaml(dict(cfg))
        buffer = io.StringIO(text)
        buffer.name = config_path
        config = load_config(buffer, **kwargs)
        for k, v in config.items():
            logger.debug("%s: %s", k, v)
        return config

    config = build_config()
    with logfire.span("plugins callback: on_startup", config=config):
        config.plugins.run_event("startup", command="build", dirty=False)
    _build(config)
    with logfire.span("plugins callback: shutdown", config=config):
        config.plugins.run_event("shutdown")


@utils.handle_exceptions
@utils.count_warnings
def _build(
    config: MkDocsConfig,
    live_server_url: str | None = None,
    dirty: bool = False,
) -> None:
    """Build a MkNodes-based website. Also used for serving.

    This method does NOT call the the startup / shutdown event hooks.
    If that is desired, build() should be called.

    Arguments:
        config: Config to use
        live_server_url: An optional URL of the live server to use
        dirty: Do a dirty build
    """
    inclusion = (
        InclusionLevel.is_in_serve if live_server_url else InclusionLevel.is_included
    )
    with logfire.span("plugins callback: on_config", config=config):
        config = config.plugins.on_config(config)
    with logfire.span("plugins callback: on_pre_build", config=config):
        config.plugins.on_pre_build(config=config)

    if not dirty:
        logger.info("Cleaning site directory")
        pathhelpers.clean_directory(config.site_dir)
    else:  # pragma: no cover
        logger.warning("A 'dirty' build is being performed (for site dev purposes only)")
    if not live_server_url:  # pragma: no cover
        logger.info("Building documentation to directory: %s", config.site_dir)
        if dirty and mkdocs_build.site_directory_contains_stale_files(config.site_dir):
            logger.info("The directory contains stale files. Use --clean to remove them.")
    # First gather all data from all files/pages to ensure all data is
    # consistent across all pages.
    files = utils.get_files(config)
    env = config.theme.get_env()
    files.add_files_from_theme(env, config)
    with logfire.span("plugins callback: on_files", files=files, config=config):
        files = config.plugins.on_files(files, config=config)
    # If plugins have added files without setting inclusion level, calculate it again.
    utils.set_exclusions(files._files, config)
    nav = get_navigation(files, config)
    # Run `nav` plugin events.
    with logfire.span("plugins callback: on_nav", config=config, nav=nav):
        nav = config.plugins.on_nav(nav, config=config, files=files)
    logger.debug("Reading markdown pages.")
    excluded: list[str] = []
    with logfire.span("populate pages"):
        for file in files.documentation_pages(inclusion=inclusion):
            with logfire.span(f"populate page for {file.src_uri}", file=file):
                logger.debug("Reading: %s", file.src_uri)
                if file.page is None and file.inclusion.is_not_in_nav():
                    if live_server_url and file.inclusion.is_excluded():
                        excluded.append(urljoin(live_server_url, file.url))
                    Page(None, file, config)
                assert file.page is not None
                _populate_page(file.page, config, files, dirty)
    if excluded:
        excluded_str = "\n  - ".join(excluded)
        logger.info(
            "The following pages are being built only for the preview "
            "but will be excluded from `mkdocs build` per `draft_docs` config:"
            "\n  - %s",
            excluded_str,
        )
    with logfire.span("plugins callback: on_env", env=env, config=config):
        env = config.plugins.on_env(env, config=config, files=files)
    logger.debug("Copying static assets.")
    with logfire.span("copy_static_files"):
        files.copy_static_files(dirty=dirty, inclusion=inclusion)

    with logfire.span("build_templates"):
        for template in config.theme.static_templates:
            mkdocs_build._build_theme_template(template, env, files, config, nav)
        for template in config.extra_templates:
            mkdocs_build._build_extra_template(template, files, config, nav)

    logger.debug("Building markdown pages.")
    doc_files = files.documentation_pages(inclusion=inclusion)
    with logfire.span("build_pages"):
        for file in doc_files:
            assert file.page
            excl = file.inclusion.is_excluded()
            with logfire.span(f"build_page {file.page.url}", page=file.page):
                mkdocs_build._build_page(
                    file.page, config, doc_files, nav, env, dirty, excl
                )

    log_level = config.validation.links.anchors
    with logfire.span("validate_anchor_links"):
        for file in doc_files:
            assert file.page is not None
            file.page.validate_anchor_links(files=files, log_level=log_level)
    # Run `post_build` plugin events.
    with logfire.span("plugins callback: on_post_build", config=config):
        config.plugins.on_post_build(config=config)


def _populate_page(
    page: Page, config: MkDocsConfig, files: Files, dirty: bool = False
) -> None:
    """Read page content from docs_dir and render Markdown."""
    config._current_page = page
    try:
        # When --dirty is used, only read the page if the file has been modified since the
        # previous build of the output.
        if dirty and not page.file.is_modified():
            return

        with logfire.span("plugins callback: on_pre_page", page=page, config=config):
            # Run the `pre_page` plugin event
            page = config.plugins.on_pre_page(page, config=config, files=files)

        with logfire.span("read_source", page=page):
            page.read_source(config)
        assert page.markdown is not None

        # Run `page_markdown` plugin events.
        with logfire.span("plugins callback: on_page_markdown", page=page, config=config):
            page.markdown = config.plugins.on_page_markdown(
                page.markdown, page=page, config=config, files=files
            )
        with logfire.span("render", page=page, config=config):
            page.render(config, files)
        assert page.content is not None

        with logfire.span("plugins callback: on_page_content", page=page, config=config):
            page.content = config.plugins.on_page_content(
                page.content, page=page, config=config, files=files
            )
    except Exception as e:
        message = f"Error reading page '{page.file.src_uri}':"
        # Prevent duplicated error msg because it will be printed immediately afterwards.
        if not isinstance(e, exceptions.BuildError):
            message += f" {e}"
        logger.exception(message)
        raise
    finally:
        config._current_page = None


if __name__ == "__main__":
    config = mkdocsconfigfile.MkDocsConfigFile("mkdocs.yml")
    print(config.dump_config())
    build("mkdocs.yml", ".", "mkdocs_mknodes.manual.root:Build.build")
