from __future__ import annotations

from collections.abc import Callable
import pathlib
import re

import jinja2


class RewriteLoader(jinja2.BaseLoader):
    def __init__(self, loader: jinja2.BaseLoader):
        self.loader = loader

    def get_source(
        self,
        environment: jinja2.Environment,
        template: str,
    ) -> tuple[str, str, Callable[[], bool] | None]:
        src: str | None
        src, filename, uptodate = self.loader.get_source(environment, template)
        old_src = src
        assert filename is not None
        path = pathlib.Path(filename).as_posix()
        src = adapt_template(path, src)
        return src or old_src, filename, uptodate


def adapt_template(path, src):
    if path.endswith("/material/templates/partials/nav-item.html"):
        src = src.replace(
            r'{% set is_expanded = "navigation.expand" in features %}',
            r'{% set is_expanded = "navigation.expand" in features or (page and page.meta'
            r" and page.meta.nav_expanded) %}",
        )
        src = src.replace(
            r'{% set sections = "navigation.sections" in features %}',
            r'{% set sections = "navigation.sections" in features or (page and page.meta'
            r" and page.meta.nav_sections) %}",
        )
    if "/material/templates/" in path:
        return re.sub(
            r"{% include \"\.icons/\" ~ (.*) ~ \"\.svg\" %}",
            r"{{ \g<1> | get_icon_svg }}",
            src,
        )
        # return re.sub(
        #     r"{% import \"\.icons/\" ~ (.*) ~ \"\.svg\" as (.*) %}",
        #     r"{% set \g<2> = \g<1> | get_icon_svg %}",
        #     src,
        # )
    return src
