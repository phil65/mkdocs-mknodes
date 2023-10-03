from __future__ import annotations

import mknodes as mk

from mkdocs_mknodes.manual import timeline_data


nav = mk.MkNav("Getting started")
router = mk.Router()


@router.route_page("MkNodes plugin for MkDocs", hide="toc", is_homepage=True)
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("index.jinja")


@router.route_page("What is MkNodes?")
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("why_should_i_use_mknodes.jinja")


@router.route_page("Plugin configuration", hide="toc")
def _(page: mk.MkPage):
    eps = page.ctx.metadata.entry_points.get("mkdocs.plugins", [])
    page += mk.MkDocStrings(
        eps[0].obj.config_class,
        show_root_toc_entry=False,
        show_if_no_docstring=True,
        heading_level=4,
        show_bases=False,
        show_source=False,
    )


@router.route_page("The build process", hide="toc")
def _(page: mk.MkPage):
    page += timeline_data.INTRO
    node = mk.MkTimeline()
    for step in timeline_data.STEPS:
        node.add_item(date=step["step"], content=step["content"])
    page += node
