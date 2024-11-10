from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import TypedDict

from jinjarope import htmlfilters
from mkdocs import utils
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page

from mkdocs_mknodes.plugin.mknodesconfig import MkNodesConfig


class TemplateContext(TypedDict):
    nav: Navigation
    pages: Sequence[File]
    base_url: str
    extra_css: Sequence[str]  # Do not use, prefer `config.extra_css`.
    extra_javascript: Sequence[str]  # Do not use, prefer `config.extra_javascript`.
    mkdocs_version: str
    mknodes_version: str
    build_date_utc: datetime
    config: MkNodesConfig
    page: Page | None


def get_context(
    nav: Navigation,
    files: Sequence[File] | Files,
    config: MkNodesConfig,
    page: Page | None = None,
    base_url: str = "",
) -> TemplateContext:
    """Return the template context for a given page or template."""
    if page is not None:
        base_url = htmlfilters.relative_url_mkdocs(".", page.url)

    extra_javascript = [
        htmlfilters.normalize_url(str(script), page.url if page else None, base_url)
        for script in config.extra_javascript
    ]
    extra_css = [
        htmlfilters.normalize_url(path, page.url if page else None, base_url)
        for path in config.extra_css
    ]

    if isinstance(files, Files):
        files = files.documentation_pages()

    import mkdocs

    import mkdocs_mknodes

    return TemplateContext(
        nav=nav,
        pages=files,
        base_url=base_url,
        extra_css=extra_css,
        extra_javascript=extra_javascript,
        mknodes_version=mkdocs_mknodes.__version__,
        mkdocs_version=mkdocs.__version__,
        build_date_utc=utils.get_build_datetime(),
        config=config,
        page=page,
    )
