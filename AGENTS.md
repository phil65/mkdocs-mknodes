# AGENTS.md

## Overview

`mkdocs-mknodes` is the MkDocs plugin (entry point `mknodes` in `mkdocs.plugins`) and CLI
(`mkdocs-mknodes`) that turns an [MkNodes](https://github.com/phil65/mknodes) node tree into a
MkDocs website. A Python "build function" populates an `mk.MkNav` root; the plugin collects the
resulting pages, templates, CSS/JS and Markdown extensions and feeds them into the MkDocs build.
It is used by ~20 documentation sites: treat the plugin config, the build-function signature and
`MkDefaultWebsite` as public API (fixes only, no breaking changes).

Not copier-managed. Type checking uses **mypy** (not ty). Package lives at top level
(`mkdocs_mknodes/`, `module-root = ""`), not under `src/`. Python >= 3.13.

## Two modes

1. **Default site (no config)**: `plugins: [mknodes]` with no options. `build_fn` defaults to
   `mkdocs_mknodes:parse` (`mkdocs_mknodes/__init__.py`). Without `pages` it calls
   `populate_default_website()` (`mkdocs_mknodes/mkdefaultwebsite.py`): index page = README
   (`README.md`, `.github/README.md`, `readme.md`, else the package description), API docs
   (`add_doc(recursive=True)`), a CLI page if CLI info is found, and a "Development" nav
   (changelog, contributing, dev setup, dependencies, MkDocs plugin flow, license).
2. **Custom**: either `kwargs: {pages: [...]}` for `mkdocs_mknodes:parse` (YAML nav parsed by
   `mknodes.navs.navparser.parse_new_style_nav`, see `configs/mkdocs_mkdocs.yml`), or a custom
   `build_fn: module:callable` / `path/file.py:callable` / `module:Class.classmethod`.
   The callable is invoked as `build_fn(theme=..., root=..., **kwargs)` and may be async
   (awaited via `anyenv.run_sync`). It mutates `root`; the return value is ignored.
   This repo's own docs use `mkdocs_mknodes.manual.root:Build.build`.

## Architecture

- `plugin/__init__.py` `MkNodesPlugin` - the MkDocs hooks:
  - `on_config`: build folder (temp dir unless `build_folder`), `LinkProvider`, `mk.Theme`,
    git repo (`reporegistry.get_repo`, remote repos are cloned), `FolderInfo`, `ProjectContext`.
  - `on_files`: create `mk.MkNav` root, run build fn, update MkDocs config from context
    (`mkdocsconfig.Config.update_from_context`), run `BuildCollector` with `MkDocsBackend` +
    `MarkdownBackend`, merge generated nav into `config.nav`, return the new `Files`.
  - `on_nav`: fill `LinkReplacer` mapping. `on_env`: add jinjarope globals/filters, optionally
    wrap the theme loader with `jinjarope.RewriteLoader` (`plugin/rewriteloader.py`).
  - `on_pre_page`: edit URLs from node `_edit_path`. `on_page_markdown`: link replacement.
  - `on_post_build`: delete generated template overrides in `theme.custom_dir`.
- `plugin/pluginconfig.py` `PluginConfig` - plugin options (`build_fn`, `kwargs`, `repo_path`,
  `clone_depth`, `build_folder`, `show_page_info`, `global_resources`, `jinja_*`, ...).
  Docstrings there are rendered on the "Plugin configuration" docs page.
- `plugin/mknodesconfig.py` `MkNodesConfig` - `MkDocsConfig` subclass used by the CLI
  (`from_yaml`, plugin helper methods). `mkdocsconfig.py` `Config` - wrapper around a MkDocs config.
- `buildcollector.py` `BuildCollector.collect()` - walks the node tree, renders pages/navs,
  aggregates resources and templates, writes via backends; returns `buildcontext.BuildContext`.
- `backends/` - `buildbackend.BuildBackend` base, `mkdocsbackend` (writes into MkDocs `Files`,
  extra CSS/JS, md extensions, theme templates), `markdownbackend` (raw `.original` Markdown
  into `site/src`).
- `cli/__init__.py` - Typer app: `build`, `serve`, `create-config`. `commands/build_page.py`
  reimplements `mkdocs build` (with logfire spans), `commands/serve.py` + `liveserver.py`
  for serving, `builders/configbuilder.py` applies CLI overrides to the YAML config.
- `appconfig/` - pydantic models of a MkDocs config (used by `create-config`).
- `mkdefaultwebsite.py` - `MkDefaultWebsite` nav + `populate_default_website()`.
- `manual/` - this project's own docs (build fn `root.py:Build.build`, sections in
  `get_started_section.py`, `use_cases_section.py`, `cli_section.py`), templates in `docs/*.jinja`.
