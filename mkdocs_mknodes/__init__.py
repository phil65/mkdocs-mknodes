__version__ = "0.5.3"


from .mkdefaultwebsite import MkDefaultWebsite
from . import telemetry

telemetry.setup_logfire()


def parse(root, theme, pages):
    from mknodes.navs.navparser import parse_new_style_nav

    parse_new_style_nav(root, pages)
    return root


__all__ = ["MkDefaultWebsite"]
