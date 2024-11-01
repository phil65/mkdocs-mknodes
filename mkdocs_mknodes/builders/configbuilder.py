from __future__ import annotations

import io
import os
from typing import Any

from mkdocs.config import load_config
from mkdocs.config.defaults import MkDocsConfig
from mknodes.info import mkdocsconfigfile
from mknodes.utils import yamlhelpers

from mkdocs_mknodes import telemetry


logger = telemetry.get_plugin_logger(__name__)


class ConfigBuilder:
    def __init__(
        self,
        configs: list[mkdocsconfigfile.MkDocsConfigFile] | None = None,
        repo_path: str | None = ".",
        build_fn: str | None = None,
        clone_depth: int | None = 100,
    ):
        self.configs = configs or []
        self.repo_path = repo_path
        self.build_fn = build_fn
        self.clone_depth = clone_depth

    def add_config_file(self, path: str | os.PathLike[str]):
        cfg = mkdocsconfigfile.MkDocsConfigFile(path)
        self.configs.append(cfg)

    def build_mkdocs_config(self, **kwargs: Any) -> MkDocsConfig:
        cfg = self.configs[0]
        cfg = {**cfg, **kwargs}
        text = yamlhelpers.dump_yaml(cfg)
        buffer = io.StringIO(text)
        buffer.name = self.configs[0].path
        config = load_config(buffer, **kwargs)
        for plugin in config["plugins"]:
            if "mknodes" in plugin:
                if self.repo_path is not None:
                    plugin["mknodes"]["repo_path"] = self.repo_path
                if self.build_fn is not None:
                    plugin["mknodes"]["build_fn"] = self.build_fn
                if self.clone_depth is not None:
                    plugin["mknodes"]["clone_depth"] = self.clone_depth
        for k, v in config.items():
            logger.debug("%s: %s", k, v)
        return config
