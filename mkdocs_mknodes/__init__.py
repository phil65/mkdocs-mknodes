from .mkdefaultwebsite import MkDefaultWebsite
from . import telemetry
from importlib.metadata import version

telemetry.setup_logfire()

__version__ = version("mkdocs-mknodes")


async def parse(root, theme, pages):
    from mknodes.navs.navparser import parse_new_style_nav

    await parse_new_style_nav(root, pages)
    return root


__all__ = ["MkDefaultWebsite"]
