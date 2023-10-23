from __future__ import annotations

from collections.abc import Mapping, Sequence
import contextlib

from datetime import datetime
import functools
import io
import os
import pathlib
from typing import Any
from urllib import parse

import jinja2

from mkdocs import config as _config
from mkdocs.commands import get_deps
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger
from mknodes.info import contexts
from mknodes.jinja import loaders
from mknodes.mdlib import mdconverter
from mknodes.utils import pathhelpers


logger = get_plugin_logger(__name__)


@functools.cache
def load_config(path: str | os.PathLike | None = None) -> MkDocsConfig:
    path = None if path is None else str(path)
    cfg = _config.load_config(path)
    logger.info("Loaded config from path '%s'", path or "mkdocs.yml")
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
                if file := pathhelpers.find_file_in_folder_or_parent("mkdocs.yml"):
                    self._config = load_config(str(file))
                else:
                    msg = "Could not find config file"
                    raise FileNotFoundError(msg)
            case _:
                raise TypeError(config)
        self.plugin = self._config.plugins["mknodes"]

    def __getattr__(self, name):
        return getattr(self._config, name)

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

    def get_loaders(self) -> Sequence[jinja2.BaseLoader]:
        jinja_loaders: list[jinja2.BaseLoader] = [loaders.FileSystemLoader(self.docs_dir)]
        for loader_dct in self.mknodes_config.get("jinja_loaders", []):
            dct = loader_dct.copy()
            kls = loaders.LOADERS[dct.pop("type")]
            loader = kls(**dct)
            jinja_loaders.append(loader)
        return jinja_loaders

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
    cfg = Config()
    print(dict(cfg.theme))
