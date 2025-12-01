from __future__ import annotations

import functools
import ipaddress
from typing import TYPE_CHECKING, Annotated, Any

from mknodes.utils import classhelpers
from pathspec import gitignore
from pydantic import BaseModel, DirectoryPath, Field, HttpUrl, ValidationInfo, field_validator
from pydantic.functional_validators import BeforeValidator
from pydantic_core import PydanticCustomError

from mkdocs_mknodes.appconfig import jinjaconfig, themeconfig, validationconfig
from mkdocs_mknodes.appconfig.base import ConfigFile


if TYPE_CHECKING:
    from collections.abc import Callable


def validate_gitignore_patterns(pattern: list[str] | str) -> str:
    """Validate a list of gitignore patterns using pathspec."""
    patterns = pattern.splitlines() if isinstance(pattern, str) else pattern
    pattern_str = pattern if isinstance(pattern, str) else "\n".join(pattern)
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
        return pattern_str


GitIgnorePatterns = Annotated[
    str,
    BeforeValidator(validate_gitignore_patterns),
]


class NavItem(BaseModel):
    """Represents a navigation item in the MkDocs configuration.

    Can be a string (for a simple link) or a dict (for nested navigation).
    """

    item: str | dict[str, NavItem]


class PluginConfig(BaseModel):
    """Configuration for a MkDocs plugin."""

    name: str = Field(..., description="The name of the plugin.")
    config: dict[str, Any] | None = Field(
        None, description="Plugin-specific configuration options."
    )


class ExtraJavascript(BaseModel):
    path: str
    type: str | None = None
    async_: bool | None = Field(None, alias="async")
    defer: bool | None = None


