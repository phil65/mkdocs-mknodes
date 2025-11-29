from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

from mknodes.info import mkdocsconfigfile
import yamling

from mkdocs_mknodes import telemetry
from mkdocs_mknodes.plugin import mknodesconfig


if TYPE_CHECKING:
    import os


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

    def build_mkdocs_config(
        self, site_dir: str | os.PathLike[str] | None = None, **kwargs: Any
    ) -> mknodesconfig.MkNodesConfig:
        cfg = self.configs[0]
        if site_dir:
            cfg["site_dir"] = site_dir
        for plugin in cfg["plugins"]:
            if "mknodes" in plugin:
                if self.repo_path is not None:
                    plugin["mknodes"]["repo_path"] = self.repo_path
                if self.build_fn is not None:
                    plugin["mknodes"]["build_fn"] = self.build_fn
                if self.clone_depth is not None:
                    plugin["mknodes"]["clone_depth"] = self.clone_depth
        # cfg = {**cfg, **kwargs}
        text = yamling.dump_yaml(dict(cfg))
        buffer = io.StringIO(text)
        buffer.name = cfg.path
        config = mknodesconfig.MkNodesConfig.from_yaml(buffer, **kwargs)

        for k, v in config.items():
            logger.debug("%s: %s", k, v)
        return config
