from __future__ import annotations

import dataclasses
import pathlib

import pathspec


@dataclasses.dataclass
class MkNodesConfig:
    """The MkDocs-MkNodes configuration."""

    config_file_path: str
    """The path to the mkdocs.yml config file. Can't be populated from the config."""
    site_name: str
    """The title to use for the documentation."""
    nav: dict | None = None
    """Defines the structure of the navigation."""
    exclude_docs: pathspec.gitignore.GitIgnoreSpec | None = None
    """File patterns (relative to docs dir) to exclude from the site.

    Gitignore-like patterns of files
    """
    not_in_nav: pathspec.gitignore.GitIgnoreSpec | None = None
    """File patterns (relative to docs dir) that are not intended to be in the nav.

    Gitignore-like patterns of files.
    This marks doc files that are expected not to be in the nav, otherwise they will
    cause a log message
    (see also `validation.nav.omitted_files`).
    """
    site_url: str | None = None  # URL type
    """The full URL to where the documentation will be hosted."""
    site_description: str | None = None
    """A description for the documentation project that will be added to the
    HTML meta tags."""
    site_author: str | None = None
    """The name of the author to add to the HTML meta tags."""
    theme: dict | str | None = "mkdocs"  # Theme type
    """The MkDocs theme for the documentation."""
    docs_dir: pathlib.Path | str = "docs"
    """The directory containing the documentation markdown."""
    site_dir: pathlib.Path | str = "site"
    """The directory where the site will be built to"""
    copyright: str | None = None  # noqa: A003
    """A copyright notice to add to the footer of documentation."""
    dev_addr: str = "127.0.0.1:8000"
    """The address on which to serve the live reloading docs server."""
    use_directory_urls: bool = True
    """If `True`, use `<page_name>/index.html` style files with hyperlinks to
    the directory. If `False`, use `<page_name>.html style file with
    hyperlinks to the file.
    True generates nicer URLs, but False is useful if browsing the output on
    a filesystem."""
    repo_url: str | None = None
    """Specify a link to the project source repo for the documentation pages."""
    repo_name: str | None = None
    """A name to use for the link to the project source repo.
    Default, If repo_url is unset then None, otherwise
    "GitHub", "Bitbucket" or "GitLab" for known url or Hostname
    for unknown urls."""
    edit_uri_template: str | None = None
    edit_uri: str | None = None
    """Specify a URI to the docs dir in the project source repo, relative to the
    repo_url. When set, a link directly to the page in the source repo will
    be added to the generated HTML. If repo_url is not set also, this option
    is ignored."""
    extra_css: list = dataclasses.field(default_factory=list)
    extra_javascript: list[str | dict] = dataclasses.field(default_factory=list)
    """Specify which css or javascript files from the docs directory should be
    additionally included in the site."""
    extra_templates: list = dataclasses.field(default_factory=list)
    """Similar to the above, but each template (HTML or XML) will be build with
    Jinja2 and the global context."""
    markdown_extensions: list[str] = dataclasses.field(
        default_factory=lambda: ["toc", "tables", "fenced_code"],
    )
    """PyMarkdown extension names."""
    mdx_configs: dict[str, dict] = dataclasses.field(default_factory=dict)
    """PyMarkdown extension configs. Populated from `markdown_extensions`."""
    strict: bool = False
    """Enabling strict mode causes MkDocs to stop the build when a problem is
    encountered rather than display an error."""
    remote_branch: str = "gh-pages"
    """The remote branch to commit to when using gh-deploy."""
    remote_name: str = "origin"
    """The remote name to push to when using gh-deploy."""
    extra: dict = dataclasses.field(default_factory=dict)
    """extra is a mapping/dictionary of data that is passed to the template.
    This allows template authors to require extra configuration that not
    relevant to all themes and doesn't need to be explicitly supported by
    MkDocs itself. A good example here would be including the current
    project version."""
    plugins: list[str | dict] = dataclasses.field(default_factory=lambda: ["search"])
    """A list of plugins. Each item may contain a string name or a key value pair.
    A key value pair should be the string name (as the key) and a dict of config
    options (as the value)."""
    hooks: list[pathlib.Path] = dataclasses.field(default_factory=list)
    """A list of filenames that will be imported as Python modules and used as
    an instance of a plugin each."""
    watch: list[pathlib.Path] = dataclasses.field(default_factory=list)
    """A list of extra paths to watch while running `mkdocs serve`."""
    validation: dict = dataclasses.field(default_factory=dict)
