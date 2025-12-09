"""The Mkdocs Plugin."""

from __future__ import annotations

import contextlib
from datetime import datetime
import functools
import io
import logging
import os
import pathlib
import sys
from typing import TYPE_CHECKING, Any, Self, TextIO
from urllib import parse

import jinjarope
from mkdocs.config import config_options as c, defaults
from mknodes.mdlib import mdconverter
from mknodes.utils import classhelpers
from upathtools import to_upath
import yamling


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from mknodes.info import contexts
    from upath.types import JoinablePathLike


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _open_config_file(
    config_file: str | os.PathLike[str] | TextIO | None,
) -> Iterator[TextIO]:
    """A context manager which yields an open file descriptor ready to be read.

    Accepts a filename as a string, an open or closed file descriptor, or None.
    When None, it defaults to `mkdocs.yml` in the CWD. If a closed file descriptor
    is received, a new file descriptor is opened for the same file.
    The file descriptor is automatically closed when the context manager block is existed.
    """
    match config_file:
        case None:
            path: pathlib.Path | None = pathlib.Path("mkdocs.yml")
        case str() | os.PathLike():
            path = pathlib.Path(config_file)
        case _ if getattr(config_file, "closed", False):
            path = pathlib.Path(config_file.name)
        case _:
            result_config_file = config_file
            path = None

    if path is not None:
        path = path.resolve()
        logger.debug("Loading configuration file: %r", path)
        try:
            result_config_file = path.open("rb")
        except FileNotFoundError as e:
            msg = f"Config file {path!r} does not exist."
            raise SystemExit(msg) from e
    else:
        logger.debug("Loading configuration file: %r", result_config_file)
        with contextlib.suppress(OSError):
            result_config_file.seek(0)

    try:
        yield result_config_file
    finally:
        if hasattr(result_config_file, "close"):
            result_config_file.close()


