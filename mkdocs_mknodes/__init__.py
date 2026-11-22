from .mkdefaultwebsite import MkDefaultWebsite
from . import telemetry
from importlib.metadata import version

telemetry.setup_logfire()

__version__ = version("mkdocs-mknodes")


async def parse(root, theme, pages=None):
    """Default build function.

    Builds the nav from the `pages` plugin setting if given, otherwise creates a
    default website (README index page, API docs, CLI docs and development infos).
    """
    if not pages:
        from mkdocs_mknodes.mkdefaultwebsite import populate_default_website

        populate_default_website(root)
        return root

    from mknodes.navs.navparser import parse_new_style_nav

    await parse_new_style_nav(root, pages)
    return root


__all__ = ["MkDefaultWebsite"]
