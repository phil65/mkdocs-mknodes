# AGENTS.md

## Overview

`mkdocs-mknodes` is the site generator (CLI `mkdocs-mknodes`) that turns an
[MkNodes](https://github.com/phil65/mknodes) node tree into a website. A Python "build function"
populates an `mk.MkNav` root; the generator collects pages, nav, assets, template overrides and
the required Markdown extensions into an engine-neutral `BuildOutput`, a writer turns that into
site-engine input and [Zensical](https://zensical.org) builds the HTML (or the `markdown`
writer emits plain GitHub-flavoured Markdown). Since 2.0 there is no
MkDocs plugin anymore and `mkdocs` is not a dependency (the package name stays).
It is used by ~30 documentation sites: treat the settings, the build-function signature, the
CLI (`build`/`serve`/`generate`, `--engine zensical|markdown`, `--flavor`) and
`MkDefaultWebsite` as public API.

Not copier-managed. Type checking uses **mypy** (not ty). Package lives at top level
(`mkdocs_mknodes/`, `module-root = ""`), not under `src/`. Python >= 3.13.

## Two modes

1. **Default site (no config)**: `build_fn` defaults to `mkdocs_mknodes:parse`
   (`mkdocs_mknodes/__init__.py`). Without `pages` it calls `populate_default_website()`
   (`mkdocs_mknodes/mkdefaultwebsite.py`): index page = README (`README.md`,
   `.github/README.md`, `readme.md`, else the package description), API docs
   (`add_doc(recursive=True)`), a CLI page if CLI info is found, and a "Development" nav
   (changelog, contributing, dev setup, dependencies, license).
2. **Custom**: either `pages = [...]` for `mkdocs_mknodes:parse` (nav parsed by
   `mknodes.navs.navparser.parse_new_style_nav`, example in `resources/pages_example.toml`), or a
   custom `build_fn: module:callable` / `path/file.py:callable` / `module:Class.classmethod`.
   The callable is invoked as `build_fn(theme=..., root=..., **kwargs)` and may be async
   (awaited via `anyenv.run_sync`). It mutates `root`; the return value is ignored.
   This repo's own docs use `mkdocs_mknodes.manual.root:Build.build` (set in `[tool.mknodes]`).

Settings (`generator/settings.py` `GeneratorSettings`) are read from the `mknodes` entry of the
`plugins` list in `mkdocs.yml` (existing sites have `- mknodes` there; zensical ignores it),
then `[tool.mknodes]` in `pyproject.toml` (preferred, `-`/`_` interchangeable), then CLI options.
Unknown keys are ignored (old plugin options like `build_folder` don't error).

## Architecture

- `generator/generator.py` `SiteGenerator.generate()`: theme (`mk.Theme.get_theme` from the
  `theme` section), git repo (`reporegistry.get_repo`, remote repos are cloned), `FolderInfo`,
  `ProjectContext`, runs the build fn, then mknodes' `DocBuilder(flavor=...).build(root, theme)`
  (renders pages, page templates, page info, resources -> assets / CSS / JS, nav tree; see
  `mknodes/build/`). Afterwards renames URL collisions (`resolve_url_collisions`, `-1` suffix
  with a warning; only a safety net for hand-built navs) and resolves bare `[x](file.md)` links
  (`replace_links`, needs the hand-written files of docs_dir).
- `BuildOutput`, `NavItem`, `Script`, `SiteMetadata` live in `mknodes.build` (re-exported from
  `mkdocs_mknodes.generator`). Keep engine-specific things out of them.
- `generator/yamlconfig.py`: YAML round-trip keeping `!ENV` / `!!python/name` tags, `INHERIT`.
- `generator/watch.py`: polling watcher for `generate --watch` / `serve`.
- Flavours: every writer has a `flavor` (`material` for zensical, `github` for markdown),
  overridable with the `flavor` setting / `--flavor`; passed to `DocBuilder`.
- `writers/markdown.py` `MarkdownWriter` (engine `markdown`): mknodes' `MarkdownExporter` files
  (pages, assets, nav as `SUMMARY.md`) written via `GeneratedFolder`; `build_command()` returns None (no build step, `serve` refuses).
- `writers/zensical.py` `ZensicalWriter`: writes pages/assets into docs_dir (manifest
  `docs/.gitignore` via `writers/base.py` `GeneratedFolder`; hand-written files are never
  overwritten), templates + downloaded Iconify SVGs into the theme `custom_dir`, and
  `mkdocs.generated.yml` (`INHERIT: mkdocs.yml` + nav, merged `markdown_extensions`, extra CSS/JS,
  `extra`). `build_command()` -> `python -m zensical build|serve -f mkdocs.generated.yml`.
- `cli/__init__.py` - Typer app: `build`, `serve`, `generate`. `cli/richstate.py` routes the
  `mknodes` / `mkdocs_mknodes` loggers through rich.
- `mkdefaultwebsite.py` - `MkDefaultWebsite` nav + `populate_default_website()`.
- `manual/` - this project's own docs (build fn `root.py:Build.build`, sections in
  `get_started_section.py`, `use_cases_section.py`, `cli_section.py`), templates in `docs/*.jinja`.
- `telemetry.py` - logfire setup (only sends if a token is present).
- `paths.py` - `RESOURCES`, `CFG_DEFAULT`, `DEFAULT_BUILD_FN`.

## Where to look

| Task | File |
| --- | --- |
| Add/change a setting | `mkdocs_mknodes/generator/settings.py` (docstrings are shown on the "Configuration" docs page) |
| Default website content | `mkdocs_mknodes/mkdefaultwebsite.py`, `mkdocs_mknodes/__init__.py:parse` |
| CLI commands/flags | `mkdocs_mknodes/cli/__init__.py` |
| Page rendering / resource + template collection | mknodes `src/mknodes/build/`, `mkdocs_mknodes/generator/generator.py` |
| Generated config / files on disk | `mkdocs_mknodes/writers/zensical.py`, `writers/base.py` |
| Own documentation | `mkdocs_mknodes/manual/`, `docs/*.jinja`, `mkdocs.yml`, `[tool.mknodes]`, `mkdocs_mknodes/resources/` |

## Commands

```bash
uv sync --all-extras                      # setup (default groups: dev, lint, docs)
uv run pytest                             # tests (tests/), coverage enabled via addopts
uv run ruff check . && uv run ruff format --check .
uv run mypy mkdocs_mknodes/               # type check (CI + pre-commit)
uv run mkdocs-mknodes build -v            # docs build (as in documentation.yml)
uv build
```

`duties.py` wraps these (`duty test`, `duty lint`, `duty lint_check`, `duty build`,
`duty serve`, `duty docs_test_build`). CI (`.github/workflows/build.yml`) runs lint, mypy and
pytest on 3.13 and 3.14; releases are published from tags.

## Conventions

- Ruff (line length 100, preview format, google docstrings). `from __future__ import annotations`.
- Build-function contract: keyword args `root` and `theme`, plus `kwargs`; sync or async.
- Commit messages: conventional commits (commitizen hook; types in `[tool.mknodes]`).
- Tests (`tests/`) generate sites from fixture projects whose `repo_path` points at this
  checkout, so they need the git checkout; CLI tests mock the generation / zensical call.

## Pitfalls

- Pre-commit runs `uv run pytest` and `uv run mypy` on every commit.
- The docs build needs Graphviz (CI installs it) and network (remote inventories, Iconify).
- `uv run` re-syncs mknodes from PyPI; to test against a local mknodes checkout use
  `uv pip install -e ../mknodes` and `uv run --no-sync ...` (or `.venv/bin/...`).
- Generated files: `docs/.gitignore` / `overrides/.gitignore` are manifests written by the
  generator; `mkdocs.generated.yml` is regenerated on every run.
- `README.md` is the PyPI description and GitHub front page; keep its examples working.
- `mknodes`, `jinjarope`, `upathtools`, `anyenv` are sibling projects by the same author;
  behavior changes often originate there.
