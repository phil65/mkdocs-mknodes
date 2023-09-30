from __future__ import annotations

import dataclasses
import datetime

from typing import Any

from mknodes.basenodes import mktext
from mknodes.info import yamlfile
from mknodes.navs import mknav
from mknodes.pages import metadata, mkpage
from mknodes.utils import requirements


@dataclasses.dataclass(frozen=True)
class Author:
    """A blog post author."""

    name: str
    description: str | None = None
    avatar: str | None = None


class BlogMetadata(metadata.Metadata):
    """Extended Metadata class for blog posts."""

    @property
    def date(self) -> str | None:
        return self.get("date")

    @date.setter
    def date(self, val: str | None):
        self["date"] = val

    @property
    def draft(self) -> bool | None:
        return self.get("draft")

    @draft.setter
    def draft(self, val: bool | None):
        self["draft"] = val

    @property
    def categories(self) -> list[str] | None:
        return self.get("categories")

    @categories.setter
    def categories(self, val: list[str] | None):
        self["categories"] = val

    @property
    def authors(self) -> list[str] | None:
        return self.get("authors")

    @authors.setter
    def authors(self, val: list[str] | None):
        self["authors"] = val


class MkBlog(mknav.MkNav):
    """Class representing the blog provided by the MkDocs-Material blog plugin."""

    def __init__(self, section: str | None = "Blog", **kwargs: Any):
        super().__init__(section=section, **kwargs)
        self.authors: dict[str, Author] = {}
        # self.posts = mknav.MkNav("posts", parent=self)
        # self.index_page = mkpage.MkPage()

    def add_author(
        self,
        username: str,
        name: str,
        description: str | None = None,
        avatar: str | None = None,
    ):
        """Add an author to the blog.

        Authors get linked to the blog post authors to show extended information.

        Arguments:
            username: Username / slug of the author
            name: Full name of the author
            description: Short description of the author
            avatar: Url to an image used as avatar
        """
        author = Author(name=name, description=description, avatar=avatar)
        self.authors[username] = author

    def get_node_requirements(self):
        authors_file = yamlfile.YamlFile()
        dct = {k: dataclasses.asdict(v) for k, v in self.authors.items()}
        authors_file._data["authors"] = dct
        content = authors_file.serialize("yaml")
        return requirements.Requirements(
            assets=[
                requirements.Asset("blog/.authors.yml", content, target="docs_dir"),
            ],
        )

    def add_post(
        self,
        text: str,
        date: datetime.datetime | str,
        more_text: str | None = None,
        *,
        categories: list[str] | str | None = None,
        authors: list[str] | str | None = None,
        draft: bool = False,
        **kwargs: Any,
    ):
        """Add a post to the blog.

        Arguments:
            text: Blog post text
            date: Time/Date of the post
            more_text: Text hidden behint the more button.
            categories: A list of categories this post is linked to
            authors: A list of authors of the post
            draft: Whether post is a draft
            kwargs: Keyword arguments passed to parent
        """
        page = MkBlogPost(
            date=date,
            draft=draft,
            categories=categories,
            authors=authors,
            **kwargs,
        )
        page += mktext.MkText(text)
        if more_text:
            page += "\n\n<!-- more -->\n\n"
            page += more_text
        self += page


class MkBlogPost(mkpage.MkPage):
    """Class representing a MkDocs-Material blog post."""

    DATE_FORMAT = "%Y-%m-%d"

    def __init__(
        self,
        date: str | datetime.datetime,
        *,
        draft: bool = True,
        categories: list[str] | str | None = None,
        authors: list[str] | str | None = None,
        **kwargs: Any,
    ):
        """Constructor.

        Arguments:
            date: Time/Date of the post
            draft: Whether post is a draft
            categories: A list of categories this post is linked to
            authors: A list of authors of the post
            kwargs: Keyword arguments passed to parent
        """
        super().__init__(**kwargs)
        if isinstance(authors, str):
            authors = [authors]
        if isinstance(categories, str):
            categories = [categories]
        self.metadata = BlogMetadata(
            **self.metadata,
            date=(
                date
                if isinstance(date, str)
                else datetime.datetime.strftime(date, self.DATE_FORMAT)
            ),
            draft=draft,
            categories=categories or [],
            authors=authors or [],
        )


if __name__ == "__main__":
    blog = MkBlog()
    blog.add_post("Hello", "2020-01-01", "more")
    page = blog.nav.pages[0]
    print(page.metadata)
    print(blog)
