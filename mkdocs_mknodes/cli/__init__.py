"""MkDocs-MkNodes CLI interface."""

from __future__ import annotations

import contextlib
from datetime import datetime
import inspect
import logging
import pathlib
import signal
import subprocess
from typing import TYPE_CHECKING, Any

import typer as t

from mknodes.utils import classhelpers, log
import mknodes as mk
import yamling

from mkdocs_mknodes.appconfig import appconfig
from mkdocs_mknodes import buildcollector, paths
from mkdocs_mknodes.cli import richstate
from mkdocs_mknodes.commands import build_page, serve as serve_
from mkdocs_mknodes.generator import watch as watch_
from mkdocs_mknodes.generator.settings import GeneratorSettings


if TYPE_CHECKING:
    from mkdocs_mknodes.writers import Writer


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
DEPTH_HELP = "Git clone depth in case repository is remote. Important for changelog generation."
CFG_PATH_HELP = "Path to the config file."
STRICT_HELP = "Strict mode (fails on warnings)"
THEME_HELP = "Theme to use for the build. Overrides config setting."
USE_DIR_URLS_HELP = "Use directory-style URLs."
VERBOSE_HELP = "Enable verbose output. (`DEBUG` level)"
QUIET_HELP = "Suppress output during build."
ENGINE_HELP = (
    "Site engine. `mkdocs` runs the MkDocs plugin, `zensical` generates the pages "
    "(see `generate`) and runs `zensical`."
)
GEN_ENGINE_HELP = "Engine to generate the site input for."
WATCH_HELP = "Keep running and regenerate when project sources change."
GEN_DIR_HELP = "Folder for generated pages (default: the docs dir)."


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
ENGINE_CMDS = "-e", "--engine"


def verbose(ctx: t.Context, _param: t.CallbackParam, value: bool):
    state = ctx.ensure_object(richstate.RichState)
    if value:
        state.stream.setLevel(logging.DEBUG)


def quiet(ctx: t.Context, _param: t.CallbackParam, value: bool):
    state = ctx.ensure_object(richstate.RichState)
    if value:
        state.stream.setLevel(logging.ERROR)


