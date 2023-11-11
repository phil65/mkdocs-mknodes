from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
import contextlib

from datetime import datetime
import functools
import io
import os
import pathlib
import sys
from typing import IO, Any
from urllib import parse

import jinja2
import jinjarope

from mkdocs.commands import get_deps
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger
from mknodes.info import contexts
from mknodes.mdlib import mdconverter
from mknodes.utils import pathhelpers, reprhelpers


logger = get_plugin_logger(__name__)


@contextlib.contextmanager
def _open_config_file(config_file: str | os.PathLike | IO | None) -> Iterator[IO]:
    """A context manager which yields an open file descriptor ready to be read.

    Accepts a filename as a string, an open or closed file descriptor, or None.
    When None, it defaults to `mkdocs.yml` in the CWD. If a closed file descriptor
    is received, a new file descriptor is opened for the same file.

    The file descriptor is automatically closed when the context manager block is existed.
    """
    match config_file:
        case None:
            paths_to_try = [pathlib.Path("mkdocs.yml")]
        case str() | os.PathLike():
            paths_to_try = [pathlib.Path(config_file)]
        case _ if getattr(config_file, "closed", False):
            # If closed file descriptor, get file path to reopen later.
            paths_to_try = [pathlib.Path(config_file.name)]
        case _:
            result_config_file = config_file
            paths_to_try = None

    if paths_to_try:
        # config_file is not a file descriptor, so open it as a path.
        for path in paths_to_try:
            path = path.resolve()
            logger.debug("Loading configuration file: %r", path)
            try:
                result_config_file = open(path, "rb")  # noqa: SIM115, PTH123
                break
            except FileNotFoundError:
                continue
        else:
            msg = f"Config file {paths_to_try[0]!r} does not exist."
            raise SystemExit(msg)
    else:
        logger.debug("Loading configuration file: %r", result_config_file)
        # Ensure file descriptor is at beginning
        with contextlib.suppress(OSError):
            result_config_file.seek(0)

    try:
        yield result_config_file
    finally:
        if hasattr(result_config_file, "close"):
            result_config_file.close()


@functools.cache
def load_config(
    config_file: str | IO | None = None,
    *,
    config_file_path: str | None = None,
    **kwargs,
) -> MkDocsConfig:
    """Load the configuration for a given file object or name.

    The config_file can either be a file object, string or None. If it is None
    the default `mkdocs.yml` filename will loaded.

    Extra kwargs are passed to the configuration to replace any default values
    unless they themselves are None.
    """
    options = {k: v for k, v in kwargs.copy().items() if v is not None}
    with _open_config_file(config_file) as fd:
        # Initialize the config with the default schema.

        if config_file_path is None and fd is not sys.stdin.buffer:
            config_file_path = getattr(fd, "name", None)
        cfg = MkDocsConfig(config_file_path=config_file_path)
        cfg.load_file(fd)

    # Then load the options to overwrite anything in the config.
    cfg.load_dict(options)

    errors, warnings = cfg.validate()

    for config_name, warning in warnings + errors:
        logger.warning("Config value %r: %s", config_name, warning)
    for k, v in cfg.items():
        logger.debug("Config value %r = %r", k, v)
    if len(errors) > 0:
        msg = f"Aborted with {len(errors)} configuration errors!"
        raise SystemExit(msg)
    if cfg.strict and len(warnings) > 0:
        msg = f"Aborted with {len(warnings)} configuration warnings in 'strict' mode!"
        raise SystemExit(msg)
    return cfg


