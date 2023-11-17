from __future__ import annotations

from typing import Any

import mknodes as mk


class MkDefaultWebsite(mk.MkNav):
    """Nav for showing a default website including API docs and environment infos."""

    def __init__(
        self,
        static_pages: dict[str, str | dict | list] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        page = self.add_page(is_index=True, hide="toc")
        page += mk.MkText(page.ctx.metadata.description)
        static_pages = static_pages or {}
        self.parse.json(static_pages)
        self.add_doc(section_name="API", recursive=True)
        self.page_template.announcement_bar = mk.MkMetadataBadges("websites")
        if self.ctx.metadata.cli:
            page = self.add_page("CLI", hide="nav")
            page += mk.MkCliDoc(show_subcommands=True)

        nav = self.add_nav("Development")

        page = nav.add_page("Changelog")
        page += mk.MkChangelog()

        page = nav.add_page("Code of conduct")
        page += mk.MkCodeOfConduct()

        page = nav.add_page("Contributing")
        page += mk.MkCommitConventions()
        page += mk.MkPullRequestGuidelines()

        page = nav.add_page("Setting up the environment")
        page += mk.MkDevEnvSetup()
        page += mk.MkDevTools(header="Tools")

        page = nav.add_page("Dependencies")
        page += mk.MkDependencyTable()
        page += mk.MkPipDepTree(direction="LR")

        if "mkdocs.plugins" in self.ctx.metadata.entry_points:
            page = nav.add_page("MkDocs Plugins")
            page += mk.MkPluginFlow()

        node = mk.MkLicense()
        page = nav.add_page("License", hide="toc")
        page += node
