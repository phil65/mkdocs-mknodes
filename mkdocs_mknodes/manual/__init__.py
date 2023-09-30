"""Module containing the documentation."""

from .nodes_section import create_nodes_section
from .navs_section import create_navs_section
from .cli_section import create_cli_section
from .internals_section import create_internals_section
from .dev_section import create_development_section
from .templating_section import create_templating_section
from .use_cases_section import create_use_cases_section
from .root import build
from . import routing
from .index_page import create_index_page

__all__ = [
    "create_nodes_section",
    "create_navs_section",
    "create_cli_section",
    "create_internals_section",
    "create_templating_section",
    "create_development_section",
    "create_use_cases_section",
    "build",
    "routing",
    "create_index_page",
]
