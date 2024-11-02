from __future__ import annotations

import ipaddress
from typing import Annotated, Any

from pathspec import gitignore
from pydantic import BaseModel, DirectoryPath, Field, FilePath, HttpUrl, field_validator
from pydantic.functional_validators import BeforeValidator
from pydantic_core import PydanticCustomError


def validate_gitignore_patterns(patterns: list[str]) -> list[str]:
    """Validate a list of gitignore patterns using pathspec."""
    try:
        gitignore.GitIgnoreSpec.from_lines(patterns)
    except Exception as e:
        msg = "invalid_gitignore_pattern"
        raise PydanticCustomError(
            msg,
            "Invalid gitignore pattern(s): {error}",
            {"error": str(e)},
        ) from e
    else:
        return patterns


GitIgnorePatterns = Annotated[
    list[str],
    BeforeValidator(validate_gitignore_patterns),
]


class NavItem(BaseModel):
    """Represents a navigation item in the MkDocs configuration.

    Can be a string (for a simple link) or a dict (for nested navigation).
    """

    item: str | dict[str, NavItem]


class ThemeConfig(BaseModel):
    """Configuration for the MkDocs theme."""

    class Config:
        extra = "allow"
        populate_by_name = True

    name: str = Field(...)
    """The name of the theme to use.

    Common values include 'material', 'mkdocs', 'readthedocs'.

    Example in mkdocs.yml:
    ```yaml
    theme:
      name: material
    ```
    """

    custom_dir: DirectoryPath | None = Field(None)
    """Directory containing a custom theme. Used to override or extend the selected theme.

    Example in mkdocs.yml:
    ```yaml
    theme:
      name: material
      custom_dir: custom_theme/
    ```
    """

    static_templates: list[str] | None = Field(None)
    """List of templates to render as static pages. These templates will be rendered
    even if they are not referenced in the navigation.

    Example in mkdocs.yml:
    ```yaml
    theme:
      name: material
      static_templates:
        - sitemap.html
        - 404.html
        - custom_page.html
    ```
    """

    locale: str | None = Field(None)
    """The locale to use for the theme

    Affects language-specific elements like date formats
    and UI text. Uses standard locale codes (e.g., 'en', 'fr', 'de', 'ja').

    Example in mkdocs.yml:
    ```yaml
    theme:
      name: material
      locale: en_US
    ```
    """
    # Material-related
    # palette: dict[str, Any] | None = Field(
    #     None, description="Color palette configuration for the theme."
    # )
    # font: dict[str, Any] | None = Field(
    #     None, description="Font configuration for the theme."
    # )
    # features: list[str] | None = Field(
    #     None, description="List of theme-specific features to enable."
    # )
    # logo: str | None = Field(None, description="Path to a logo file for the theme.")
    # icon: str | None = Field(None, description="Path to a favicon file.")
    # favicon: str | None = Field(None, description="Path to a favicon file.")
    # language: str | None = Field(None, description="Language for theme localization.")


class PluginConfig(BaseModel):
    """Configuration for a MkDocs plugin."""

    name: str = Field(..., description="The name of the plugin.")
    config: dict[str, Any] | None = Field(
        None, description="Plugin-specific configuration options."
    )


