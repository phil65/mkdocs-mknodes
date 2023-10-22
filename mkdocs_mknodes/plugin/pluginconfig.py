"""The Mkdocs Plugin."""

from __future__ import annotations

from collections.abc import Callable
import functools

from mkdocs.config import base, config_options as c
from mknodes.utils import classhelpers


class PluginConfig(base.Config):
    build_fn = c.Optional(c.Type(str))
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
    the `generated_by` attribute of the MkPage needs to be set manually)
    """
    rewrite_theme_templates = c.Type(bool, default=True)
    """Add additional functionality to themes by rewriting template files.

    MkNodes can rewrite the HTML templates of Themes in order to add additional
    functionality.

    Right now, setting this feature allows these options for the Material-MkDocs theme:
    - use iconify icons instead of the Material-MkDocs icons
    - setting the theme features "navigation.indexes" and "navigation.expand" via
      page metadata.
    """
    render_all_pages = c.Type(bool, default=True)
    """Render all pages in the jinja environment.

    This allows to render jinja in the MkNodes environment outside of the MkJinja nodes.

    This setting can be overridden by setting the page metadata field "render_jinja".
    """
    jinja_loaders = c.Optional(c.ListOfItems(c.Type(dict)))
    """List containing additional jinja loaders to use.

    Dictionaries must have the name key set to either "filesystem" or "fsspec".

    Examples:
        ``` yaml
        jinja_loaders:
          - name: fsspec
            protocol: github
            repo: mknodes
            org: phil65
    """
    jinja_extensions = c.Optional(c.ListOfItems(c.Type(str)))
    """List containing additional jinja extensions to use.

    Examples:
        ``` yaml
        jinja_extensions:
          - jinja2_ansible_filters.AnsibleCoreFiltersExtension
    """

    def get_builder(self) -> Callable:
        build_fn = classhelpers.to_callable(self.build_fn)
        build_kwargs = self.kwargs or {}
        return functools.partial(build_fn, **build_kwargs)