@cli.command()
def build(  # noqa: PLR0917
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    site_dir: str = t.Option("site", *SITE_DIR_CMDS, help=SITE_DIR_HELP),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    theme: str = t.Option("material", *THEME_CMDS, help=THEME_HELP),
    strict: bool = t.Option(False, *STRICT_CMDS, help=STRICT_HELP),
    use_directory_urls: bool = t.Option(True, *USE_DIR_URLS_CMDS, help=USE_DIR_URLS_HELP),
    engine: str = t.Option("mkdocs", *ENGINE_CMDS, help=ENGINE_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Create a MkNodes-based website, locally or remotely.

    Runs the build script on given repository (either locally or a hosted one), adapts
    the config file automatically and creates the HTML website in given site dir.

    With `--engine zensical`, this is `mkdocs-mknodes generate` followed by
    `zensical build -f <generated config>`.

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
    if engine != "mkdocs":
        settings = _load_settings(
            config_path=config_path,
            build_fn=build_fn,
            repo_path=repo_path,
            clone_depth=clone_depth,
            site_dir=site_dir if site_dir != "site" else None,
        )
        writer = _generate(settings, engine)
        args = ["--strict"] if strict else []
        raise t.Exit(subprocess.call(writer.build_command(extra_args=args)))
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
def serve(  # noqa: PLR0917
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    strict: bool = t.Option(False, *STRICT_CMDS, help=STRICT_HELP),
    theme: str = t.Option("material", *THEME_CMDS, help=THEME_HELP),
    use_directory_urls: bool = t.Option(True, *USE_DIR_URLS_CMDS, help=USE_DIR_URLS_HELP),
    engine: str = t.Option("mkdocs", *ENGINE_CMDS, help=ENGINE_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Serve a MkNodes-based website, locally or remotely.

    Runs the build script on given repository (either locally or a hosted one), adapts
    the config file automatically and serves a webpage on http://127.0.0.1/8000/.

    With `--engine zensical`, this is `mkdocs-mknodes generate --watch` running next to
    `zensical serve -f <generated config>`.

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
    if engine != "mkdocs":
        opts: dict[str, Any] = dict(
            config_path=config_path,
            build_fn=build_fn,
            repo_path=repo_path,
            clone_depth=clone_depth,
        )
        settings = _load_settings(**opts)
        writer = _generate(settings, engine)
        process = subprocess.Popen(writer.build_command(serve=True))
        signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)
        try:
            watch_.watch(
                settings,
                watch_.regenerate_in_subprocess(_generate_args(engine=engine, **opts)),
                should_stop=lambda: process.poll() is not None,
            )
        except KeyboardInterrupt:
            pass
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()
        raise t.Exit(process.returncode or 0)
    serve_.serve(
        config_path=config_path,
        build_fn=build_fn,
        repo_path=repo_path,
        clone_depth=clone_depth,
        strict=strict,
        theme=theme if theme != "material" else None,
        use_directory_urls=use_directory_urls,
    )


def _raise_keyboard_interrupt(*_args: Any) -> None:
    raise KeyboardInterrupt


def _load_settings(
    config_path: str | None,
    build_fn: str | None = None,
    repo_path: str | None = None,
    clone_depth: int | None = None,
    **overrides: Any,
) -> GeneratorSettings:
    cfg = config_path if config_path and pathlib.Path(config_path).is_file() else None
    if config_path and config_path != paths.CFG_DEFAULT and cfg is None:
        msg = f"Config file {config_path!r} does not exist."
        raise t.BadParameter(msg)
    return GeneratorSettings.load(
        config_file=cfg,
        build_fn=build_fn,
        repo_path=repo_path,
        clone_depth=clone_depth,
        **overrides,
    )


def _generate(settings: GeneratorSettings, engine: str) -> Writer:
    from mkdocs_mknodes.generator import generate_output
    from mkdocs_mknodes.writers import get_writer

    writer = get_writer(engine)(settings)
    output = generate_output(settings)
    cfg_path = writer.write(output)
    logger.info("Generated %s pages, config: %s", len(output.pages), cfg_path)
    return writer


def _generate_args(engine: str, **opts: Any) -> list[str]:
    names = {
        "config_path": "--config-path",
        "build_fn": "--build-fn",
        "repo_path": "--repo-url",
        "clone_depth": "--clone-depth",
        "generated_dir": "--generated-dir",
    }
    args = ["--engine", engine]
    for key, value in opts.items():
        if value is not None:
            args += [names[key], str(value)]
    return args


@cli.command()
def generate(  # noqa: PLR0917
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    engine: str = t.Option("zensical", *ENGINE_CMDS, help=GEN_ENGINE_HELP),
    generated_dir: str = t.Option(None, "--generated-dir", help=GEN_DIR_HELP),
    watch: bool = t.Option(False, "-w", "--watch", help=WATCH_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Generate the site input (pages, nav, assets, config) for a site engine.

    Runs the build function (`mkdocs_mknodes:parse` / the default website unless
    configured in the `mknodes` plugin section of `mkdocs.yml` or in `[tool.mknodes]`)
    and writes the generated pages into the docs dir plus a generated config
    (`mkdocs.generated.yml`) inheriting from `mkdocs.yml`.
    Build afterwards with `zensical build -f mkdocs.generated.yml`.
    """
    opts: dict[str, Any] = dict(
        config_path=config_path,
        build_fn=build_fn,
        repo_path=repo_path,
        clone_depth=clone_depth,
        generated_dir=generated_dir,
    )
    settings = _load_settings(**opts)
    _generate(settings, engine)
    if watch:
        regenerate = watch_.regenerate_in_subprocess(_generate_args(engine=engine, **opts))
        with contextlib.suppress(KeyboardInterrupt):
            watch_.watch(settings, regenerate)


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

    config = appconfig.AppConfig.from_yaml_file(paths.RESOURCES / "mkdocs_basic.yml")
    theme_name = theme or "material"
    if theme_name != "material":
        theme_dict = {"name": theme_name, "override_dir": "overrides"}
        config.set_theme(theme_dict)
    config.use_directory_urls = use_directory_urls
    skin = mk.Theme(theme_name)
    nav = mk.MkNav.with_context(repo_url=repo_path)
    builder = classhelpers.to_callable(build_fn)
    collector = buildcollector.BuildCollector([])

    async def main():
        result = builder(root=nav, theme=skin)
        if inspect.iscoroutine(result):
            await result
        info = await collector.collect(nav, skin)
        resources = info.resources
        info = nav.ctx.metadata
        if social := info.social_info:
            config.extra["social"] = social  # type: ignore[index]
        config.markdown_extensions = resources.markdown_extensions
        config.repo_path = info.repository_url
        config.repo_url = info.repository_url  # type: ignore[assignment]
        config.site_description = info.summary
        config.site_name = info.distribution_name
        config.site_author = info.author_name
        config.copyright = f"Copyright © {datetime.now().year} {info.author_name}"
        result = yamling.dump_yaml(config.model_dump(exclude_unset=True, exclude_defaults=True))
        print(result)

    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    cli(["create-config"])
