from __future__ import annotations

import tomllib

import mknodes as mk

from mkdocs_mknodes import paths


nav = mk.MkNav("Getting started")
router = mk.Router()

INTRO = (
    "This section provides an overview about the sequence of operations applied by"
    " **MkNodes** when running the full build process."
)


@router.route_page("MkNodes plugin for MkDocs", hide="toc", is_homepage=True)
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("index.jinja")


@router.route_page("What is MkNodes?")
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("why_should_i_use_mknodes.jinja")


@router.route_page("Plugin configuration", hide="toc")
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("plugin_configuration.jinja")
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
    text = (paths.RESOURCES / "timeline_data.toml").read_text()
    data = tomllib.loads(text)
    page += INTRO
    node = mk.MkTimeline()
    for step in data.values():
        node.add_item(date=step["label"], content=step["content"])
    page += node
