"""Module containing the BuildCollector class."""

from __future__ import annotations

import collections
import dataclasses

import mknodes as mk

from mknodes.info import contexts
from mknodes.utils import log, resources


logger = log.get_logger(__name__)


@dataclasses.dataclass
class BuildContext(contexts.Context):
    """Information about a website build."""

    page_mapping: dict = dataclasses.field(default_factory=dict)
    """A dictionary mapping all page filenames to the corresponding MkPages."""
    resources: resources.Resources = dataclasses.field(
        default_factory=resources.Resources,
    )
    """All resources (JS, CSS, extensions) inferred from the build."""
    # node_stats: list[contexts.NodeBuildStats] = dataclasses.field(default_factory=list)
    """Some stats about nodes construction."""
    build_files: dict = dataclasses.field(default_factory=dict)
    """A mapping of filepaths -> Markdown."""
    node_counter: collections.Counter = dataclasses.field(
        default_factory=collections.Counter,
    )
    """Counter containing the amount of creations for each node class."""
    templates: list[mk.PageTemplate] = dataclasses.field(default_factory=list)
    """A list of required templates."""

    # original_config: dict = dataclasses.field(default_factory=dict)
    # config_override: dict = dataclasses.field(default_factory=dict)
    # final_config: dict[str, str] = dataclasses.field(default_factory=dict)


if __name__ == "__main__":
    ctx = BuildContext()
