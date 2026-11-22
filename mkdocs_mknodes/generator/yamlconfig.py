"""Round-trip helpers for MkDocs-style YAML config files.

MkDocs configs may contain custom tags (`!ENV`, `!!python/name:...`). The generator never
executes them: it loads them as [Tagged][mkdocs_mknodes.generator.yamlconfig.Tagged] values
and dumps them back unchanged, so a generated config can safely repeat values of the
config it inherits from.
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import types
from typing import Any

import yaml


PYTHON_NAME_TAG = "tag:yaml.org,2002:python/name:"


@dataclasses.dataclass
class Tagged:
    """A YAML node with a custom tag, kept verbatim."""

    tag: str
    value: Any


class _Loader(yaml.SafeLoader):
    pass


def _construct_tagged(loader: _Loader, _suffix: str, node: yaml.Node) -> Tagged:
    value: Any
    match node:
        case yaml.ScalarNode():
            value = loader.construct_scalar(node)
        case yaml.SequenceNode():
            value = loader.construct_sequence(node, deep=True)
        case yaml.MappingNode():
            value = loader.construct_mapping(node, deep=True)
        case _:
            value = None
    return Tagged(node.tag, value)


_Loader.add_multi_constructor("!", _construct_tagged)
_Loader.add_multi_constructor("tag:yaml.org,2002:python/", _construct_tagged)


class _Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _represent_tagged(dumper: _Dumper, data: Tagged) -> yaml.Node:
    match data.value:
        case list():
            return dumper.represent_sequence(data.tag, data.value)
        case dict():
            return dumper.represent_mapping(data.tag, data.value)
        case None:
            return dumper.represent_scalar(data.tag, "")
        case _:
            return dumper.represent_scalar(data.tag, str(data.value))


def _represent_callable(dumper: _Dumper, data: Any) -> yaml.Node:
    name = f"{data.__module__}.{data.__qualname__}"
    return dumper.represent_scalar(PYTHON_NAME_TAG + name, "")


def _represent_unknown(dumper: _Dumper, data: Any) -> yaml.Node:
    if callable(data) and hasattr(data, "__qualname__") and hasattr(data, "__module__"):
        return _represent_callable(dumper, data)
    msg = f"Cannot serialize {data!r} into a YAML config"
    raise yaml.representer.RepresenterError(msg)


def _represent_str(dumper: _Dumper, data: str) -> yaml.Node:
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(Tagged, _represent_tagged)
_Dumper.add_representer(str, _represent_str)
for _typ in (types.FunctionType, types.BuiltinFunctionType, type):
    _Dumper.add_multi_representer(_typ, _represent_callable)
_Dumper.add_multi_representer(object, _represent_unknown)
_Dumper.add_representer(pathlib.PosixPath, lambda d, v: d.represent_str(v.as_posix()))
_Dumper.add_representer(pathlib.WindowsPath, lambda d, v: d.represent_str(v.as_posix()))


def loads(text: str) -> Any:
    """Load YAML text, keeping custom tags as `Tagged` values."""
    return yaml.load(text, Loader=_Loader)


def dumps(data: Any) -> str:
    """Dump data to YAML (`Tagged` values and callables become tags again)."""
    return yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)


def merge_inherited(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Merge configs the way MkDocs `INHERIT` does: mappings merge, the rest is replaced."""
    for key, value in child.items():
        if isinstance(parent.get(key), dict) and isinstance(value, dict):
            parent[key] = merge_inherited(parent[key], value)
        else:
            parent[key] = value
    return parent


def load_file(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load a MkDocs YAML config file and resolve `INHERIT` chains."""
    path = pathlib.Path(path)
    data = loads(path.read_text(encoding="utf-8")) or {}
    if parent_path := data.pop("INHERIT", None):
        parent = load_file(path.parent / str(parent_path))
        data = merge_inherited(parent, data)
    return data


def resolve(value: Any) -> Any:
    """Resolve `!ENV` tags in given value (recursively) to plain Python values."""
    match value:
        case Tagged(tag="!ENV", value=val):
            names = val if isinstance(val, list) else [val]
            default = names[-1] if isinstance(val, list) and len(names) > 1 else None
            if isinstance(val, list) and len(names) > 1:
                names = names[:-1]
            for name in names:
                if name in os.environ:
                    return yaml.safe_load(os.environ[name])
            return default
        case dict():
            return {k: resolve(v) for k, v in value.items()}
        case list():
            return [resolve(v) for v in value]
        case _:
            return value
