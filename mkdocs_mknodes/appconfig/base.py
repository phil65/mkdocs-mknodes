from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel, Field
import yamling


if TYPE_CHECKING:
    import os


class ConfigFile(BaseModel):
    """Base class for config files.

    A class for loading and managing configuration files in YAML format.
    Supports inheritance between config files and provides methods for
    loading from files or YAML text.
    """

    config_file_path: str | None = Field(None, exclude=True)
    # Either exclude here or add inherit field to MkNodesConfig?
    inherit: str | None = Field(None, exclude=True, alias="INHERIT")
    """Define the parent for a configuration file.

    The path must be relative to the location of the primary file.
    """

    @classmethod
    def from_yaml_file(cls, yaml_path: str | os.PathLike[str], **overrides: Any) -> Self:
        """Create a ConfigFile instance from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file
            **overrides: Additional key-value pairs to override values from the file

        Returns:
            A new instance of the ConfigFile class initialized with the YAML data
        """
        cfg = yamling.load_yaml_file(yaml_path)
        vals = {"config_file_path": str(yaml_path), **cfg, **overrides}
        return cls(**vals)

    @classmethod
    def from_yaml(cls, text: yamling.YAMLInput, **overrides: Any) -> Self:
        """Create a ConfigFile instance from YAML text.

        Args:
            text: YAML content as text or file-like object
            **overrides: Additional key-value pairs to override values from the YAML

        Returns:
            A new instance of the ConfigFile class initialized with the YAML data
        """
        cfg = yamling.load_yaml(text, resolve_inherit=True)
        path = {"config_file_path": str(text.name)} if getattr(text, "name", None) else {}  # type: ignore
        vals = {**path, **cfg, **overrides}
        return cls(**vals)

    def to_yaml(self) -> str:
        """Convert the configuration to YAML format.

        Returns:
            A string containing the YAML representation of the configuration
        """
        cfg = self.model_dump()
        return yamling.dump_yaml(cfg)
