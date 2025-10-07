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
from mknodes.utils import log
from upath.types import JoinablePathLike
from upathtools import to_upath
import yamling

from mkdocs_mknodes import liveserver, paths
from mkdocs_mknodes.commands import build_page
from mkdocs_mknodes.plugin import mknodesconfig


if TYPE_CHECKING:
    pass

logger = log.get_logger(__name__)

AnyPath = str | os.PathLike[str] | JoinablePathLike


def serve(
    config_path: AnyPath = paths.CFG_DEFAULT,
    theme: str | None = None,
    **kwargs: Any,
):
    """Serve a MkNodes-based website.

    Args:
        config_path: The path to the config file to use
        theme: Theme to use
        kwargs: Optional config values (overrides value from config)
    """
    if theme and theme != "material":
        kwargs["theme"] = theme
    text = to_upath(config_path).read_text("utf-8")
    stream = io.StringIO(text)
    stream.name = str(config_path)
    _serve(config_file=stream, livereload=False, **kwargs)  # type: ignore[arg-type]


@contextlib.contextmanager
def catch_exceptions(config: mknodesconfig.MkNodesConfig):
    """Context manager used to clean up in case of build error.

    Args:
        config: Build config.
    """
    try:
        yield
    finally:
        config.plugins.on_shutdown()
        if pathlib.Path(config.site_dir).is_dir():
            shutil.rmtree(config.site_dir)


def _serve(
    config_file: str | None | yamling.YAMLInput = None,
    livereload: bool = True,
    build_type: Literal["clean", "dirty"] | None = None,
    watch_theme: bool = False,
    watch: list[str] | None = None,
    **kwargs: Any,
) -> None:
    """Start the MkDocs development server.

    By default it will serve the documentation on http://localhost:8000/ and
    it will rebuild the documentation and refresh the page automatically
    whenever a file is edited.

    Args:
        config_file: Config file to use
        livereload: Reload on file changes
        build_type: Type of the build
        watch_theme: Whether to watch the theme for file changes
        watch: Additional files / folders to watch
        kwargs: Additional config values. Overrides values from config_file
    """
    watch = watch or []
    site_dir = pathlib.Path(tempfile.mkdtemp(prefix="mkdocs_"))

    def mount_path(config: mknodesconfig.MkNodesConfig) -> str:
        return urlsplit(config.site_url or "/").path

    def get_config() -> mknodesconfig.MkNodesConfig:
        config = mknodesconfig.MkNodesConfig.from_yaml(
            config_file=config_file,  # type: ignore[arg-type]
            site_dir=str(site_dir),
            **kwargs,
        )
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

    def builder(config: mknodesconfig.MkNodesConfig | None = None):
        logger.info("Building documentation...")
        if config is None:
            config = get_config()
        build_page._build(config, live_server_url=url, dirty=is_dirty)

    server = liveserver.LiveServer(
        builder=builder,
        host=host,
        port=port,
        root=str(site_dir),
        mount_path=mount_path(config),
    )

    with catch_exceptions(config):
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
            server = config.plugins.on_serve(server, config=config, builder=builder)  # type: ignore[arg-type]

            for item in config.watch:
                server.watch(item)

        try:
            server.serve()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            server.shutdown()
