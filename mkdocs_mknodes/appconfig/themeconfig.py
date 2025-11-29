"""Pydantic types for universal_pathlib (upath.UPath) with validation capabilities.

This module provides a Pydantic-compatible type for upath.UPath,
offering similar functionality to Pydantic's built-in Path type. It includes
validators for existence checks and path type verification.

Example:
    ```python
    from pydantic import BaseModel

    class Config(BaseModel):
        input_file: UPathFile
        output_dir: UPathDir
        temp_path: UPath

    # Usage
    config = Config(
        input_file="data.csv",
        output_dir="output",
        temp_path="temp/workspace"
    )
    ```
"""

from typing import Any, Self

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


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

    name: str = Field("material")
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
    # pydantic.DirectoryPath would be better
    custom_dir: str | None = Field(None)
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

    locale: str | None = Field("en")
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

    @model_validator(mode="before")
    @classmethod
    def validate_theme_config(cls, data: Self | dict[str, Any] | str) -> Self | dict[str, Any]:
        if isinstance(data, cls):
            # Return the ThemeConfig instance as is
            return data
        if isinstance(data, str):
            # Initialize ThemeConfig with name=string
            return {"name": data}
        if isinstance(data, dict):
            # Validate using the standard model validation
            return data
        msg = "ThemeConfig must be a str, ThemeConfig instance, or dict"
        raise TypeError(msg)

    # @field_validator("locale")
    # @classmethod
    # def validate_language(cls, v: str | None) -> str | None:
    #     import babel

    #     if v and v not in babel.core.LOCALE_ALIASES:
    #         raise ValueError(f"Invalid language code: {v}")
    #     return v


if __name__ == "__main__":
    # Example usage:
    class MyConfig(BaseModel):
        theme: ThemeConfig

    # Passing a string
    config1 = MyConfig(theme="material")
    print(config1)

    # Passing a ThemeConfig instance
    theme_config = ThemeConfig(name="material", locale="en_US")
    config2 = MyConfig(theme=theme_config)
    print(config2)

    # Passing a dict
    config3 = MyConfig(theme={"name": "material", "locale": "en_US"})
    print(config3)
