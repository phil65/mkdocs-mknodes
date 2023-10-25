from __future__ import annotations

import os

from typing import TYPE_CHECKING

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure import files as files_, nav, pages

from mkdocs_mknodes import mkdocsconfig


if TYPE_CHECKING:
    import mknodes as mk

logger = get_plugin_logger(__name__)


class MkDocsPage(pages.Page):
    """MkPage-based Mkocs-Page subclass."""

    def __init__(self, mkpage: mk.MkPage, file: files_.File, config: MkDocsConfig):
        self.mkpage = mkpage
        super().__init__(title=self.mkpage.title, file=file, config=config)

    def read_source(self, config: MkDocsConfig):
        self.meta = self.mkpage.metadata
        self.mkpage.metadata = {}
        self.markdown = str(self.mkpage)
        self.mkpage.metadata = self.meta


class MkDocsBuilder:
    def __init__(
        self,
        config: mkdocsconfig.Config | MkDocsConfig | str | os.PathLike | None = None,
    ):
        """Constructor.

        Arguments:
            config: MkDocs Config
        """
        match config:
            case mkdocsconfig.Config():
                self._config = config._config
            case MkDocsConfig():
                self._config = config
            case _:
                self._config = mkdocsconfig.Config(config)._config
        self.mk_files = files_.Files([])

    def get_file(
        self,
        path: str | os.PathLike,
        src_dir: str | os.PathLike | None = None,
        dest_dir: str | os.PathLike | None = None,
        inclusion_level: files_.InclusionLevel = files_.InclusionLevel.UNDEFINED,
    ) -> files_.File:
        """Return a MkDocs File for given path.

        Arguments:
            path: path to get a File object for (relative to src_dir)
            src_dir: Source directory. If None, docs_dir is used.
            dest_dir: Target directory. If None, site_dir is used.
            inclusion_level: Inclusion level of new file
        """
        new_f = files_.File(
            os.fspath(path),
            src_dir=str(src_dir) if src_dir else self._config.docs_dir,
            dest_dir=str(dest_dir) if dest_dir else self._config.site_dir,
            use_directory_urls=self._config.use_directory_urls,
            inclusion=inclusion_level,
        )
        self.mk_files.append(new_f)
        new_f.generated_by = "mknodes"  # type: ignore
        return new_f

    def get_section_page(
        self,
        title: str,
        path: str | os.PathLike,
        children: list[pages.Page | nav.Section | nav.Link],
        inclusion_level: files_.InclusionLevel = files_.InclusionLevel.UNDEFINED,
    ) -> pages.Page:
        import mkdocs_section_index

        file = self.get_file(path, inclusion_level=inclusion_level)
        return mkdocs_section_index.SectionPage(
            title=title,
            file=file,
            config=self._config,
            children=children,
        )

    def get_page(
        self,
        mkpage,
        run_event_hooks: bool = False,
    ) -> pages.Page:
        file = self.get_file(
            mkpage.resolved_file_path,
            inclusion_level=files_.InclusionLevel.UNDEFINED,
        )
        page = MkDocsPage(mkpage, file, self._config)

        if run_event_hooks:
            self._config._current_page = page
            page = self._config.plugins.on_pre_page(
                page,
                config=self._config,
                files=self.mk_files,
            )
            page.read_source(self._config)
            page.markdown = self._config.plugins.on_page_markdown(
                page.markdown or "",
                page=page,
                config=self._config,
                files=self.mk_files,
            )
            page.render(self._config, self.mk_files)
            page.content = self._config.plugins.on_page_content(
                page.content or "",
                page=page,
                config=self._config,
                files=self.mk_files,
            )

            self._config._current_page = None

        return page

    def get_nav(self) -> nav.Navigation:
        return nav.get_navigation(self.mk_files, self._config)


if __name__ == "__main__":
    builder = MkDocsBuilder()