class Config:
    """MkDocs config file wrapper."""

    def __init__(self, config: Mapping | str | os.PathLike | None = None):
        """Constructor.

        Arguments:
            config: MkDocs config
        """
        match config:
            case MkDocsConfig():
                self._config: MkDocsConfig = config
            case Mapping():
                self._config = load_config(config)
            case str() | os.PathLike() as path:
                self._config = load_config(str(path))
            case None:
                if file := pathhelpers.find_cfg_for_folder("mkdocs.yml"):
                    self._config = load_config(str(file))
                else:
                    msg = "Could not find config file"
                    raise FileNotFoundError(msg)
            case _:
                raise TypeError(config)
        self.plugin = self._config.plugins["mknodes"]

    def __getattr__(self, name):
        return getattr(self._config, name)

    def __repr__(self):
        return reprhelpers.get_repr(self, self._config)

    @property
    def site_url(self) -> str:
        url = self._config.site_url
        if url is None:
            return ""
        return url if url.endswith("/") else f"{url}/"

    @property
    def docs_dir(self) -> pathlib.Path:
        return pathlib.Path(self._config.docs_dir)

    @property
    def site_dir(self) -> pathlib.Path:
        return pathlib.Path(self._config.site_dir)

    def update_from_context(self, context: contexts.ProjectContext):
        if not self._config.extra.get("social"):
            self._config.extra["social"] = context.metadata.social_info
        self._config.repo_url = context.metadata.repository_url
        self._config.site_description = context.metadata.summary
        self._config.site_name = context.metadata.distribution_name
        self._config.site_author = context.metadata.author_name
        text = f"Copyright © {datetime.now().year} {context.metadata.author_name}"
        self._config.copyright = text

    def get_markdown_instance(
        self,
        additional_extensions: list[str] | None = None,
        config_override: dict[str, Any] | None = None,
    ) -> mdconverter.MdConverter:
        """Return a markdown instance based on given config.

        Arguments:
            additional_extensions: Additional extensions to use
            config_override: Dict with extension settings. Overrides config settings.
        """
        extensions = self._config.markdown_extensions
        if additional_extensions:
            extensions = list(set(additional_extensions + extensions))
        configs = self._config.mdx_configs | (config_override or {})
        return mdconverter.MdConverter(extensions=extensions, extension_configs=configs)

    def get_edit_url(self, edit_path: str | None) -> str | None:
        """Return edit url.

        If no explicit edit path is given, this will return the path
        to the builder function.

        Arguments:
            edit_path: Edit path
        """
        repo_url = self.repo_url
        if not repo_url:
            return None
        edit_uri = self.edit_uri or "edit/main/"
        if not edit_uri.startswith(("?", "#")) and not repo_url.endswith("/"):
            repo_url += "/"
        rel_path = self.plugin.config.build_fn.split(":")[0]
        if not rel_path.endswith(".py"):
            rel_path = rel_path.replace(".", "/")
            rel_path += ".py"
        base_url = parse.urljoin(repo_url, edit_uri)
        if repo_url and edit_path:
            # root_path = pathlib.Path(config["docs_dir"]).parent
            # edit_path = str(edit_path.relative_to(root_path))
            rel_path = edit_path
        return parse.urljoin(base_url, rel_path)

    def get_jinja_config(self) -> Sequence[jinja2.BaseLoader]:
        cfg = self.plugin.config.get_jinja_config()
        cfg["loader"].append(jinjarope.FileSystemLoader(self.docs_dir))
        return cfg

    def get_install_candidates(self) -> list[str]:
        """Return a list of installation candidates for this config."""
        path = "https://raw.githubusercontent.com/mkdocs/catalog/main/projects.yaml"
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            get_deps.get_deps(path, self._config.config_file_path)
        return [i for i in buffer.getvalue().split("\n") if i]

    def add_js(
        self,
        path: str,
        defer: bool = False,
        async_: bool = False,
        typ: str = "",
    ):
        """Add javascript to the config.

        Arguments:
            path: Path / URL to the javascript file
            defer: Add defer attribute to <script> tag
            async_: Add async attribute to <script> tag
            typ: Add given type attribute to <script> tag
        """
        from mkdocs.config import config_options

        val = config_options.ExtraScriptValue(str(path))
        val.async_ = async_
        val.defer = defer
        val.type = typ
        self.extra_javascript.append(val)


if __name__ == "__main__":
    test = Config()
    print(test)
