# MkDocs-MkNodes

#### Don't write docs. Code them.

[![PyPI License](https://img.shields.io/pypi/l/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Package status](https://img.shields.io/pypi/status/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Daily downloads](https://img.shields.io/pypi/dd/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Weekly downloads](https://img.shields.io/pypi/dw/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Monthly downloads](https://img.shields.io/pypi/dm/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Distribution format](https://img.shields.io/pypi/format/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Wheel availability](https://img.shields.io/pypi/wheel/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Python version](https://img.shields.io/pypi/pyversions/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Implementation](https://img.shields.io/pypi/implementation/mkdocs-mknodes.svg)](https://pypi.org/project/mkdocs-mknodes/)
[![Releases](https://img.shields.io/github/downloads/phil65/mkdocs-mknodes/total.svg)](https://github.com/phil65/mkdocs-mknodes/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes)
[![Github commits this week](https://img.shields.io/github/commit-activity/w/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes)
[![Github commits this year](https://img.shields.io/github/commit-activity/y/phil65/mkdocs-mknodes)](https://github.com/phil65/mkdocs-mknodes)
[![Package status](https://codecov.io/gh/phil65/mkdocs-mknodes/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/mkdocs-mknodes/)

[Read the documentation!](https://phil65.github.io/mkdocs-mknodes/)

**mkdocs-mknodes** builds your documentation site from a Python node tree created with
[MkNodes](https://github.com/phil65/mknodes). Pages, navigation, API docs, changelogs,
dependency tables, diagrams and more are generated from your project's metadata and code, and
you can still mix in hand-written Markdown and Jinja templates wherever you like.
The HTML site is built by [Zensical](https://zensical.org).

> **2.0:** The MkDocs plugin is gone. MkNodes generates the site input (pages, nav, assets,
> config) and Zensical builds it. Existing `mkdocs.yml` files keep working: the `mknodes`
> entry of the `plugins` list is still read for settings, but `[tool.mknodes]` in
> `pyproject.toml` is the preferred place now.

## Installation

```bash
pip install mkdocs-mknodes
```

## Quickstart

### 1. Zero configuration: the default website

```bash
mkdocs-mknodes build   # generate + zensical build
mkdocs-mknodes serve   # live preview on http://localhost:8000/
```

A `mkdocs.yml` is optional (theme, `site_name`, `markdown_extensions`, ...). Without a
`build-fn` or `pages` setting, MkNodes builds a complete default website for the project in the
current Git repository:

- **Home**: your `README.md` (falls back to `.github/README.md`, then the package description)
- **API**: API reference for your package, generated recursively
- **CLI**: CLI documentation, if your project defines a command line interface
- **Development**: changelog (from Git commits), contribution guidelines, dev environment setup,
  dependency table and tree and license

### 2. Custom website: your own build function

Point `build-fn` to any callable (`module:function`, `module:Class.classmethod` or
`path/to/file.py:function`). It receives the root `MkNav` and the theme and fills the tree:

```python
# build_docs.py (in the project root)
import mknodes as mk


def build(root: mk.MkNav, theme: mk.Theme) -> None:
    page = root.add_page("Home", is_index=True)
    page += mk.MkAdmonition("Hello, world!")
    page += mk.MkCode.for_object(build)  # show the code that created this page
    root.add_doc(section_name="API", recursive=True)
```

```toml
# pyproject.toml
[tool.mknodes]
build-fn = "build_docs.py:build"
```

Build functions may also be `async`. Extra keyword arguments can be passed via the `kwargs`
setting.

### 3. Custom website from config

The default build function also accepts a node tree via the `pages` setting:

```toml
[[tool.mknodes.pages]]
title = "Home"
type = "MkText"
text = "{{ metadata.description }}"
is_index = true

[[tool.mknodes.pages]]
title = "API"
type = "MkDoc"
section_name = "API"
recursive = true

[[tool.mknodes.pages]]
Development = [
  { title = "Changelog", type = "MkChangelog" },
  { title = "License", type = "MkLicense" },
]
```

## How it works

`mkdocs-mknodes generate` runs the build function and writes

- the generated pages and assets into the docs folder (listed in a generated `docs/.gitignore`;
  hand-written pages are never overwritten and keep working next to the generated ones),
- HTML template overrides (announcement bars, per-page resources, error page, ...) into the
  theme `custom_dir` (default `overrides/`),
- `mkdocs.generated.yml`, which `INHERIT`s `mkdocs.yml` and adds the nav, the required Markdown
  extensions and extra CSS / JS.

`mkdocs-mknodes build` then runs `zensical build -f mkdocs.generated.yml`; `serve` runs
`generate --watch` next to `zensical serve`.

## Features

- Project metadata (pyproject, Git, installed distribution, ...) is available to all nodes and to
  the built-in Jinja environment (powered by [JinjaRope](https://github.com/phil65/jinjarope)).
- Pages can be Jinja templates; bare links between generated pages are resolved automatically.
- Edit-page links point to the code that generated a page; `show-page-info = true` appends
  build information (metadata, resources, generating code) to every page.
- Build documentation for remote repositories (`--repo-url` can be a Git URL).

## CLI

```bash
mkdocs-mknodes generate [--watch]       # only write the site input
mkdocs-mknodes build [-d site] [-s]     # generate + zensical build (strict mode with -s)
mkdocs-mknodes serve                    # generate --watch + zensical serve
mkdocs-mknodes build -r https://github.com/owner/repo.git   # docs for a remote repository
```

`--engine zensical` / `-e zensical` is accepted for compatibility (Zensical is the only engine).
Run `mkdocs-mknodes <command> --help` for all options.

## Settings

Read from `[tool.mknodes]` in `pyproject.toml` (preferred) and the `mknodes` entry of the
`plugins` list in `mkdocs.yml` (`pyproject.toml` wins, CLI options win over both).
The most important settings (see the [docs](https://phil65.github.io/mkdocs-mknodes/) for all):

| Setting | Default | Description |
| --- | --- | --- |
| `build-fn` | `mkdocs_mknodes:parse` | Callable that builds the node tree |
| `kwargs` | | Keyword arguments for the build function |
| `pages` | | Node tree for the default build function |
| `repo-path` | `.` | Local path or Git URL of the repository to document |
| `clone-depth` | `100` | Clone depth for remote repositories |
| `show-page-info` | `false` | Append build information to every page |
| `global-resources` | `true` | Put CSS/JS into all pages instead of only the pages that need them |
| `render-by-default` | `true` | Render generated pages with Jinja |
| `generated-dir` | docs dir | Where generated pages are written |

## Migrating from 1.x

- Build with `mkdocs-mknodes build` (`--engine zensical` still works), not `mkdocs build`.
- `mkdocs` is no longer a dependency; add `zensical` (pulled in by mkdocs-mknodes) and keep
  `mkdocstrings[python]` in your docs dependencies for API pages.
- Removed: the MkDocs plugin (`mkdocs.plugins` entry point), `create-config`, the `--theme` and
  `--use-directory-urls` options, the Jinja rendering of hand-written pages, the link replacer
  for hand-written pages and the MkDocs template rewriting. The plugin options `build_folder`,
  `rewrite_theme_templates`, `auto_delete_generated_templates`, `jinja_on_undefined` and
  `llm_*` are ignored.

## License

MIT
