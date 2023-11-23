"""MkDocs-MkNodes CLI interface."""

from __future__ import annotations

from datetime import datetime
import logging
from mknodes.info.mkdocsconfigfile import MkDocsConfigFile

import typer as t

from mknodes.utils import classhelpers, log, yamlhelpers
import mknodes as mk

from mkdocs_mknodes import buildcollector, paths
from mkdocs_mknodes.cli import richstate
from mkdocs_mknodes.commands import build_page, serve as serve_


logger = log.get_logger(__name__)

cli = t.Typer(
    name="MkNodes",
    help=(
        " 🚀🚀🚀 MkNodes CLI interface. Build websites from command line! 🚀🚀🚀\n\n"
        "Check out https://phil65.github.io/mkdocs-mknodes/ !"
    ),
    no_args_is_help=True,
)

REPO_HELP = "Repository URL of the target package. Can be remote or local."
BUILD_HELP = "Path to the build script. (form: `path.to.module:function` )"
SITE_DIR_HELP = "Path to the folder where the HTML should get written."
DEPTH_HELP = (
    "Git clone depth in case repository is remote. Important for changelog generation."
)
CFG_PATH_HELP = "Path to the config file."
STRICT_HELP = "Strict mode (fails on warnings)"
THEME_HELP = "Theme to use for the build. Overrides config setting."
USE_DIR_URLS_HELP = "Use directory-style URLs."
VERBOSE_HELP = "Enable verbose output. (`DEBUG` level)"
QUIET_HELP = "Suppress output during build."


REPO_CMDS = "-r", "--repo-url"
SITE_DIR_CMDS = "-d", "--site-dir"
BUILD_CMS = "-b", "--build-fn"
DEPTH_CMDS = "-c", "--clone-depth"
CFG_PATH_CMDS = "-p", "--config-path"
STRICT_CMDS = "-s", "--strict"
THEME_CMDS = "-t", "--theme"
USE_DIR_URLS_CMDS = "--use-directory-urls/--no-directory-urls", "-u"
VERBOSE_CMDS = "-v", "--verbose"
QUIET_CMDS = "-q", "--quiet"


def verbose(ctx: t.Context, param: t.CallbackParam, value: bool):
    # sourcery skip: move-assign
    state = ctx.ensure_object(richstate.RichState)
    if value:
        state.stream.setLevel(logging.DEBUG)


def quiet(ctx: t.Context, param: t.CallbackParam, value: bool):
    # sourcery skip: move-assign
    state = ctx.ensure_object(richstate.RichState)
    if value:
        state.stream.setLevel(logging.ERROR)


@cli.command()
def build(
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    site_dir: str = t.Option("site", *SITE_DIR_CMDS, help=SITE_DIR_HELP),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    theme: str = t.Option("material", *THEME_CMDS, help=THEME_HELP),
    strict: bool = t.Option(False, *STRICT_CMDS, help=STRICT_HELP),
    use_directory_urls: bool = t.Option(True, *USE_DIR_URLS_CMDS, help=USE_DIR_URLS_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Create a MkNodes-based website, locally or remotely.

    Runs the build script on given repository (either locally or a hosted one), adapts
    the config file automatically and creates the HTML website in given site dir.

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
    build_page.build(
        config_path=config_path,
        repo_path=repo_path,
        build_fn=build_fn,
        clone_depth=clone_depth,
        site_dir=site_dir,
        strict=strict,
        theme=theme if theme != "material" else None,
        use_directory_urls=use_directory_urls,
    )


@cli.command()
def serve(
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    strict: bool = t.Option(False, *STRICT_CMDS, help=STRICT_HELP),
    theme: str = t.Option("material", *THEME_CMDS, help=THEME_HELP),
    use_directory_urls: bool = t.Option(True, *USE_DIR_URLS_CMDS, help=USE_DIR_URLS_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Serve a MkNodes-based website, locally or remotely.

    Runs the build script on given repository (either locally or a hosted one), adapts
    the config file automatically and serves a webpage on http://127.0.0.1/8000/.

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
    serve_.serve(
        config_path=config_path,
        build_fn=build_fn,
        repo_path=repo_path,
        clone_depth=clone_depth,
        strict=strict,
        theme=theme if theme != "material" else None,
        use_directory_urls=use_directory_urls,
    )


@cli.command()
def create_config(
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    # config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    theme: str = t.Option("material", *THEME_CMDS, help=THEME_HELP),
    use_directory_urls: bool = t.Option(True, *USE_DIR_URLS_CMDS, help=USE_DIR_URLS_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Create a config based on a given build setup.

    Runs the build script on given repository (either locally or a hosted one),
    infers the required resources (CSS / JS / Md extensions) as well as metadata
    and creates a MkDocs config file.

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
    build_fn = build_fn or paths.DEFAULT_BUILD_FN

    cfg_file = MkDocsConfigFile(paths.RESOURCES / "mkdocs_basic.yml")
    cfg_file.update_mknodes_section(repo_url=repo_path, build_fn=build_fn)
    theme_name = theme or "material"
    if theme_name != "material":
        cfg_file["theme"] = dict(name=theme_name, override_dir="overrides")
    cfg_file["use_directory_urls"] = use_directory_urls
    config = cfg_file._data
    skin = mk.Theme(theme_name)
    nav = mk.MkNav.with_context(repo_url=repo_path)
    builder = classhelpers.to_callable(build_fn)
    builder(context=nav.ctx)
    collector = buildcollector.BuildCollector([])
    info = collector.collect(nav, skin)
    resources = info.resources
    info = nav.ctx.metadata
    if social := info.social_info:
        config.setdefault("extra", {})["social"] = social  # type: ignore[index]
    config["markdown_extensions"] = resources.markdown_extensions
    config["repo_path"] = info.repository_url
    config["site_description"] = info.summary
    config["site_name"] = info.distribution_name
    config["site_author"] = info.author_name
    config["copyright"] = f"Copyright © {datetime.now().year} {info.author_name}"
    result = yamlhelpers.dump_yaml(config)
    print(result)


if __name__ == "__main__":
    cli(["create-config", "--build-fn", "mkdocs_mknodes:MkDefaultWebsite"])
