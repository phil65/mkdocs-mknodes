from __future__ import annotations

from typing import Any

import mknodes as mk


README_NAMES = ("README.md", ".github/README.md", "readme.md")


def add_index_page(nav: mk.MkNav) -> mk.MkPage:
    """Add an index page showing the repository README (or the package description)."""
    page = nav.add_page(is_index=True, hide="toc")
    repo_path = nav.ctx.metadata.repository_path
    readme = next((p for name in README_NAMES if (p := repo_path / name).is_file()), None)
    if readme is not None:
        page += mk.MkInclude(readme)
    else:
        page += mk.MkText(nav.ctx.metadata.description)
    return page


def populate_default_website(
    nav: mk.MkNav,
    static_pages: dict[str, str | dict | list] | None = None,
) -> mk.MkNav:
    """Fill given nav with a default website: README, API docs, CLI and dev infos."""
    add_index_page(nav)
    if static_pages:
        nav.parse.json(static_pages)
    nav.add_doc(section_name="API", recursive=True)
    nav.page_template.announcement_bar = mk.MkMetadataBadges("websites")
    if nav.ctx.metadata.cli or nav.ctx.metadata.cli_info:
        page = nav.add_page("CLI", hide="nav")
        page += mk.MkCliDoc(show_subcommands=True)

    dev_nav = nav.add_nav("Development")

    page = dev_nav.add_page("Changelog")
    page += mk.MkChangelog()

    page = dev_nav.add_page("Contributing")
    page += mk.MkCommitConventions()

    page = dev_nav.add_page("Setting up the environment")
    page += mk.MkDevEnvSetup()
    page += mk.MkDevTools(header="Tools")

    page = dev_nav.add_page("Dependencies")
    page += mk.MkDependencyTable()
    page += mk.MkPipDepTree(direction="LR")

    page = dev_nav.add_page("License", hide="toc")
    page += mk.MkLicense()
    return nav


class MkDefaultWebsite(mk.MkNav):
    """Nav for showing a default website including API docs and environment infos."""

    def __init__(
        self,
        static_pages: dict[str, str | dict | list] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        populate_default_website(self, static_pages)
