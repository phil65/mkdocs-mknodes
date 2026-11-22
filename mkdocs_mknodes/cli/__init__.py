"""MkDocs-MkNodes CLI interface."""

from __future__ import annotations

import contextlib
import logging
import pathlib
import signal
import subprocess
from typing import TYPE_CHECKING, Any

import typer as t

from mknodes.utils import log

from mkdocs_mknodes import paths
from mkdocs_mknodes.cli import richstate
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
VERBOSE_HELP = "Enable verbose output. (`DEBUG` level)"
QUIET_HELP = "Suppress output during build."
ENGINE_HELP = "Site engine. Only `zensical` (the default) is supported."
WATCH_HELP = "Keep running and regenerate when project sources change."
GEN_DIR_HELP = "Folder for generated pages (default: the docs dir)."


REPO_CMDS = "-r", "--repo-url"
SITE_DIR_CMDS = "-d", "--site-dir"
BUILD_CMS = "-b", "--build-fn"
DEPTH_CMDS = "-c", "--clone-depth"
CFG_PATH_CMDS = "-p", "--config-path"
STRICT_CMDS = "-s", "--strict"
VERBOSE_CMDS = "-v", "--verbose"
QUIET_CMDS = "-q", "--quiet"
ENGINE_CMDS = "-e", "--engine"
DEFAULT_ENGINE = "zensical"


def verbose(ctx: t.Context, _param: t.CallbackParam, value: bool):
    state = ctx.ensure_object(richstate.RichState)
    if value:
        state.set_level(logging.DEBUG)


def quiet(ctx: t.Context, _param: t.CallbackParam, value: bool):
    state = ctx.ensure_object(richstate.RichState)
    if value:
        state.set_level(logging.ERROR)


def check_engine(value: str) -> str:
    """Only accept engines with a writer (the option is kept for compatibility)."""
    from mkdocs_mknodes.writers import WRITERS

    if value not in WRITERS:
        msg = (
            f"Unsupported engine {value!r} (available: {', '.join(WRITERS)}). "
            "The MkDocs engine was removed in mkdocs-mknodes 2.0: MkNodes generates the "
            "pages and Zensical builds the site."
        )
        raise t.BadParameter(msg)
    return value


def _engine_option() -> Any:
    return t.Option(DEFAULT_ENGINE, *ENGINE_CMDS, help=ENGINE_HELP, callback=check_engine)


@cli.command()
def build(  # noqa: PLR0917
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    site_dir: str = t.Option(None, *SITE_DIR_CMDS, help=SITE_DIR_HELP, show_default=False),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    strict: bool = t.Option(False, *STRICT_CMDS, help=STRICT_HELP),
    engine: str = _engine_option(),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Build a MkNodes-based website, locally or remotely.

    Runs the build function on given repository (either locally or a hosted one),
    writes the generated pages and config (see `generate`) and builds the HTML website
    with `zensical build -f <generated config>`.

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
    settings = _load_settings(
        config_path=config_path,
        build_fn=build_fn,
        repo_path=repo_path,
        clone_depth=clone_depth,
        site_dir=site_dir,
    )
    writer = _generate(settings, engine)
    args = ["--strict"] if strict else []
    raise t.Exit(subprocess.call(writer.build_command(extra_args=args)))


@cli.command()
def serve(
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    engine: str = _engine_option(),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Serve a MkNodes-based website, locally or remotely.

    This is `mkdocs-mknodes generate --watch` running next to
    `zensical serve -f <generated config>` (serves on http://localhost:8000/).

    Further info here: https://phil65.github.io/mkdocs-mknodes/CLI/
    """
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


@cli.command()
def generate(  # noqa: PLR0917
    repo_path: str = t.Option(None, *REPO_CMDS, help=REPO_HELP, show_default=False),
    build_fn: str = t.Option(None, *BUILD_CMS, help=BUILD_HELP, show_default=False),
    clone_depth: int = t.Option(None, *DEPTH_CMDS, help=DEPTH_HELP, show_default=False),
    config_path: str = t.Option(paths.CFG_DEFAULT, *CFG_PATH_CMDS, help=CFG_PATH_HELP),
    engine: str = _engine_option(),
    generated_dir: str = t.Option(None, "--generated-dir", help=GEN_DIR_HELP),
    watch: bool = t.Option(False, "-w", "--watch", help=WATCH_HELP),
    _verbose: bool = t.Option(False, *VERBOSE_CMDS, help=VERBOSE_HELP, callback=verbose),
    _quiet: bool = t.Option(False, *QUIET_CMDS, help=QUIET_HELP, callback=quiet),
):
    """Generate the site input (pages, nav, assets, config) for the site engine.

    Runs the build function (`mkdocs_mknodes:parse` / the default website unless
    configured in `[tool.mknodes]` of `pyproject.toml` or in the `mknodes` entry of the
    `plugins` list of `mkdocs.yml`) and writes the generated pages into the docs dir plus
    a generated config (`mkdocs.generated.yml`) inheriting from `mkdocs.yml`.
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


if __name__ == "__main__":
    cli(["build"])