class AppConfig(ConfigFile):
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

    site_url: str | None = Field(None)
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

    build_fn: str = "mkdocs_mknodes:parse"
    """Path to the build script / callable.

    Possible formats:

      - `my.module:Class.build_fn` (must be a classmethod / staticmethod)
      - `my.module:build_fn`
      - `path/to/file.py:build_fn`

    Can also be remote.
    The targeted callable gets the project instance as an argument and optionally
    keyword arguments from setting below.
    """
    build_fn_arguments: dict[str, Any] | None = None
    """Keyword arguments passed to the build script / callable.

    Build scripts may have keyword arguments. You can set them by using this setting.
    """
    repo_path: str = "."
    """Path to the repository to create a website for. (`http://....my_project.git`)"""
    clone_depth: int = 100
    """Clone depth in case the repository is remote. (Required for `git-changelog`)."""
    build_folder: str | None = None
    """Folder to create the Markdown files in.

    If no folder is set, **MkNodes** will generate a temporary dir."""
    show_page_info: bool = True
    """Append an admonition box with build-related information.

    If True, all pages get added an expandable admonition box at the bottom,
    containing information about the created page.
    This includes:
    - Metadata
    - Resources
    - Code which created the page (needs the page to be created via decorators, or
    the `generated_by` attribute of the `MkPage` needs to be set manually)
    """
    rewrite_theme_templates: bool = True
    """Add additional functionality to themes by rewriting template files.

    MkNodes can rewrite the HTML templates of Themes in order to add additional
    functionality.

    Right now, enabling this feature allows these options for the **Material-MkDocs**
    theme:
    - use iconify icons instead of the **Material-MkDocs** icons
    - setting the theme features "navigation.indexes" and "navigation.expand" via
      page metadata.
    """
    auto_delete_generated_templates: bool = True
    """Delete the generated HTML templates when build is finished.

    MkNodes may generate HTML template overrides during the build process and
    deletes them after build. Using this setting, the deletion can be prevented.
    """
    render_by_default: bool = True
    """Render all pages in the jinja environment.

    This allows to render jinja in the **MkNodes** environment outside of the `MkJinja`
    nodes.

    This setting can be overridden by setting the page metadata field "render_macros".
    """
    global_resources: bool = True
    """Make resources globally available.

    If True, then the resources inferred from the nodes will be put into all HTML pages.
    (This reflects the "default" MkDocs mechanism of putting extra CSS / JS into the
    config file)
    If False, then MkNodes will put the CSS / JS only into the pages which need it.
    (the resources will be moved into the appropriate page template blocks)
    """
    jinja_config: jinjaconfig.JinjaConfig = Field(default_factory=jinjaconfig.JinjaConfig)
    """Contains the configuration for the Jinja2 Environment.

    Allows setting up loaders, extensions and the render behavior.
    """
    docs_dir: str = Field("docs")
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

    site_dir: str = Field("site")
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

    theme: themeconfig.ThemeConfig = Field(default_factory=themeconfig.ThemeConfig)
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
    # pydantic.FilePath would be nice.. Looses bw compat to old mkdocs filess
    extra_css: list[str] | None = Field(None)
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

    extra_javascript: list[str | ExtraJavascript] | None = Field(None)
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

    markdown_extensions: list[dict[str, Any]] | None = Field(None)
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

    nav: list[dict[str, Any] | str] | None = Field(None)
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

    extra: dict[str, Any] = Field(default_factory=dict)
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

    validation: validationconfig.ValidationConfig | None = Field(None)
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
    # DirectoryPath would be nice
    watch: list[str] | None = Field(None)
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

    exclude_docs: GitIgnorePatterns = Field(default="")
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

    not_in_nav: GitIgnorePatterns = Field(default="")
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

    @field_validator("plugins", "markdown_extensions", mode="before")
    @classmethod
    def convert_to_plugin_dict_list(
        cls,
        value: list[str | dict[str, dict[str, Any]]] | dict[str, Any],
        info: ValidationInfo,
    ) -> list[dict[str, dict[str, Any]]]:
        result: list[dict[str, Any]] = []
        match value:
            case dict():
                # Convert dict to list of single-key dicts
                for k, v in value.items():
                    result.append({k: v})
            case list():
                for item in value:
                    match item:
                        case str():
                            result.append({item: {}})
                        case dict():
                            if len(item) > 1:
                                f = info.field_name
                                msg = f"{f} dictionaries must have a single key"
                                raise ValueError(msg)
                            result.append(item)
                        case _:
                            type_str = f"{item!r} ({type(item)})"
                            f = info.field_name
                            msg = f"Invalid type for {f} section: {type_str}"
                            raise ValueError(msg)
        return result

    @field_validator("extra_javascript", mode="before")
    @classmethod
    def validate_extra_javascript(
        cls, values: list[dict[str, Any] | str]
    ) -> list[ExtraJavascript | str]:
        items: list[ExtraJavascript | str] = []
        for value in values:
            if isinstance(value, str):
                if value.endswith(".mjs"):
                    item = ExtraJavascript(path=value, type="module")
                    items.append(item)
                    continue
                items.append(value)
                continue
            item = ExtraJavascript(**value)
            items.append(item)
        return items

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

    def get_builder(self) -> Callable[..., Any]:
        build_fn = classhelpers.to_callable(self.build_fn)
        build_kwargs = self.build_fn_arguments or {}
        return functools.partial(build_fn, **build_kwargs)

    def set_theme(
        self,
        theme: str | dict[str, Any] | themeconfig.ThemeConfig,
        **kwargs: Any,
    ):
        match theme:
            case themeconfig.ThemeConfig():
                self.theme = theme
            case dict():
                self.theme = themeconfig.ThemeConfig(**{**theme, **kwargs})
            case str():
                self.theme = themeconfig.ThemeConfig(name=theme, **kwargs)

    def remove_plugin(self, name: str):
        for plg in self.plugins:
            if plg == name or (isinstance(plg, dict) and next(iter(plg.keys())) == name):
                self.plugins.remove(plg)

    # @field_validator("theme", mode="before")
    # @classmethod
    # def validate_theme(cls, value: Any) -> ThemeConfig:
    #     if isinstance(value, dict):
    #         return themeconfig.ThemeConfig(**value)
    #     if isinstance(value, themeconfig.ThemeConfig):
    #         return value
    #     raise ValueError("Address must be either a dict or Address instance")


if __name__ == "__main__":
    import devtools

    tests = [
        "https://raw.githubusercontent.com/squidfunk/mkdocs-material/master/mkdocs.yml",
        # "https://raw.githubusercontent.com/fastapi-users/fastapi-users/master/mkdocs.yml",
        # "https://raw.githubusercontent.com/pydantic/pydantic/main/mkdocs.yml",
        # "https://raw.githubusercontent.com/facelessuser/pymdown-extensions/refs/heads/main/mkdocs.yml",
    ]
    for url in tests:
        config = AppConfig.from_yaml_file(url)

        devtools.debug(config.theme)
        print(config.theme, type(config.theme))
