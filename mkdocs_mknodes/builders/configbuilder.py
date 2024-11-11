from __future__ import annotations

import io
import os
from typing import Any

import yamling

from mkdocs_mknodes import telemetry
from mkdocs_mknodes.appconfig import appconfig
from mkdocs_mknodes.plugin import mknodesconfig


logger = telemetry.get_plugin_logger(__name__)


class ConfigBuilder:
    def __init__(
        self,
        configs: list[appconfig.AppConfig] | None = None,
        repo_path: str | None = ".",
        build_fn: str | None = None,
        clone_depth: int | None = 100,
    ):
        self.configs = configs or []
        self.repo_path = repo_path
        self.build_fn = build_fn
        self.clone_depth = clone_depth

    def add_config_file(self, path: str | os.PathLike[str], **overrides: Any):
        cfg = appconfig.AppConfig.from_yaml_file(path, **overrides)
        self.configs.append(cfg)

    def build_mkdocs_config(
        self, site_dir: str | os.PathLike[str] | None = None, **kwargs: Any
    ) -> mknodesconfig.MkNodesConfig:
        cfg = self.configs[0]
        if site_dir:
            cfg.site_dir = site_dir
        if self.repo_path is not None:
            cfg.repo_path = self.repo_path
        if self.build_fn is not None:
            cfg.build_fn = self.build_fn
        if self.clone_depth is not None:
            cfg.clone_depth = self.clone_depth
        if cfg.theme.name != "material":
            cfg.remove_plugin("social")
            cfg.remove_plugin("tags")
        # cfg = {**cfg, **kwargs}
        text = yamling.dump_yaml(cfg.model_dump(mode="json", exclude_none=True))
        buffer = io.StringIO(text)
        buffer.name = cfg.config_file_path
        config = mknodesconfig.MkNodesConfig.from_yaml(buffer, **kwargs)

        for k, v in config.items():
            logger.debug("%s: %s", k, v)
        return config
