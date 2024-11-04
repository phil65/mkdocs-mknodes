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
    """Configuration settings for the MkDocs themes.

    !!! info "Theme Configuration Options"
        The theme configuration allows for extensive customization including custom
        directories, static templates, and locale settings.

    ## Properties Overview

    | Property | Description | Required |
    |----------|-------------|----------|
    | name | Theme identifier | Yes |
    | custom_dir | Custom theme directory | No |
    | static_templates | Additional static pages | No |
    | locale | Language/locale setting | No |
    """

    name: str = Field(...)
    """Specifies the theme to use for documentation rendering.

    !!! info "Common Theme Options"
        - `material`: Material for MkDocs theme
        - `mkdocs`: Default MkDocs theme
        - `readthedocs`: ReadTheDocs theme

    !!! example "Basic Configuration"
        ```yaml
        theme:
          name: material
        ```
    """

    custom_dir: DirectoryPath | None = Field(None)
    """Directory containing custom theme overrides or extensions.

    !!! tip "Theme Customization"
        Use this to override or extend the selected theme's templates and assets.

    !!! example "Custom Directory Setup"
        ```yaml
        theme:
          name: material
          custom_dir: custom_theme/
        ```
    """

    static_templates: list[str] | None = Field(None)
    """Defines templates to be rendered as static pages, regardless of nav structure.

    !!! info "Common Use Cases"
        - Error pages (404, 500)
        - Sitemaps
        - Custom static pages

    !!! example "Static Templates Configuration"
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
    """Defines the language and regional settings for the theme.

    !!! info "Locale Impact"
        Affects:
        - Date formats
        - UI text translations
        - RTL/LTR text direction

    !!! example "Locale Setting"
        ```yaml
        theme:
          name: material
          locale: en_US
        ```

    !!! tip "Common Locales"
        - `en_US`: English (United States)
        - `fr_FR`: French (France)
        - `de_DE`: German (Germany)
        - `ja_JP`: Japanese (Japan)
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
    """The main configuration class for MkDocs projects.

    This class defines all available settings for customizing your documentation site.

    !!! tip "Configuration File"
        All settings are typically defined in `mkdocs.yml` at your project root.

    !!! warning "Required Fields"
        At minimum, your configuration must include:
        - `site_name`
        - `theme` configuration
    """

    site_name: str = Field(...)
    """The primary title for your documentation project.

    !!! info "Usage"
        This title will appear:
        - At the top of your documentation
        - In browser tab titles
        - In search engine results

    !!! example "Configuration"
        ```yaml
        site_name: My Project Documentation
        ```
    """

    site_url: HttpUrl | None = Field(None)
    """The canonical URL for your documentation site.

    !!! info "Purpose"
        - Adds canonical URL meta tags to HTML
        - Configures the development server base path
        - Helps with SEO optimization

    !!! warning "Subdirectory Hosting"
        If hosting in a subdirectory, include it in the URL:
        ```yaml
        site_url: https://example.com/docs/
        ```

    !!! example "Basic Configuration"
        ```yaml
        site_url: https://example.com/
        ```
    """

    site_description: str | None = Field(None)
    """A concise description of your documentation project.

    !!! info "SEO Impact"
        - Appears in search engine results
        - Used in social media cards
        - Improves site discoverability

    !!! example "Configuration"
        ```yaml
        site_description: Official documentation for XYZ - A data analysis library
        ```
    """

    site_author: str | None = Field(None)
    """The name of the documentation author or organization.

    !!! info "Usage"
        - Added to HTML meta tags
        - Used for attribution
        - Helpful for SEO

    !!! example "Configuration"
        ```yaml
        site_author: John Doe
        ```
    """

    copyright: str | None = Field(None)
    """Copyright information displayed in the documentation footer.

    !!! tip "Formatting"
        You can use HTML entities and Unicode characters for © symbol:
        - `&copy;`
        - `©`

    !!! example "Configuration"
        ```yaml
        copyright: '© 2024 MyProject Team. All rights reserved.'
        ```
    """

    repo_url: HttpUrl | None = Field(None)
    """Link to your project's source code repository.

    !!! info "Supported Platforms"
        - GitHub
        - GitLab
        - Bitbucket
        - Custom Git repositories

    !!! tip "Integration Features"
        - Adds repository link to documentation
        - Enables "Edit on GitHub" (or similar) buttons
        - Integrates with version control features

    !!! example "Configuration"
        ```yaml
        repo_url: https://github.com/username/project
        ```
    """

    edit_uri: str | None = Field(None)
    """Path to documentation source files in your repository.

    !!! info "Construction"
        The full edit URL is built by combining:
        - `repo_url`
        - `edit_uri`
        - Current page path

    !!! tip "Common Patterns"
        | Platform | Typical Format |
        |----------|---------------|
        | GitHub   | `edit/main/docs/` |
        | GitLab   | `-/edit/main/docs/` |
        | GitHub Wiki | `{path_noext}/_edit` |

    !!! example "Configuration"
        ```yaml
        edit_uri: edit/main/docs/
        ```
    """

    remote_branch: str | None = Field(None)
    """Target branch for deployment when using gh-deploy command.

    !!! info "Default Value"
        If not specified, defaults to `gh-pages`

    !!! tip "Common Use Cases"
        - GitHub Pages deployment
        - Documentation versioning
        - Staging environments

    !!! example "Configuration"
        ```yaml
        remote_branch: gh-pages
        # or
        remote_branch: documentation
        ```
    """

    remote_name: str | None = Field(None)
    """Git remote for deployment with gh-deploy command.

    !!! info "Default Value"
        If not specified, defaults to `origin`

    !!! example "Configuration"
        ```yaml
        remote_name: origin
        # or
        remote_name: documentation
        ```

    !!! tip "Multiple Remotes"
        Useful when maintaining separate remotes for:
        - Code repository
        - Documentation hosting
        - Staging environments
    """

    docs_dir: DirectoryPath = Field("docs")
    """Directory containing documentation markdown source files.

    !!! info "Path Resolution"
        - Relative paths: Resolved from mkdocs.yml location
        - Absolute paths: Used as-is from filesystem root

    !!! warning "Important Notes"
        - Must be different from `site_dir`
        - Should contain only documentation source files
        - Binary files here will be copied to `site_dir`

    !!! example "Configuration"
        ```yaml
        docs_dir: documentation
        # or
        docs_dir: /absolute/path/to/docs
        ```
    """

    site_dir: DirectoryPath = Field("site")
    """Directory where the built HTML site will be created.

    !!! warning "Version Control"
        - Add this directory to `.gitignore`
        - Don't manually edit files in this directory
        - Contents are overwritten on each build

    !!! tip "Best Practices"
        - Keep separate from source files
        - Use for deployment only
        - Clear directory before builds

    !!! example "Configuration"
        ```yaml
        site_dir: public
        # or
        site_dir: build
        ```
    """

    extra_templates: list[DirectoryPath] | None = Field(None)
    """Additional template files to be processed by MkDocs.

    !!! info "Template Processing"
        - Templates are processed with Jinja2
        - Have access to global context
        - Can generate HTML or XML output

    !!! tip "Template Locations"
        Templates must be in either:
        - Theme's template directory
        - Custom directory specified in theme config

    !!! example "Configuration"
        ```yaml
        extra_templates:
          - templates/sitemap.xml
          - templates/robots.txt
          - templates/custom_layout.html
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
    """Controls URL structure of the generated documentation site.

    !!! info "URL Formats"
        | Setting | URL Format | File Structure |
        |---------|------------|----------------|
        | `True`  | site.com/page/ | pretty URLs |
        | `False` | site.com/page.html | file-based URLs |

    !!! warning "When to Disable"
        Consider setting to `False` when:
        - Serving files directly from filesystem
        - Using Amazon S3 static hosting
        - Working with systems that don't support URL rewrites

    !!! example "Configuration"
        ```yaml
        use_directory_urls: true  # default
        # or
        use_directory_urls: false  # for file-based URLs
        ```
    """

    strict: bool = Field(False)
    """Controls how MkDocs handles warnings during build process.

    !!! info "Behavior"
        - `True`: Treats warnings as errors, fails build
        - `False`: Shows warnings but continues build

    !!! tip "Use Cases"
        Enable strict mode for:
        - CI/CD pipelines
        - Quality assurance
        - Pre-release validation

    !!! example "Configuration"
        ```yaml
        strict: true
        ```
    """

    dev_addr: str = Field("127.0.0.1:8000")
    """Specifies the IP address and port for the development server.

    !!! info "Format"
        Must follow the pattern: `IP:PORT`

    !!! warning "Validation Rules"
        - IP must be valid IPv4/IPv6 address
        - Port must be between 1-65535
        - Common ports (80, 443) may require privileges

    !!! example "Configuration Options"
        ```yaml
        dev_addr: 127.0.0.1:8000  # default, localhost only
        dev_addr: 0.0.0.0:8000    # allow external access
        dev_addr: localhost:8080   # alternate port
        ```
    """

    extra_css: list[FilePath] | None = Field(None)
    """Custom CSS files to include in the documentation.

    !!! info "Processing"
        - Files are copied from `docs_dir` to `site_dir`
        - Included in HTML as `<link>` tags
        - Applied after theme CSS

    !!! tip "Best Practices"
        - Use for custom styling
        - Override theme defaults
        - Maintain responsive design

    !!! example "Configuration"
        ```yaml
        extra_css:
          - css/custom.css
          - css/print.css
          - css/responsive.css
        ```
    """

    extra_javascript: list[FilePath] | None = Field(None)
    """Custom JavaScript files to include in the documentation.

    !!! info "File Types"
        - Regular `.js` files
        - ES6 modules (`.mjs`)
        - Async/deferred scripts

    !!! tip "Advanced Usage"
        You can specify script attributes:
        ```yaml
        extra_javascript:
          - path: js/analytics.js
            defer: true
          - path: js/module.mjs
            type: module
            async: true
        ```

    !!! warning "Loading Order"
        Scripts are loaded after theme JavaScript files
    """

    markdown_extensions: list[str | dict[str, Any]] | None = Field(None)
    """PyMarkdown extensions and their configurations.

    !!! info "Default Extensions"
        Built-in enabled extensions:
        - `meta`
        - `toc`
        - `tables`
        - `fenced_code`

    !!! tip "Popular Extensions"
        ```yaml
        markdown_extensions:
          - admonition
          - codehilite:
              guess_lang: false
          - toc:
              permalink: true
          - pymdownx.superfences
        ```

    !!! example "Advanced Configuration"
        ```yaml
        markdown_extensions:
          - pymdownx.highlight:
              anchor_linenums: true
          - pymdownx.inlinehilite
          - pymdownx.snippets
          - pymdownx.superfences:
              custom_fences:
                - name: mermaid
                  class: mermaid
                  format: !!python/name:pymdownx.superfences.fence_code_format
        ```
    """

    hooks: list[str] | None = Field(None)
    """Python scripts that extend the build process.

    !!! info "Hook Types"
        Hooks can implement various event handlers:
        - `on_pre_build`
        - `on_files`
        - `on_nav`
        - `on_page_read`
        - `on_page_markdown`
        - `on_page_content`
        - `on_post_build`

    !!! warning "Development Server"
        Hook modules are not reloaded during `mkdocs serve`

    !!! example "Configuration"
        ```yaml
        hooks:
          - hooks/process_images.py
          - hooks/custom_navigation.py
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
    """The locale of the documentation.

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
    """Controls the validation behavior for links, content, and navigation.

    !!! info "Validation Levels"
        | Level   | Description |
        |---------|-------------|
        | `warn`  | Show warnings but continue |
        | `info`  | Show informational messages |
        | `ignore`| Skip validation |

    !!! example "Configuration"
        ```yaml
        validation:
          nav:
            omitted_files: warn
          links:
            check_external: true
            anchors: warn
        ```

    !!! tip "Recommended Settings"
        Enable strict validation in CI/CD pipelines:
        ```yaml
        validation:
          links:
            check_external: true
            anchors: strict
          nav:
            omitted_files: strict
        ```
    """

    watch: list[DirectoryPath] | None = Field(None)
    """Additional directories to monitor for changes during development.

    !!! info "Behavior"
        - Automatically rebuilds site when files change
        - Supplements default watching of `docs_dir`
        - Useful for template and theme development

    !!! example "Configuration"
        ```yaml
        watch:
          - src/docs/
          - custom_theme/
          - templates/
        ```
    """

    exclude_docs: GitIgnorePatterns = Field(default_factory=list)
    """Gitignore-style patterns for files to exclude from documentation.

    !!! info "Pattern Syntax"
        Uses `.gitignore` pattern format:
        - `*` matches any sequence of characters
        - `**` matches across directories
        - `?` matches single character
        - `!` negates a pattern

    !!! example "Common Exclusions"
        ```yaml
        exclude_docs:
          - '*.tmp'
          - 'drafts/*.md'
          - '.git/**'
          - 'internal/**/*.md'
        ```

    !!! warning "Path Resolution"
        Patterns are relative to `docs_dir`
    """

    not_in_nav: GitIgnorePatterns = Field(default_factory=list)
    """Patterns for files that should not generate warnings when not in navigation.

    !!! info "Use Cases"
        - Include files (partials)
        - Template files
        - Asset documentation
        - Supporting content

    !!! example "Configuration"
        ```yaml
        not_in_nav:
          - 'includes/*.md'
          - 'assets/templates/*'
          - '_snippets/**'
        ```

    !!! tip "Best Practices"
        Use this to suppress warnings for files that are:
        - Intentionally excluded from navigation
        - Used as includes/partials
        - Referenced programmatically
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