- `telemetry.py` - logfire setup (only sends if a token is present), prefixed plugin logger.
- `paths.py` - `RESOURCES`, `CFG_DEFAULT`, `DEFAULT_BUILD_FN`.

## Where to look

| Task | File |
| --- | --- |
| Plugin hook behavior | `mkdocs_mknodes/plugin/__init__.py` |
| Add/change a plugin option | `mkdocs_mknodes/plugin/pluginconfig.py` (+ `plugin/mknodesconfig.py` for the CLI) |
| Default website content | `mkdocs_mknodes/mkdefaultwebsite.py`, `mkdocs_mknodes/__init__.py:parse` |
| CLI commands/flags | `mkdocs_mknodes/cli/__init__.py`, `mkdocs_mknodes/commands/` |
| Resource/template collection | `mkdocs_mknodes/buildcollector.py`, `mkdocs_mknodes/backends/` |
| Theme template rewriting | `mkdocs_mknodes/plugin/rewriteloader.py` |
| Own documentation | `mkdocs_mknodes/manual/`, `docs/*.jinja`, `mkdocs.yml`, `mkdocs_mknodes/resources/timeline_data.toml` |
| Example sub-site (MkDocs docs) | `configs/mkdocs_mkdocs.yml` (inherits `configs/mkdocs_shared.yml`) |

## Commands

```bash
uv sync --all-extras                      # setup (default groups: dev, lint, docs)
uv run pytest                             # tests (tests/), coverage enabled via addopts
uv run ruff check . && uv run ruff format --check .
uv run mypy mkdocs_mknodes/               # type check (CI + pre-commit)
uv run mkdocs-mknodes build -v            # docs build (as in documentation.yml)
uv run mkdocs-mknodes build -d ../site/mkdocs -p configs/mkdocs_mkdocs.yml -v --clone-depth 100
uv build
```

`duties.py` wraps these (`duty test`, `duty lint`, `duty lint_check`, `duty build`,
`duty serve`, `duty docs_test_build`). CI (`.github/workflows/build.yml`) runs lint, mypy and
pytest on 3.13 and 3.14; releases are published from tags.

## Conventions

- Ruff (line length 100, preview format, google docstrings). `from __future__ import annotations`.
- Build-function contract: keyword args `root` and `theme`, plus plugin `kwargs`; sync or async.
- Commit messages: conventional commits (commitizen hook; types in `[tool.mknodes]`).
- Tests (`tests/`) build MkNodes contexts from this repo (`mk.MkNav.with_context(...)`), so they
  need the git checkout; CLI tests mock the actual build/serve.

## Pitfalls

- Pre-commit runs `uv run pytest` and `uv run mypy` on every commit.
- The docs build needs Graphviz (CI installs it) and network (remote inventories, the example
  sub-site clones `mkdocs/mkdocs`).
- MkNodes may write HTML template overrides into `theme.custom_dir` (must exist and be outside
  `docs/`); they are deleted after the build unless `auto_delete_generated_templates: false`.
- `README.md` is the PyPI description and GitHub front page; keep its examples working.
- `mknodes`, `jinjarope`, `upathtools`, `anyenv` are sibling projects by the same author;
  behavior changes often originate there.