class MkNodesConfig(defaults.MkDocsConfig):
    @classmethod
    @functools.cache
    def from_yaml(
        cls,
        config_file: str | TextIO | None = None,
        *,
        config_file_path: str | None = None,
        **kwargs: Any,
    ) -> Self:
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
            cfg = cls(config_file_path=config_file_path)
            dct = yamling.load_yaml(fd, resolve_inherit=True)
            cfg.load_dict(dct)
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

    @classmethod
    def from_yaml_file(
        cls,
        file: JoinablePathLike,
        config_file_path: str | None = None,
    ) -> Self:
        # cfg = yamling.load_yaml_file(file, resolve_inherit=True)
        config_str = to_upath(file).read_text("utf-8")
        str_io = io.StringIO(config_str)
        return cls.from_yaml(str_io, config_file_path=config_file_path)

    build_fn = c.Type(str, default="mkdocs_mknodes:parse")
    """Path to the build script / callable.

    Possible formats:

      - `my.module:Class.build_fn` (must be a classmethod / staticmethod)
      - `my.module:build_fn`
      - `path/to/file.py:build_fn`

    Can also be remote.
    The targeted callable gets the project instance as an argument and optionally
    keyword arguments from setting below.
    """
    kwargs = c.Optional(c.Type(dict))
    """Keyword arguments passed to the build script / callable.

    Build scripts may have keyword arguments. You can set them by using this setting.
    """
    repo_path = c.Type(str, default=".")
    """Path to the repository to create a website for. (`http://....my_project.git`)"""
    clone_depth = c.Type(int, default=100)
    """Clone depth in case the repository is remote. (Required for `git-changelog`)."""
    build_folder = c.Optional(c.Type(str))
    """Folder to create the Markdown files in.

    If no folder is set, **MkNodes** will generate a temporary dir."""
    show_page_info = c.Type(bool, default=False)
    """Append an admonition box with build-related information.

    If True, all pages get added an expandable admonition box at the bottom,
    containing information about the created page.
    This includes:
    - Metadata
    - Resources
    - Code which created the page (needs the page to be created via decorators, or
    the `generated_by` attribute of the `MkPage` needs to be set manually)
    """
    rewrite_theme_templates = c.Type(bool, default=True)
    """Add additional functionality to themes by rewriting template files.

    MkNodes can rewrite the HTML templates of Themes in order to add additional
    functionality.

    Right now, enabling this feature allows these options for the **Material-MkDocs**
    theme:
    - use iconify icons instead of the **Material-MkDocs** icons
    - setting the theme features "navigation.indexes" and "navigation.expand" via
      page metadata.
    """
    auto_delete_generated_templates = c.Type(bool, default=True)
    """Delete the generated HTML templates when build is finished.

    MkNodes may generate HTML template overrides during the build process and
    deletes them after build. Using this setting, the deletion can be prevented.
    """
    render_by_default = c.Type(bool, default=True)
    """Render all pages in the jinja environment.

    This allows to render jinja in the **MkNodes** environment outside of the `MkJinja`
    nodes.

    This setting can be overridden by setting the page metadata field "render_macros".
    """
    global_resources = c.Type(bool, default=True)
    """Make resources globally available.

    If True, then the resources inferred from the nodes will be put into all HTML pages.
    (This reflects the "default" MkDocs mechanism of putting extra CSS / JS into the
    config file)
    If False, then MkNodes will put the CSS / JS only into the pages which need it.
    (the resources will be moved into the appropriate page template blocks)
    """
    jinja_loaders = c.Optional(c.ListOfItems(c.Type(dict)))
    """List containing additional jinja loaders to use.

    Dictionaries must have the `type` key set to either "filesystem" or "fsspec".

    Examples:
        ``` yaml
        plugins:
        - mknodes:
            jinja_loaders:
            - type: fsspec
              path: github://
              repo: mknodes
              org: phil65
        ```
    """
    jinja_extensions = c.Optional(c.ListOfItems(c.Type(str)))
    """List containing additional jinja extensions to use.

    Examples:
        ``` yaml
        plugins:
        - mknodes:
            jinja_extensions:
            - jinja2_ansible_filters.AnsibleCoreFiltersExtension
        ```
    """
    jinja_block_start_string = c.Optional(c.Type(str))
    """Jinja block start string."""
    jinja_block_end_string = c.Optional(c.Type(str))
    """Jinja block end string."""
    jinja_variable_start_string = c.Optional(c.Type(str))
    """Jinja variable start string."""
    jinja_variable_end_string = c.Optional(c.Type(str))
    """Jinja variable end string."""
    jinja_on_undefined = c.Type(str, default="strict")
    """Jinja undefined macro behavior."""

    def get_builder(self) -> Callable[..., Any]:
        build_fn = classhelpers.to_callable(self.build_fn)
        build_kwargs = self.kwargs or {}
        return functools.partial(build_fn, **build_kwargs)

    def get_jinja_config(self) -> jinjarope.EnvConfig:
        cfg = jinjarope.EnvConfig(
            block_start_string=self.jinja_block_start_string or "{%",
            block_end_string=self.jinja_block_end_string or "%}",
            variable_start_string=self.jinja_variable_start_string or r"{{",
            variable_end_string=self.jinja_variable_end_string or r"}}",
            # undefined=self.jinja_on_undefined,
            loader=jinjarope.loaders.from_json(self.jinja_loaders),
        )
        cfg.loader |= jinjarope.FileSystemLoader(self.docs_dir)  # type: ignore
        return cfg

    # @property
    # def site_url(self) -> str:
    #     url = super().site_url
    #     if url is None:
    #         return ""
    #     return url if url.endswith("/") else f"{url}/"

    # @property
    # def docs_dir(self) -> pathlib.Path:
    #     return pathlib.Path(super().docs_dir)

    # @property
    # def site_dir(self) -> pathlib.Path:
    #     return pathlib.Path(super().site_dir)

    def update_from_context(self, context: contexts.ProjectContext):
        if not super().extra.get("social"):
            super().extra["social"] = context.metadata.social_info
        self.repo_url = context.metadata.repository_url
        self.site_description = context.metadata.summary
        self.site_name = context.metadata.distribution_name
        self.site_author = context.metadata.author_name
        text = f"Copyright © {datetime.now().year} {context.metadata.author_name}"
        self.copyright = text

    def get_markdown_instance(
        self,
        additional_extensions: list[str] | None = None,
        config_override: dict[str, Any] | None = None,
    ) -> mdconverter.MdConverter:
        """Return a markdown instance based on given config.

        Args:
            additional_extensions: Additional extensions to use
            config_override: Dict with extension settings. Overrides config settings.
        """
        extensions = super().markdown_extensions
        if additional_extensions:
            extensions = list(set(additional_extensions + extensions))
        configs = super().mdx_configs | (config_override or {})
        return mdconverter.MdConverter(extensions=extensions, extension_configs=configs)

    def get_edit_url(self, edit_path: str | None) -> str | None:
        """Return edit url.

        If no explicit edit path is given, this will return the path
        to the builder function.

        Args:
            edit_path: Edit path
        """
        repo_url = self.repo_url
        if not repo_url:
            return None
        edit_uri = self.edit_uri or "edit/main/"
        if not edit_uri.startswith(("?", "#")) and not repo_url.endswith("/"):
            repo_url += "/"
        rel_path = self.build_fn.split(":")[0]
        if not rel_path.endswith(".py"):
            rel_path = rel_path.replace(".", "/")
            rel_path += ".py"
        base_url = parse.urljoin(repo_url, edit_uri)
        if repo_url and edit_path:
            # root_path = pathlib.Path(config["docs_dir"]).parent
            # edit_path = str(edit_path.relative_to(root_path))
            rel_path = edit_path
        return parse.urljoin(base_url, rel_path)

    def add_js(
        self,
        path: str,
        defer: bool = False,
        async_: bool = False,
        typ: str = "",
    ):
        """Add javascript to the config.

        Args:
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