class AppConfig(BaseModel):
    """Represents the full configuration for a MkDocs project."""

    site_name: str = Field(...)
    """The title to use for the documentation.

    Example in mkdocs.yml:
    ```yaml
    site_name: My Project Documentation
    ```
    """

    site_url: HttpUrl | None = Field(None)
    """The full URL where the documentation will be hosted.

    Example in mkdocs.yml:
    ```yaml
    site_url: https://myproject.github.io
    ```
    """

    site_description: str | None = Field(None)
    """A description for the documentation project.

    Will be added to the HTML meta tags.
    This helps with SEO and provides context when the site is shared.

    Example in mkdocs.yml:
    ```yaml
    site_description: Official documentation for Xyz - A Python library for data analysis
    ```
    """

    site_author: str | None = Field(None)
    """The name of the author to add to the HTML meta tags.

    Example in mkdocs.yml:
    ```yaml
    site_author: John Doe
    ```
    """

    copyright: str | None = Field(None)
    """A copyright notice to add to the footer of documentation.

    Example in mkdocs.yml:
    ```yaml
    copyright: '© 2024 MyProject Team'
    ```
    """

    repo_name: str | None = Field(None)
    """A name to use for the link to the project source repo.
    If repo_url is set but repo_name is not, it will default to "GitHub", "Bitbucket",
    or "GitLab" for known URLs, or the hostname for unknown URLs.

    Example in mkdocs.yml:
    ```yaml
    repo_name: MyProject
    repo_url: https://github.com/username/myproject
    ```
    """

    repo_url: HttpUrl | None = Field(None)
    """A link to the project source repository.

    Example in mkdocs.yml:
    ```yaml
    repo_url: https://github.com/username/project
    ```
    """

    edit_uri: str | None = Field(None)
    """A URI to the docs directory in the project source repo, relative to the repo_url.

    When set, a link directly to the page in the source repo will be added
    to the generated HTML.

    Example in mkdocs.yml:
    ```yaml
    edit_uri: edit/main/docs/
    ```
    """

    remote_branch: str | None = Field(None)
    """The remote branch to commit to when using gh-deploy.

    Example in mkdocs.yml:
    ```yaml
    remote_branch: gh-pages  # default
    ```
    """

    remote_name: str | None = Field(None)
    """The remote name to push to when using gh-deploy.

    Example in mkdocs.yml:
    ```yaml
    remote_name: origin  # default
    ```
    """

    docs_dir: DirectoryPath = Field("docs")
    """The directory containing the documentation markdown files.

    Example in mkdocs.yml:
    ```yaml
    docs_dir: documentation
    ```
    """

    site_dir: DirectoryPath = Field("site")
    """The directory where the site will be built to.

    Example in mkdocs.yml:
    ```yaml
    site_dir: public
    ```
    """

    extra_templates: list[DirectoryPath] | None = Field(None)
    """Similar to extra_css/js, but each template (HTML or XML) will be built with
    Jinja2 and the global context.

    Example in mkdocs.yml:
    ```yaml
    extra_templates:
      - templates/custom.html
      - templates/footer.html
    ```
    """

    theme: ThemeConfig = Field(...)
    """The MkDocs theme for the documentation.

    Can be a string for built-in themes or a theme config dict.

    Example in mkdocs.yml:
    ```yaml
    theme:
      name: material
      features:
        - navigation.tabs
        - navigation.expand
      palette:
        primary: indigo
        accent: indigo
      custom_dir: overrides
    ```
    """

    use_directory_urls: bool = Field(True)
    """If True, use <page_name>/index.html style files with hyperlinks to the directory.
    If False, use <page_name>.html style file with hyperlinks to the file.
    True generates nicer URLs, but False is useful if browsing the output on a filesystem.

    Example in mkdocs.yml:
    ```yaml
    use_directory_urls: true  # default
    ```
    """

    strict: bool = Field(False)
    """Enabling strict mode causes MkDocs to stop the build when a problem is encountered
    rather than display an error message.

    Example in mkdocs.yml:
    ```yaml
    strict: true
    ```
    """

    dev_addr: str = Field("127.0.0.1:8000")
    """The address on which to serve the live reloading docs server.

    Example in mkdocs.yml:
    ```yaml
    dev_addr: 127.0.0.1:8000  # default
    ```
    """

    extra_css: list[FilePath] | None = Field(None)
    """List of CSS files from the docs dir that should be additionally includede.

    Example in mkdocs.yml:
    ```yaml
    extra_css:
      - css/custom.css
      - css/extra.css
    ```
    """

    extra_javascript: list[FilePath] | None = Field(None)
    """List of JavaScript files from the docs dir that should be additionally includede.

    Can include both simple paths and dictionaries with additional attributes.

    Example in mkdocs.yml:
    ```yaml
    extra_javascript:
      - js/custom.js
      - path: js/analytics.js
        defer: true
    ```
    """

    markdown_extensions: list[str | dict[str, Any]] | None = Field(None)
    """PyMarkdown extension names and their configurations.

    Example in mkdocs.yml:
    ```yaml
    markdown_extensions:
      - toc:
          permalink: true
      - admonition
      - pymdownx.highlight:
          anchor_linenums: true
      - pymdownx.superfences
    ```
    """

    hooks: list[str] | None = Field(None)
    """A list of Python scripts to load as hooks.

    These scripts can modify the build process.

    Example in mkdocs.yml:
    ```yaml
    hooks:
      - hooks/custom_hook.py
      - hooks/pre_build.py
    ```
    """

    nav: list[NavItem] | None = Field(None)
    """Defines the hierarchical structure of the documentation navigation.
    Each item can be a simple path to a file or a section with nested items.

    Example in mkdocs.yml:
    ```yaml
    nav:
      - Home: index.md
      - User Guide:
          - Installation: guide/installation.md
          - Configuration: guide/configuration.md
      - API Reference: api.md
    ```
    """

    plugins: list[dict[str, Any]] = Field(default_factory=list)
    """A list of plugins to use.

    Each item can be a string (plugin name) or a dictionary with configuration.

    Example in mkdocs.yml:
    ```yaml
    plugins:
      - search
      - mkdocstrings:
          handlers:
            python:
              options:
                show_source: true
      - git-revision-date
    ```
    """

    language: str | None = Field(None)
    """The language of the documentation as a BCP 47 language tag.

    Example in mkdocs.yml:
    ```yaml
    language: en
    ```
    """

    locale: str | None = Field(None)
    """The locale of the documentation

   Affects date formats and other regional settings.

    Example in mkdocs.yml:
    ```yaml
    locale: en_US
    ```
    """

    extra: dict[str, Any] | None = Field(None)
    """A mapping/dictionary of custom data that is passed to the template.

    This allows template authors to require extra configuration that is not
    relevant to all themes and doesn't need to be explicitly supported by MkDocs itself.

    Example in mkdocs.yml:
    ```yaml
    extra:
      version: 1.0.0
      analytics_id: UA-XXXXX
      social:
        - icon: fontawesome/brands/github
          link: https://github.com/project
    ```
    """

    validation: dict[str, Any] | None = Field(None)
    """Validation options for internal & external links, and other content.

    Example in mkdocs.yml:
    ```yaml
    validation:
      nav:
        omitted_files: warn
      links:
        check_external: true
    ```
    """

    watch: list[DirectoryPath] | None = Field(None)
    """A list of extra paths to watch while running `mkdocs serve`.

    These paths will trigger a rebuild if their contents change.

    Example in mkdocs.yml:
    ```yaml
    watch:
      - src/docs/
      - additional/content/
    ```
    """

    exclude_docs: GitIgnorePatterns = Field(default_factory=list)
    """Gitignore-like file patterns (relative to docs dir) to exclude from the site.

    These files will be completely ignored during site generation.

    Example in mkdocs.yml:
    ```yaml
    exclude_docs:
      - '*.tmp'
      - 'draft/*.md'
      - '.git/*'
    ```
    """

    not_in_nav: GitIgnorePatterns = Field(default_factory=list)
    """Gitignore-like file patterns that are not intended to be in the nav.

    Patterns are relative to docs dir.
    This marks doc files that are expected not to be in the nav, otherwise they will
    cause a log message.

    Example in mkdocs.yml:
    ```yaml
    not_in_nav:
      - 'includes/*.md'
      - 'assets/templates/*'
    ```
    """

    @field_validator("plugins", mode="before")
    @classmethod
    def convert_to_plugin_dict_list(
        cls,
        value: list[str | dict[str, dict[str, Any]]] | dict[str, Any],
    ) -> list[dict[str, dict[str, Any]]]:
        result: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, str):
                result.append({item: {}})
            elif isinstance(item, dict):
                if len(item) > 1:
                    msg = "Plugin dictionaries must have a single key"
                    raise ValueError(msg)
                result.append(item)
            else:
                msg = f"Invalid type for plugin section: {item!r} ({type(item)})"
                raise ValueError(msg)  # noqa: TRY004
        return result

    @field_validator("dev_addr", mode="before")
    @classmethod
    def validate_ip_port(cls, v: str) -> str:
        try:
            ip, port = v.split(":")
            ipaddress.ip_address(ip)  # Validates IP
        except ValueError as e:
            msg = f"Invalid IP:PORT format - {e!s}"
            raise ValueError(msg) from e
        if not 1 <= int(port) <= 65535:  # noqa: PLR2004
            msg = "Port must be between 1 and 65535"
            raise ValueError(msg)
        return v


if __name__ == "__main__":
    import pathlib

    import devtools
    import yaml

    text = pathlib.Path("mkdocs.yml").read_text("utf-8")
    cfg = yaml.unsafe_load(text)
    config = AppConfig(**cfg)

    devtools.debug(config)
