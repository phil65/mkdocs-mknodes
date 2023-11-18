"""MkNodes project."""

from __future__ import annotations

from collections.abc import Callable
import os

from typing import Generic, TypeVar

from mknodes import paths
from mknodes.info import contexts, folderinfo, linkprovider, reporegistry
from mknodes.navs import mknav
from mknodes.theme import theme as theme_
from mknodes.utils import classhelpers, log, reprhelpers


logger = log.get_logger(__name__)


T = TypeVar("T", bound=theme_.Theme)


class Project(Generic[T]):
    """MkNodes Project."""

    def __init__(
        self,
        theme: T,
        repo: str | os.PathLike | None | folderinfo.FolderInfo = None,
        build_fn: str | Callable = paths.DEFAULT_BUILD_FN,
        base_url: str = "",
        use_directory_urls: bool = True,
        clone_depth: int = 100,
        jinja_extensions: list[str] | None = None,
    ):
        """The main project to create a website.

        Arguments:
            theme: The theme to use
            repo: Path to the git repository
            build_fn: Callable to create the website with
            base_url: Base url of the website
            use_directory_urls: Whether urls are in directory-style
            clone_depth: Amount of commits to clone in case repository is remote.
            jinja_extensions: Optional additional jinja extensions to load.
        """
        self.linkprovider = linkprovider.LinkProvider(
            base_url=base_url,
            use_directory_urls=use_directory_urls,
            include_stdlib=True,
        )
        self.build_fn = classhelpers.to_callable(build_fn)
        self.theme: T = theme
        git_repo = reporegistry.get_repo(str(repo or "."), clone_depth=clone_depth)
        self.folderinfo = folderinfo.FolderInfo(git_repo.working_dir)
        self.context = contexts.ProjectContext(
            metadata=self.folderinfo.context,
            git=self.folderinfo.git.context,
            # github=self.folderinfo.github.context,
            theme=self.theme.context,
            links=self.linkprovider,
            env_config={},
        )
        self._root = mknav.MkNav(context=self.context)

    def __repr__(self):
        return reprhelpers.get_repr(self, repo_path=str(self.folderinfo.path))

    @property
    def root(self) -> mknav.MkNav:
        return self._root

    @root.setter
    def root(self, nav: mknav.MkNav):
        self._root = nav
        nav._ctx = self.context


if __name__ == "__main__":
    import mknodes as mk

    theme = mk.MaterialTheme()
    project = Project(theme=theme)
    log.basic()
