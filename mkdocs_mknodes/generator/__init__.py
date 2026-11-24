"""Engine-agnostic site generator.

Runs a MkNodes build function, collects the result into an engine-neutral
`BuildOutput` (`mknodes.build`) and lets a writer
(see `mkdocs_mknodes.writers`) produce the input files for a site engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mknodes.build import BuildOutput, NavItem, Script, SiteMetadata
from mkdocs_mknodes.generator.settings import GeneratorSettings


if TYPE_CHECKING:
    import pathlib


def generate_output(settings: GeneratorSettings, flavor: str | None = None) -> BuildOutput:
    """Run the build function of given settings and return the collected output.

    Args:
        settings: Generator settings
        flavor: Markdown flavour (default: the `flavor` setting, else `material`)
    """
    from mkdocs_mknodes.generator.generator import SiteGenerator

    return SiteGenerator(settings, flavor=flavor).generate()


def generate(
    settings: GeneratorSettings | None = None,
    engine: str = "zensical",
    **overrides: Any,
) -> pathlib.Path:
    """Generate the site input for given engine. Returns the config file to build with.

    Args:
        settings: Generator settings (default: loaded from the current folder)
        engine: Name of the writer to use
        overrides: Setting overrides used when settings get loaded
    """
    from mkdocs_mknodes.writers import get_writer

    settings = settings or GeneratorSettings.load(**overrides)
    writer = get_writer(engine)(settings)
    output = generate_output(settings, flavor=writer.resolved_flavor)
    return writer.write(output)


__all__ = [
    "BuildOutput",
    "GeneratorSettings",
    "NavItem",
    "Script",
    "SiteMetadata",
    "generate",
    "generate_output",
]
