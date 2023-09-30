from __future__ import annotations

from collections.abc import Mapping
import contextlib
import io
import os
import pathlib
import shutil
import tempfile

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import jinja2.exceptions


# from mkdocs.commands import serve as serve_
from mkdocs.config import load_config
from mkdocs.exceptions import Abort
from mkdocs.livereload import LiveReloadServer
from mknodes import paths
from mknodes.utils import log, yamlhelpers

from mkdocs_mknodes.plugin import build_page


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

logger = log.get_logger(__name__)


def serve(
    config: str | os.PathLike | MkDocsConfig | Mapping[str, Any] = paths.CFG_DEFAULT,
    **kwargs,
):
    """Serve a MkNodes-based website."""
    match config:
        case str() | os.PathLike():
            text = pathlib.Path(config).read_text(encoding="utf-8")
        case _:
            text = yamlhelpers.dump_yaml(dict(config))
    stream = io.StringIO(text)
    _serve(config_file=stream, livereload=False, **kwargs)  # type: ignore[arg-type]


def serve_node(node, repo_path: str = "."):
    text = f"""
    import mknodes

    def build(project):
        root = project.get_root()
        page = root.add_index_page(hide="toc")
        page += '''{node!s}'''


    """
    p = pathlib.Path("docs/test.py")
    p.write_text(text)
    serve(repo_url=repo_path, site_script=p)


@contextlib.contextmanager
def catch_exceptions(config, site_dir):
    try:
        yield
    except jinja2.exceptions.TemplateError:
        # This is a subclass of OSError, but shouldn't be suppressed.
        raise
    except OSError as e:  # pragma: no cover
        # Avoid ugly, unhelpful traceback
        msg = f"{type(e).__name__}: {e}"
        raise Abort(msg) from e
    finally:
        config.plugins.on_shutdown()
        if pathlib.Path(site_dir).is_dir():
            shutil.rmtree(site_dir)


def _serve(
    config_file: str | None = None,
    livereload: bool = True,
    build_type: str | None = None,
    watch_theme: bool = False,
    watch: list[str] | None = None,
    **kwargs,
) -> None:
    """Start the MkDocs development server.

    By default it will serve the documentation on http://localhost:8000/ and
    it will rebuild the documentation and refresh the page automatically
    whenever a file is edited.
    """
    watch = watch or []
    site_dir = pathlib.Path(tempfile.mkdtemp(prefix="mkdocs_"))

    def mount_path(config: MkDocsConfig):
        return urlsplit(config.site_url or "/").path

    def get_config():
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

    def error_handler(code) -> bytes | None:
        if code not in (404, 500):
            return None
        error_page = site_dir / f"{code}.html"
        if not error_page.is_file():
            return None
        with error_page.open("rb") as f:
            return f.read()

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
    except jinja2.exceptions.TemplateError:
        # This is a subclass of OSError, but shouldn't be suppressed.
        raise
    except OSError as e:  # pragma: no cover
        # Avoid ugly, unhelpful traceback
        msg = f"{type(e).__name__}: {e}"
        raise Abort(msg) from None
    finally:
        config.plugins.on_shutdown()
        if site_dir.is_dir():
            shutil.rmtree(site_dir)

    # # Perform the initial build
    # with catch_exceptions(config, site_dir):
    #     builder(config)

    # server = LiveReloadServer(
    #     builder=builder,
    #     host=host,
    #     port=port,
    #     root=site_dir,
    #     mount_path=mount_path(config),
    # )

    # def error_handler(code) -> bytes | None:
    #     if code not in (404, 500):
    #         return None
    #     error_page = pathlib.Path(site_dir) / f"{code}.html"
    #     if not error_page.is_file():
    #         return None
    #     with error_page.open("rb") as f:
    #         return f.read()

    # # Run the server
    # server.error_handler = error_handler
    # with catch_exceptions(config, site_dir):
    #     run_server(server, config, builder, livereload, watch_theme)


# def run_server(server, config, builder, livereload, watch_theme):
#     if livereload:
#         # Watch the documentation files, the config file and the theme files.
#         server.watch(config.docs_dir)
#         if config.config_file_path:
#             server.watch(config.config_file_path)

#         if watch_theme:
#             for d in config.theme.dirs:
#                 server.watch(d)

#         # Run `serve` plugin events.
#         server = config.plugins.on_serve(server, config=config, builder=builder)

#         for item in config.watch:
#             server.watch(item)

#     try:
#         server.serve()
#     except KeyboardInterrupt:
#         logger.info("Shutting down...")
#     finally:
#         server.shutdown()
