"""The Mkdocs Plugin."""

from __future__ import annotations

from collections.abc import Callable
import functools
import io
import logging
import os
import time

from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from mkdocs import utils
from mkdocs.commands import build as mkdocs_build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort, BuildError
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import InclusionLevel, _set_exclusions, get_files
from mkdocs.structure.nav import get_navigation
from mkdocs.structure.pages import Page
from mknodes.info import mkdocsconfigfile
from mknodes.utils import pathhelpers, yamlhelpers


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


logger = get_plugin_logger(__name__)


def build(
    config_path: str | os.PathLike,
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
    config.plugins.run_event("startup", command="build", dirty=False)
    _build(config)
    config.plugins.run_event("shutdown")


def count_warnings(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapped(config: MkDocsConfig, *args, **kwargs):
        start = time.monotonic()
        warning_counter = utils.CountHandler()
        warning_counter.setLevel(logging.WARNING)
        if config.strict:
            logging.getLogger("mkdocs").addHandler(warning_counter)
        result = fn(config, *args, **kwargs)
        counts = warning_counter.get_counts()
        if counts:
            msg = ", ".join(f"{v} {k.lower()}s" for k, v in counts)
            msg = f"Aborted with {msg} in strict mode!"
            raise Abort(msg)
        duration = time.monotonic() - start
        logger.info("Documentation built in %.2f seconds", duration)
        logging.getLogger("mkdocs").removeHandler(warning_counter)

        return result

    return wrapped


def handle_exceptions(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapped(config: MkDocsConfig, *args, **kwargs):
        try:
            return fn(config, *args, **kwargs)
        except Exception as e:
            # Run `build_error` plugin events.
            config.plugins.on_build_error(error=e)
            if isinstance(e, BuildError):
                msg = "Aborted with a BuildError!"
                logger.exception(msg)
                raise Abort(msg) from e
            raise
        # finally:
        # logging.getLogger("mkdocs").removeHandler(warning_counter)

    return wrapped


@handle_exceptions
@count_warnings
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
    inclusion = InclusionLevel.all if live_server_url else InclusionLevel.is_included
    config = config.plugins.on_config(config)
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
    files = get_files(config)
    env = config.theme.get_env()
    files.add_files_from_theme(env, config)
    files = config.plugins.on_files(files, config=config)
    # If plugins have added files without setting inclusion level, calculate it again.
    _set_exclusions(files._files, config)
    nav = get_navigation(files, config)
    # Run `nav` plugin events.
    nav = config.plugins.on_nav(nav, config=config, files=files)
    logger.debug("Reading markdown pages.")
    excluded = []
    for file in files.documentation_pages(inclusion=inclusion):
        logger.debug("Reading: %s", file.src_uri)
        if file.page is None and file.inclusion.is_excluded():
            if live_server_url:
                excluded.append(urljoin(live_server_url, file.url))
            Page(None, file, config)
        assert file.page is not None
        mkdocs_build._populate_page(file.page, config, files, dirty)
    if excluded:
        excluded_str = "\n  - ".join(excluded)
        logger.info(
            "The following pages are being built only for the preview "
            "but will be excluded from `mkdocs build` per `exclude_docs`:"
            "\n  - %s",
            excluded_str,
        )
    env = config.plugins.on_env(env, config=config, files=files)
    logger.debug("Copying static assets.")
    files.copy_static_files(dirty=dirty, inclusion=inclusion)

    for template in config.theme.static_templates:
        mkdocs_build._build_theme_template(template, env, files, config, nav)
    for template in config.extra_templates:
        mkdocs_build._build_extra_template(template, files, config, nav)

    logger.debug("Building markdown pages.")
    doc_files = files.documentation_pages(inclusion=inclusion)
    for file in doc_files:
        assert file.page
        excl = file.inclusion.is_excluded()
        mkdocs_build._build_page(file.page, config, doc_files, nav, env, dirty, excl)

    # Run `post_build` plugin events.
    config.plugins.on_post_build(config=config)
