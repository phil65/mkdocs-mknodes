"""Settings for the engine-agnostic site generator.

Settings are read from (later sources win):

1. the `mknodes` plugin section of the project's `mkdocs.yml` (the legacy MkDocs setup),
2. `[tool.mknodes]` in `pyproject.toml` (the keys below, `-` and `_` are interchangeable),
3. explicit overrides (CLI options).

Without any configuration, the default website (`mkdocs_mknodes:parse`) gets generated.
"""

from __future__ import annotations

import dataclasses
import functools
import pathlib
import tomllib
from typing import TYPE_CHECKING, Any

from mkdocs_mknodes import paths
from mkdocs_mknodes.generator import yamlconfig


if TYPE_CHECKING:
    from collections.abc import Callable
    import os

    import jinjarope


CONFIG_NAMES = ("mkdocs.yml", "mkdocs.yaml")
GENERATED_CONFIG = "mkdocs.generated.yml"


@dataclasses.dataclass
class GeneratorSettings:
    """Settings for generating a website from a MkNodes build function."""

    project_dir: pathlib.Path = dataclasses.field(default_factory=pathlib.Path.cwd)
    """Root folder of the project (contains `mkdocs.yml` / `pyproject.toml`)."""
    config_file: pathlib.Path | None = None
    """The site config the generated config inherits from (`mkdocs.yml`)."""
    build_fn: str = paths.DEFAULT_BUILD_FN
    """Build function (`module:callable`, `path/file.py:callable`, `module:Class.method`)."""
    kwargs: dict[str, Any] = dataclasses.field(default_factory=dict)
    """Keyword arguments for the build function (`pages` for the default build function)."""
    repo_path: str = "."
    """Repository to build docs for (local path or remote URL)."""
    clone_depth: int = 100
    """Clone depth for remote repositories."""
    show_page_info: bool = False
    """Append a collapsible box with build info to every page."""
    render_by_default: bool = True
    """Render generated pages with the MkNodes Jinja environment."""
    global_resources: bool = True
    """Put CSS / JS into the site config instead of per-page template blocks."""
    docs_dir: str | None = None
    """Docs folder (default: `docs_dir` of the site config, else `docs`)."""
    generated_dir: str | None = None
    """Folder to write generated pages into (default: `docs_dir`).

    If it differs from `docs_dir`, hand-written pages get mirrored into it and it becomes
    the docs dir of the generated config.
    """
    generated_config: str = GENERATED_CONFIG
    """Filename of the generated site config (relative to the project dir)."""
    site_dir: str | None = None
    """Output folder for the HTML build (default: the site config's `site_dir`)."""
    jinja_loaders: list[dict[str, Any]] | None = None
    jinja_extensions: list[str] | None = None
    jinja_block_start_string: str | None = None
    jinja_block_end_string: str | None = None
    jinja_variable_start_string: str | None = None
    jinja_variable_end_string: str | None = None
    site_config: dict[str, Any] = dataclasses.field(default_factory=dict, repr=False)
    """The loaded site config (`INHERIT` resolved, custom tags preserved)."""

    @property
    def resolved_docs_dir(self) -> pathlib.Path:
        name = self.docs_dir or self.site_config.get("docs_dir") or "docs"
        return self.project_dir / name

    @property
    def resolved_generated_dir(self) -> pathlib.Path:
        if self.generated_dir:
            return self.project_dir / self.generated_dir
        return self.resolved_docs_dir

    @property
    def generated_config_path(self) -> pathlib.Path:
        return self.project_dir / self.generated_config

    @property
    def theme_config(self) -> dict[str, Any]:
        theme = self.site_config.get("theme") or {}
        if isinstance(theme, str):
            theme = {"name": theme}
        return yamlconfig.resolve(theme)

    def get_builder(self) -> Callable[..., Any]:
        """Return the build function with the configured kwargs bound."""
        from mknodes.utils import classhelpers

        build_fn_path = self.build_fn
        module, sep, qualname = build_fn_path.partition(":")
        if module.endswith(".py") and not pathlib.Path(module).is_absolute():
            build_fn_path = f"{(self.project_dir / module).as_posix()}{sep}{qualname}"
        build_fn = classhelpers.to_callable(build_fn_path)
        return functools.partial(build_fn, **self.kwargs)

    def get_jinja_config(self) -> jinjarope.EnvConfig:
        import jinjarope

        cfg = jinjarope.EnvConfig(
            block_start_string=self.jinja_block_start_string or "{%",
            block_end_string=self.jinja_block_end_string or "%}",
            variable_start_string=self.jinja_variable_start_string or r"{{",
            variable_end_string=self.jinja_variable_end_string or r"}}",
            loader=jinjarope.loaders.from_json(self.jinja_loaders),
        )
        if self.jinja_extensions:
            cfg.extensions = list(self.jinja_extensions)
        docs_loader = jinjarope.FileSystemLoader(str(self.resolved_docs_dir))
        loader = cfg.loader
        cfg.loader = jinjarope.ChoiceLoader([loader, docs_loader]) if loader else docs_loader
        return cfg

    @classmethod
    def load(
        cls,
        project_dir: str | os.PathLike[str] | None = None,
        config_file: str | os.PathLike[str] | None = None,
        **overrides: Any,
    ) -> GeneratorSettings:
        """Load settings for given project.

        Args:
            project_dir: Project root (default: cwd, or the folder of `config_file`)
            config_file: Site config to read (default: `mkdocs.yml` in the project dir)
            overrides: Explicit setting overrides (`None` values are ignored)
        """
        if project_dir is None:
            project_dir = pathlib.Path(config_file).parent if config_file else pathlib.Path()
        root = pathlib.Path(project_dir).resolve()
        cfg_path = pathlib.Path(config_file) if config_file else None
        if cfg_path and not cfg_path.is_absolute():
            cfg_path = (pathlib.Path.cwd() / cfg_path).resolve()
        if cfg_path is None:
            cfg_path = next((root / n for n in CONFIG_NAMES if (root / n).is_file()), None)
        site_config = yamlconfig.load_file(cfg_path) if cfg_path and cfg_path.is_file() else {}
        values: dict[str, Any] = {}
        values |= _normalize(get_plugin_config(site_config))
        values |= _normalize(_read_pyproject(root))
        values |= {k: v for k, v in _normalize(overrides).items() if v is not None}
        if "pages" in values:  # shortcut for the default build function
            values.setdefault("kwargs", {})["pages"] = values.pop("pages")
        fields = {f.name for f in dataclasses.fields(cls)}
        known = {k: v for k, v in values.items() if k in fields}
        known["kwargs"] = known.get("kwargs") or {}
        return cls(
            project_dir=root,
            config_file=cfg_path if cfg_path and cfg_path.is_file() else None,
            site_config=site_config,
            **{k: v for k, v in known.items() if k not in {"project_dir", "config_file"}},
        )


def get_plugin_config(site_config: dict[str, Any]) -> dict[str, Any]:
    """Return the (`!ENV`-resolved) `mknodes` plugin options from a MkDocs config."""
    plugins = site_config.get("plugins") or []
    if isinstance(plugins, dict):
        plugins = [{k: v} for k, v in plugins.items()]
    for plugin in plugins:
        if plugin == "mknodes":
            return {}
        if isinstance(plugin, dict) and "mknodes" in plugin:
            return yamlconfig.resolve(plugin["mknodes"] or {})
    return {}


def _read_pyproject(root: pathlib.Path) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data.get("tool", {}).get("mknodes", {})


def _normalize(dct: dict[str, Any]) -> dict[str, Any]:
    return {k.replace("-", "_"): v for k, v in dct.items()}
