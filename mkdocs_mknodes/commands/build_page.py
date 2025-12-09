"""The Mkdocs Plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypedDict
from urllib.parse import urljoin, urlsplit

import jinja2
from jinja2.exceptions import TemplateNotFound
from jinjarope import envtests, htmlfilters
import logfire
from mkdocs import exceptions, utils as mkdocs_utils
from mkdocs.structure.files import Files, InclusionLevel
from mkdocs.structure.nav import get_navigation
from mkdocs.structure.pages import Page
from upathtools import helpers, to_upath

from mkdocs_mknodes import telemetry
from mkdocs_mknodes.builders import configbuilder
from mkdocs_mknodes.commands import utils


if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    import os

    from mkdocs.structure.files import File
    from mkdocs.structure.nav import Navigation

    from mkdocs_mknodes.plugin.mknodesconfig import MkNodesConfig


logger = telemetry.get_plugin_logger(__name__)


class TemplateContext(TypedDict):
    nav: Navigation
    pages: Sequence[File]
    base_url: str
    extra_css: Sequence[str]  # Do not use, prefer `config.extra_css`.
    extra_javascript: Sequence[str]  # Do not use, prefer `config.extra_javascript`.
    mkdocs_version: str
    mknodes_version: str
    build_date_utc: datetime
    config: MkNodesConfig
    page: Page | None


DRAFT_CONTENT = (
    '<div class="mkdocs-draft-marker" title="This page wont be included into the site.">DRAFT</div>'
)


def build(
    config_path: str | os.PathLike[str],
    repo_path: str,
    build_fn: str | None,
    *,
    site_dir: str | None = None,
    clone_depth: int = 100,
    **kwargs: Any,
):
    """Build a MkNodes-based website.

    Args:
        config_path: Path to the MkDocs config file
        repo_path: Repository path/URL to build docs for
        build_fn: Fully qualified name of build function to use
        site_dir: Output directory for built site
        clone_depth: Number of commits to fetch for Git repos
        kwargs: Additional config overrides passed to MkDocs
    """
    cfg_builder = configbuilder.ConfigBuilder(
        repo_path=repo_path, build_fn=build_fn, clone_depth=clone_depth
    )
    cfg_builder.add_config_file(config_path)
    config = cfg_builder.build_mkdocs_config(site_dir=site_dir, **kwargs)
    with logfire.span("plugins callback: on_startup", config=config):
        config.plugins.on_startup(command="build", dirty=False)
    _build(config)
    with logfire.span("plugins callback: shutdown", config=config):
        config.plugins.on_shutdown()


@utils.handle_exceptions
@utils.count_warnings
def _build(
    config: MkNodesConfig,
    live_server_url: str | None = None,
    dirty: bool = False,
) -> None:
    """Build a MkNodes-based website. Also used for serving.

    This method does NOT call the the startup / shutdown event hooks.
    If that is desired, build() should be called.

    Args:
        config: Config to use
        live_server_url: An optional URL of the live server to use
        dirty: Do a dirty build
    """
    with logfire.span("plugins callback: on_config", config=config):
        config = config.plugins.on_config(config)
    with logfire.span("plugins callback: on_pre_build", config=config):
        config.plugins.on_pre_build(config=config)

    if not dirty:
        logger.info("Cleaning site directory")
        helpers.clean_directory(config.site_dir)
    else:  # pragma: no cover
        logger.warning("A 'dirty' build is being performed (for site dev purposes only)")
    if not live_server_url:  # pragma: no cover
        logger.info("Building documentation to directory: %s", config.site_dir)
        if dirty and envtests.contains_files(config.site_dir):
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
    inclusion = InclusionLevel.is_in_serve if live_server_url else InclusionLevel.is_included
    with logfire.span("populate pages"):
        for file in files.documentation_pages(inclusion=inclusion):
            with logfire.span(f"populate page for {file.src_uri}", file=file):
                logger.debug("Reading: %s", file.src_uri)
                if file.page is None and file.inclusion.is_not_in_nav():
                    Page(None, file, config)
                    if live_server_url and file.inclusion.is_excluded():
                        excluded.append(urljoin(live_server_url, file.url))
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
            _build_theme_template(template, env, files, config, nav)
        for template in config.extra_templates:
            _build_extra_template(template, files, config, nav)

    logger.debug("Building markdown pages.")
    doc_files = files.documentation_pages(inclusion=inclusion)
    with logfire.span("build_pages"):
        for file in doc_files:
            assert file.page
            excl = file.inclusion.is_excluded()
            with logfire.span(f"build_page {file.page.url}", page=file.page):
                _build_page(file.page, config, doc_files, nav, env, dirty, excl)
    log_level = config.validation.links.anchors
    with logfire.span("validate_anchor_links"):
        for file in doc_files:
            assert file.page is not None
            file.page.validate_anchor_links(files=files, log_level=log_level)
    # Run `post_build` plugin events.
    with logfire.span("plugins callback: on_post_build", config=config):
        config.plugins.on_post_build(config=config)


def _populate_page(page: Page, config: MkNodesConfig, files: Files, dirty: bool = False) -> None:
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


def _build_page(
    page: Page,
    config: MkNodesConfig,
    doc_files: Sequence[File],
    nav: Navigation,
    env: jinja2.Environment,
    dirty: bool = False,
    excluded: bool = False,
) -> None:
    """Pass a Page to theme template and write output to site_dir."""
    config._current_page = page
    try:
        # only build pages if the file has been modified since the previous build
        if dirty and not page.file.is_modified():
            return
        logger.debug("Building page %s", page.file.src_uri)
        # Activate page. Signals to theme that this is the current page.
        page.active = True
        ctx = get_context(nav, doc_files, config, page)
        # Allow 'template:' override in md source files.
        template = env.get_template(page.meta.get("template", "main.html"))
        # Run `page_context` plugin events.
        ctx = config.plugins.on_page_context(ctx, page=page, config=config, nav=nav)  # type: ignore

        if excluded:
            page.content = DRAFT_CONTENT + (page.content or "")
        # Render the template.
        output = template.render(ctx)
        # Run `post_page` plugin events.
        output = config.plugins.on_post_page(output, page=page, config=config)

        # Write the output file.
        if output.strip():
            text = output.encode("utf-8", errors="xmlcharrefreplace")
            helpers.write_file(text, page.file.abs_dest_path)
        else:
            logger.info("Page skipped: '%s'. Generated empty output.", page.file.src_uri)

    except Exception as e:
        message = f"Error building page '{page.file.src_uri}':"
        # Prevent duplicated the error message because
        # it will be printed immediately afterwards.
        if not isinstance(e, exceptions.BuildError):
            message += f" {e}"
        logger.error(message)  # noqa: TRY400
        raise
    finally:
        # Deactivate page
        page.active = False
        config._current_page = None


def _build_template(
    name: str,
    template: jinja2.Template,
    files: Files,
    config: MkNodesConfig,
    nav: Navigation,
) -> str:
    """Return rendered output for given template as a string."""
    template = config.plugins.on_pre_template(template, template_name=name, config=config)

    if utils.is_error_template(name):
        # Force absolute URLs for error pages. Docs root & server root might differ.
        # See https://github.com/mkdocs/mkdocs/issues/77.
        # However, if site_url is not set, assume the docs root and server root
        # are the same. See https://github.com/mkdocs/mkdocs/issues/1598.
        base_url = urlsplit(config.site_url or "/").path
    else:
        base_url = htmlfilters.relative_url_mkdocs(".", name)
    context = get_context(nav, files, config, base_url=base_url)
    ctx = config.plugins.on_template_context(context, template_name=name, config=config)  # type: ignore
    output = template.render(ctx)
    return config.plugins.on_post_template(output, template_name=name, config=config)


def _build_theme_template(
    template_name: str,
    env: jinja2.Environment,
    files: Files,
    config: MkNodesConfig,
    nav: Navigation,
) -> None:
    """Build a template using the theme environment."""
    logger.debug("Building theme template: %s", template_name)

    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        logger.warning("Template skipped: %r not found in theme dirs.", template_name)
        return

    output = _build_template(template_name, template, files, config, nav)

    if output.strip():
        output_path = to_upath(config.site_dir) / template_name
        helpers.write_file(output.encode(), output_path)
        if template_name == "sitemap.xml":
            docs = files.documentation_pages()
            ts = get_build_timestamp(pages=[f.page for f in docs if f.page is not None])
            utils.write_gzip(f"{output_path}.gz", output, timestamp=ts)
    else:
        logger.info("Template skipped: %r generated empty output.", template_name)


def _build_extra_template(template_name: str, files: Files, config: MkNodesConfig, nav: Navigation):
    """Build user templates which are not part of the theme."""
    logger.debug("Building extra template: %s", template_name)

    file = files.get_file_from_path(template_name)
    if file is None:
        logger.warning("Template skipped: %r not found in docs_dir.", template_name)
        return
    try:
        template = jinja2.Template(file.content_string)
    except Exception as e:  # noqa: BLE001
        logger.warning("Error reading template %r: %s", template_name, e)
        return
    output = _build_template(template_name, template, files, config, nav)
    if output.strip():
        helpers.write_file(output.encode(), file.abs_dest_path)
    else:
        logger.info("Template skipped: %r generated empty output.", template_name)


def get_build_timestamp(*, pages: Collection[Page] | None = None) -> int:
    """Returns the number of seconds since the epoch for the latest updated page.

    In reality this is just today's date because that's how pages' update time
    is populated.

    Args:
        pages: Optional collection of pages to determine timestamp from

    Returns:
        Unix timestamp as integer
    """
    if pages:
        # Lexicographic comparison is OK for ISO date.
        date_string = max(p.update_date for p in pages)
        dt = datetime.fromisoformat(date_string).replace(tzinfo=UTC)
    else:
        dt = utils.get_build_datetime()
    return int(dt.timestamp())


def get_context(
    nav: Navigation,
    files: Sequence[File] | Files,
    config: MkNodesConfig,
    page: Page | None = None,
    base_url: str = "",
) -> TemplateContext:
    """Return the template context for a given page or template."""
    if page is not None:
        base_url = mkdocs_utils.get_relative_url(".", page.url)

    extra_javascript = [
        mkdocs_utils.normalize_url(str(script), page, base_url)
        for script in config.extra_javascript
    ]
    extra_css = [mkdocs_utils.normalize_url(path, page, base_url) for path in config.extra_css]

    if isinstance(files, Files):
        files = files.documentation_pages()

    import mkdocs

    import mkdocs_mknodes

    return TemplateContext(
        nav=nav,
        pages=files,
        base_url=base_url,
        extra_css=extra_css,
        extra_javascript=extra_javascript,
        mknodes_version=mkdocs_mknodes.__version__,
        mkdocs_version=mkdocs.__version__,
        build_date_utc=utils.get_build_datetime(),
        config=config,
        page=page,
    )


if __name__ == "__main__":
    from mkdocs_mknodes.appconfig import appconfig

    config = appconfig.AppConfig.from_yaml_file("mkdocs.yml")
    print(config.model_dump())
    build("mkdocs.yml", ".", "mkdocs_mknodes.manual.root:Build.build")
