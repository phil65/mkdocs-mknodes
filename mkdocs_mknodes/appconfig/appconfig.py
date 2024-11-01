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

    name: str = Field(..., description="The name of the theme to use.")
    custom_dir: DirectoryPath | None = Field(
        None, description="Directory containing a custom theme."
    )
    static_templates: list[str] | None = Field(
        None, description="List of templates to render as static pages."
    )
    locale: str | None = Field(
        None, description="The locale to use for the theme (e.g., 'en' or 'fr')."
    )
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

    config_file_path: str | None = Field(None, description="Path to the config file.")

    # Site information
    site_name: str = Field(..., description="The name of the project documentation.")
    site_url: HttpUrl | None = Field(
        None, description="The URL where the documentation will be hosted."
    )
    site_description: str | None = Field(
        None, description="A description of the documentation project."
    )
    site_author: str | None = Field(None, description="The author of the documentation.")
    copyright: str | None = Field(
        None, description="A copyright statement for the documentation."
    )

    # Repository information
    repo_name: str | None = Field(None, description="The name of the source repository.")
    repo_url: HttpUrl | None = Field(
        None, description="The URL of the source repository."
    )
    edit_uri: str | None = Field(
        None, description="Path to the docs directory in the source repository."
    )
    remote_branch: str | None = Field(
        None, description="The remote branch to point to (default: 'master')."
    )
    remote_name: str | None = Field(
        None, description="The remote name to push to (default: 'origin')."
    )

    # Configuration directories
    docs_dir: DirectoryPath = Field(
        "docs", description="The directory containing the documentation source files."
    )
    site_dir: DirectoryPath = Field(
        "site", description="The directory where the output HTML will be created."
    )
    extra_templates: list[DirectoryPath] | None = Field(
        None, description="List of directories containing extra Jinja2 templates."
    )

    # Theme configuration
    theme: ThemeConfig = Field(
        ..., description="The theme configuration for the documentation."
    )

    # Build configuration
    use_directory_urls: bool = Field(
        True, description="Use directory URLs when building pages (default: True)."
    )
    strict: bool = Field(
        False, description="Enable strict mode for warnings as errors (default: False)."
    )
    dev_addr: str = Field(
        "127.0.0.1:8000", description="The server address for the development server."
    )
    extra_css: list[FilePath] | None = Field(
        None, description="List of CSS files to include in the documentation."
    )
    extra_javascript: list[FilePath] | None = Field(
        None, description="List of JavaScript files to include in the documentation."
    )

    # Markdown extensions
    markdown_extensions: list[str | dict[str, Any]] | None = Field(
        None, description="List of Markdown extensions to use."
    )
    hooks: list[str] | None = Field(
        None, description="List of Python scripts to load as hooks."
    )

    # Navigation
    nav: list[NavItem] | None = Field(
        None, description="The navigation structure for the documentation."
    )

    # Plugins
    plugins: list[dict[str, Any]] = Field(
        default_factory=list, description="List of plugins to use."
    )

    # Internationalization
    language: str | None = Field(
        None, description="The language of the documentation (as a BCP 47 language tag)."
    )
    locale: str | None = Field(
        None, description="The locale of the documentation (e.g., 'en_US')."
    )

    # Additional options
    extra: dict[str, Any] | None = Field(
        None, description="A set of key-value pairs for custom data in templates."
    )
    validation: dict[str, Any] | None = Field(
        None, description="Validation options for external links and fragments."
    )
    watch: list[DirectoryPath] | None = Field(
        None, description="List of directories to watch for changes."
    )
    exclude_docs: GitIgnorePatterns = Field(
        default_factory=list,
        description="Gitignore-like file patterns to exclude pages from the site.",
    )

    not_in_nav: GitIgnorePatterns = Field(
        default_factory=list,
        description="Gitignore-like file patterns to exclude pages from nav.",
    )

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
