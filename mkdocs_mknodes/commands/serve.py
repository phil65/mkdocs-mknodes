from __future__ import annotations

import contextlib
import io
import os
import pathlib
import shutil
import tempfile

from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlsplit

# from mkdocs.commands import serve as serve_
from mkdocs.config import load_config
from mkdocs.livereload import LiveReloadServer
from mknodes.info import mkdocsconfigfile
from mknodes.utils import log, yamlhelpers

from mkdocs_mknodes import paths
from mkdocs_mknodes.commands import build_page


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

logger = log.get_logger(__name__)


def serve(
    config_path: str | os.PathLike = paths.CFG_DEFAULT,
    repo_path: str = ".",
    build_fn: str = paths.DEFAULT_BUILD_FN,
    clone_depth: int = 100,
    theme: str | None = None,
    **kwargs: Any,
):
    """Serve a MkNodes-based website.

    Arguments:
        config_path: The path to the config file to use
        repo_path: Path to the repository a page should be built for
        build_fn: Callable to use for creating the webpage
        clone_depth: If repository is remote, the amount of commits to fetch
        theme: Theme to use
        kwargs: Optional config values (overrides value from config)
    """
    config = mkdocsconfigfile.MkDocsConfigFile(config_path)
    config.update_mknodes_section(
        repo_url=repo_path,
        build_fn=build_fn,
        clone_depth=clone_depth,
    )
    if theme and theme != "material":
        config.remove_plugin("social")
        config.remove_plugin("tags")
        kwargs["theme"] = theme
    text = yamlhelpers.dump_yaml(dict(config))
    stream = io.StringIO(text)
    stream.name = str(config_path)
    _serve(config_file=stream, livereload=False, **kwargs)  # type: ignore[arg-type]


def serve_node(node, repo_path: str = "."):
    text = f"""
    import mknodes

    def build(project):
        page = project.root.add_page(is_index=True, hide="toc")
        page += '''{node!s}'''


    """
    p = pathlib.Path("docs/test.py")
    p.write_text(text)
    serve(repo_url=repo_path, site_script=p)


@contextlib.contextmanager
def catch_exceptions(config, site_dir):
    try:
        yield
    finally:
        config.plugins.on_shutdown()
        if pathlib.Path(site_dir).is_dir():
            shutil.rmtree(site_dir)


def _serve(
    config_file: str | None = None,
    livereload: bool = True,
    build_type: Literal["clean", "dirty"] | None = None,
    watch_theme: bool = False,
    watch: list[str] | None = None,
    **kwargs,
) -> None:
    """Start the MkDocs development server.

    By default it will serve the documentation on http://localhost:8000/ and
    it will rebuild the documentation and refresh the page automatically
    whenever a file is edited.

    Arguments:
        config_file: Config file to use
        livereload: Reload on file changes
        build_type: Type of the build
        watch_theme: Whether to watch the theme for file changes
        watch: Additional files / folders to watch
        kwargs: Additional config values. Overrides values from config_file
    """
    watch = watch or []
    site_dir = pathlib.Path(tempfile.mkdtemp(prefix="mkdocs_"))

    def mount_path(config: MkDocsConfig) -> str:
        return urlsplit(config.site_url or "/").path

    def get_config() -> MkDocsConfig:
        config = load_config(config_file=config_file, site_dir=str(site_dir), **kwargs)
        config.watch.extend(watch)
        config.site_url = f"http://{config.dev_addr}{mount_path(config)}"
        return config

    is_clean = build_type == "clean"
    is_dirty = build_type == "dirty"

    config = get_config()
    config.plugins.on_startup(command=("build" if is_clean else "serve"), dirty=is_dirty)

    host, port = config.dev_addr
    suffix = mount_path(config).lstrip("/").rstrip("/")
    url = None if is_clean else f"http://{host}:{port}/{suffix}/"

    def builder(config: MkDocsConfig | None = None):
        logger.info("Building documentation...")
        if config is None:
            config = get_config()
        build_page._build(config, live_server_url=url, dirty=is_dirty)

    server = LiveReloadServer(
        builder=builder,
        host=host,
        port=port,
        root=str(site_dir),
        mount_path=mount_path(config),
    )

    def error_handler(code: int) -> bytes | None:
        if code not in (404, 500):
            return None
        error_page = site_dir / f"{code}.html"
        return error_page.read_bytes() if error_page.is_file() else None

    server.error_handler = error_handler

    try:
        # Perform the initial build
        builder(config)

        if livereload:
            # Watch the documentation files, the config file and the theme files.
            server.watch(config.docs_dir)
            if config.config_file_path:
                server.watch(config.config_file_path)

            if watch_theme:
                for d in config.theme.dirs:
                    server.watch(d)

            # Run `serve` plugin events.
            server = config.plugins.on_serve(server, config=config, builder=builder)

            for item in config.watch:
                server.watch(item)

        try:
            server.serve()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            server.shutdown()
    finally:
        config.plugins.on_shutdown()
        if site_dir.is_dir():
            shutil.rmtree(site_dir)
