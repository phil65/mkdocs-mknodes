from __future__ import annotations

import re

from mknodes.utils import log


logger = log.get_logger(__name__)

MKDOCS_TOC_PRE = """\
                {%- block content %}
                    <div class="col-md-3">{% include "toc.html" %}</div>
                    <div class="col-md-9" role="main">{% include "content.html" %}</div>
                {%- endblock %}
"""


MKDOCS_TOC_AFTER = """\
                {% set hide_toc = (page.meta and page.meta.hide and "toc" in page.meta.hide) or not page.toc %}
                {%- block content %}
                    {% if not hide_toc %}<div class="col-md-3">{% include "toc.html" %}</div>{% endif %}
                    <div class="col-md-{{"12" if hide_toc else "9"}}" role="main">{% include "content.html" %}</div>
                {%- endblock %}

"""  # noqa: E501


def rewrite(path, src):
    if path.endswith("mkdocs/themes/mkdocs/base.html"):
        logger.debug("Modifying %r", path)
        src = src.replace(MKDOCS_TOC_PRE, MKDOCS_TOC_AFTER)
    if path.endswith("/material/templates/partials/nav-item.html"):
        logger.debug("Modifying %r", path)
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
        logger.debug("Modifying %r", path)
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
