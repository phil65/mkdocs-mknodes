"""Engine-neutral result of running a MkNodes build function."""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class NavItem:
    """An entry of the site navigation.

    Either a link to a page / URL (`target` set) or a section (`children` set).
    """

    title: str
    target: str | None = None
    """Page path (relative to the docs root) or an external URL."""
    children: list[NavItem] = dataclasses.field(default_factory=list)

    @property
    def is_section(self) -> bool:
        return self.target is None

    def iter_targets(self):
        if self.target:
            yield self.target
        for child in self.children:
            yield from child.iter_targets()


@dataclasses.dataclass
class Script:
    """A JavaScript file to include in every page."""

    path: str
    """URL or path relative to the docs root."""
    defer: bool = False
    async_: bool = False
    typ: str | None = None


@dataclasses.dataclass
class SiteMetadata:
    """Site-level metadata inferred from the project."""

    site_name: str | None = None
    site_description: str | None = None
    site_author: str | None = None
    repo_url: str | None = None
    copyright: str | None = None
    social: list[dict[str, str]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class BuildOutput:
    """Everything a build function produced, independent of the site engine.

    Writers (see `mkdocs_mknodes.writers`) turn this into the input of a concrete
    static site generator.
    """

    pages: dict[str, str] = dataclasses.field(default_factory=dict)
    """Markdown pages: path relative to the docs root -> Markdown."""
    assets: dict[str, str | bytes] = dataclasses.field(default_factory=dict)
    """Static files: path relative to the docs root -> content (CSS, JS, images, ...)."""
    nav: list[NavItem] = dataclasses.field(default_factory=list)
    """Navigation tree."""
    markdown_extensions: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)
    """Python-Markdown extensions required by the pages: name -> config."""
    extra_css: list[str] = dataclasses.field(default_factory=list)
    """Stylesheets: URLs or paths relative to the docs root (contained in `assets`)."""
    extra_javascript: list[Script] = dataclasses.field(default_factory=list)
    """Scripts: URLs or paths relative to the docs root (contained in `assets`)."""
    templates: dict[str, str] = dataclasses.field(default_factory=dict)
    """Theme template overrides (Material-style Jinja blocks): filename -> template."""
    extra: dict[str, Any] = dataclasses.field(default_factory=dict)
    """Theme variables (`extra` in MkDocs / Zensical configs)."""
    metadata: SiteMetadata = dataclasses.field(default_factory=SiteMetadata)
    """Site metadata inferred from the project."""
    edit_paths: dict[str, str] = dataclasses.field(default_factory=dict)
    """Page path -> repository path of the source that generated it."""

    @property
    def files(self) -> dict[str, str | bytes]:
        """Pages and assets combined."""
        return {**self.assets, **self.pages}
