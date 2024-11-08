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

from typing import Annotated, Any

from pydantic import BeforeValidator, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
import upath


def _convert_to_upath(value: Any) -> upath.UPath:
    """Convert a value to a UPath object.

    Args:
        value: Input value to convert (string, PathLike, or UPath)

    Returns:
        UPath: Converted UPath object

    Raises:
        TypeError: If the value cannot be converted to a UPath
    """
    try:
        return upath.UPath(value)
    except (TypeError, ValueError) as e:
        msg = f"Cannot convert {value!r} to UPath: {e}"
        raise TypeError(msg) from e


def _validate_path_exists(path: upath.UPath) -> upath.UPath:
    """Validate that a path exists.

    Args:
        path: UPath object to validate

    Returns:
        UPath: The validated path

    Raises:
        ValueError: If the path does not exist
    """
    path = upath.UPath(path)
    if not path.exists():
        msg = f"Path does not exist: {path}"
        raise ValueError(msg)
    return path


def _validate_is_file(path: upath.UPath) -> upath.UPath:
    """Validate that a path points to a file.

    Args:
        path: UPath object to validate

    Returns:
        UPath: The validated path

    Raises:
        ValueError: If the path is not a file
    """
    path = upath.UPath(path)
    if not path.is_file():
        msg = f"Path is not a file: {path}"
        raise ValueError(msg)
    return path


def _validate_is_dir(path: upath.UPath) -> upath.UPath:
    """Validate that a path points to a directory.

    Args:
        path: UPath object to validate

    Returns:
        UPath: The validated path

    Raises:
        ValueError: If the path is not a directory
    """
    path = upath.UPath(path)
    if not path.is_dir():
        msg = f"Path is not a directory: {path}"
        raise ValueError(msg)
    return path


class UPath:
    """A Pydantic type for universal_pathlib.UPath.

    This type handles conversion of strings and path-like objects to UPath objects,
    with proper serialization support. It can be used directly in Pydantic models
    and supports validation via the provided validator types.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Generate the Pydantic core schema for UPath type."""
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(upath.UPath),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(_convert_to_upath),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x), return_schema=core_schema.str_schema(), when_used="json"
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """Generate the JSON schema for UPath type."""
        return {"type": "string", "format": "path"}


# Type aliases with validation
UPathExists = Annotated[UPath, BeforeValidator(_validate_path_exists)]
UPathFile = Annotated[UPathExists, BeforeValidator(_validate_is_file)]
UPathDir = Annotated[UPathExists, BeforeValidator(_validate_is_dir)]


# Example usage with type annotations
if __name__ == "__main__":
    from pydantic import BaseModel

    class FileConfig(BaseModel):
        """Example configuration using UPath types."""

        input_file: UPathFile
        output_dir: UPathDir
        temp_path: UPath

        model_config = {
            "frozen": True,
            "extra": "forbid",
        }

    try:
        config = FileConfig(
            input_file="github://phil65:mknodes@main/README.md",
            output_dir="output",
            temp_path="temp/workspace",
        )
        print(f"{config=!r}")
    except ValueError as e:
        print(f"Validation error: {e}")
