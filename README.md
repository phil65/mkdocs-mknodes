# MkNodes (MkDocs plugin)

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

**mkdocs-mknodes** is a [MkDocs](https://www.mkdocs.org) plugin that builds your documentation
site from a Python node tree created with [MkNodes](https://github.com/phil65/mknodes).
Pages, navigation, API docs, changelogs, dependency tables, diagrams and more are generated
from your project's metadata and code, and you can still mix in hand-written Markdown and
Jinja templates wherever you like.

## Installation

```bash
pip install mkdocs-mknodes
```

## Quickstart

### 1. Zero configuration: the default website

Add the plugin to `mkdocs.yml` without any options:

```yaml
site_name: My project
theme:
  name: material
plugins:
  - mknodes
```

Then build:

```bash
mkdocs-mknodes build   # or: mkdocs build / mkdocs serve
```

Without a `build_fn` or `pages` setting, MkNodes builds a complete default website for the
project in the current Git repository:

- **Home**: your `README.md` (falls back to `.github/README.md`, then the package description)
- **API**: API reference for your package, generated recursively
- **CLI**: CLI documentation, if your project defines a command line interface
- **Development**: changelog (from Git commits), contribution guidelines, dev environment setup,
  dependency table and tree, MkDocs plugin flow (for MkDocs plugins) and license

### 2. Custom website: your own build function

Point `build_fn` to any callable (`module:function`, `module:Class.classmethod` or
`path/to/file.py:function`). It receives the root `MkNav` and the theme and fills the tree:

```python
# build_docs.py (next to mkdocs.yml)
import mknodes as mk


def build(root: mk.MkNav, theme: mk.Theme) -> None:
    page = root.add_page("Home", is_index=True)
    page += mk.MkAdmonition("Hello, world!")
    page += mk.MkCode.for_object(build)  # show the code that created this page
    root.add_doc(section_name="API", recursive=True)
```

```yaml
plugins:
  - mknodes:
      build_fn: build_docs.py:build
```

Build functions may also be `async`. Extra keyword arguments can be passed via the `kwargs`
setting.

### 3. Custom website from YAML

The default build function also accepts a node tree written in YAML:

```yaml
plugins:
  - mknodes:
      kwargs:
        pages:
          - title: Home
            type: MkText
            text: "{{ metadata.description }}"
            is_index: true
          - title: API
            type: MkDoc
            section_name: API
            recursive: true
          - Development:
              - title: Changelog
                type: MkChangelog
              - title: License
                type: MkLicense
```

## Features

- Hooks into the regular MkDocs build: pages, navigation, CSS/JS resources and required Markdown
  extensions are collected from the node tree and added to the MkDocs config automatically.
- Project metadata (pyproject, Git, installed distribution, ...) is available to all nodes and to
  the built-in Jinja environment (powered by [JinjaRope](https://github.com/phil65/jinjarope)).
- Pages can be Jinja templates; links between pages are resolved automatically.
- Edit-page links point to the code that generated a page; `show_page_info: true` appends
  build information (metadata, resources, generating code) to every page.
- Optional rewriting of MkDocs-Material templates for extra features (iconify icons,
  per-page `navigation.indexes` / `navigation.expand`).
- Build documentation for remote repositories (`repo_path` can be a Git URL).
- A CLI (`mkdocs-mknodes build | serve | create-config`) closely aligned with the MkDocs CLI,
  with rich logging output.

## CLI

```bash
# build the site for the current repository using mkdocs.yml
mkdocs-mknodes build

# build docs for a remote repository with a different config and output dir
mkdocs-mknodes build -r https://github.com/mkdocs/mkdocs.git -p configs/mkdocs_mkdocs.yml -d site/mkdocs

# live preview
mkdocs-mknodes serve

# print a MkDocs config inferred from a build function and the project metadata
mkdocs-mknodes create-config
```

Run `mkdocs-mknodes <command> --help` for all options.

## Plugin options

The most important settings (see the [docs](https://phil65.github.io/mkdocs-mknodes/) for all):

| Option | Default | Description |
| --- | --- | --- |
| `build_fn` | `mkdocs_mknodes:parse` | Callable that builds the node tree |
| `kwargs` | | Keyword arguments for the build function (e.g. `pages`) |
| `repo_path` | `.` | Local path or Git URL of the repository to document |
| `clone_depth` | `100` | Clone depth for remote repositories |
| `show_page_info` | `false` | Append build information to every page |
| `global_resources` | `true` | Put CSS/JS into all pages instead of only the pages that need them |
| `render_by_default` | `true` | Render all pages with Jinja |
| `build_folder` | temporary dir | Where generated Markdown files are written |

## License

MIT
