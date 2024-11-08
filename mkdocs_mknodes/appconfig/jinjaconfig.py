from __future__ import annotations

import jinjarope
from pydantic import BaseModel, Field


class JinjaConfig(BaseModel):
    jinja_block_start_string: str | None = None
    """Jinja block start string."""
    jinja_block_end_string: str | None = None
    """Jinja block end string."""
    jinja_variable_start_string: str | None = None
    """Jinja variable start string."""
    jinja_variable_end_string: str | None = None
    """Jinja variable end string."""
    jinja_on_undefined: str = Field("strict")
    """Jinja undefined macro behavior."""
    jinja_loaders: list[JinjaLoader] | None = None
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
    jinja_extensions: list[str] | None = None
    """List containing additional jinja extensions to use.

    Examples:
        ``` yaml
        plugins:
        - mknodes:
            jinja_extensions:
            - jinja2_ansible_filters.AnsibleCoreFiltersExtension
        ```
    """

    def get_jinja_config(self) -> jinjarope.EnvConfig:
        return jinjarope.EnvConfig(
            block_start_string=self.jinja_block_start_string or "{%",
            block_end_string=self.jinja_block_end_string or "%}",
            variable_start_string=self.jinja_variable_start_string or r"{{",
            variable_end_string=self.jinja_variable_end_string or r"}}",
            # undefined=self.jinja_on_undefined,
            loader=jinjarope.loaders.from_json(self.jinja_loaders),
            extensions=self.jinja_extensions or [],
        )


class JinjaLoader(BaseModel):
    typ: str
    path: str
