"""Run a MkNodes build function and collect the result as a `BuildOutput`."""

from __future__ import annotations

from datetime import datetime
import inspect
import pathlib
import re
from typing import TYPE_CHECKING, Any
import urllib.parse

from anyenv import run_sync
import mknodes as mk
from mknodes.info import contexts, folderinfo, linkprovider, reporegistry
from mknodes.mdlib import mdconverter
from mknodes.utils import linkreplacer, log, resources

from mkdocs_mknodes import buildcollector
from mkdocs_mknodes.backends import buildbackend
from mkdocs_mknodes.generator import yamlconfig
from mkdocs_mknodes.generator.output import BuildOutput, NavItem, Script, SiteMetadata


if TYPE_CHECKING:
    from mkdocs_mknodes.generator.settings import GeneratorSettings


logger = log.get_logger(__name__)

ASSETS_DIR = "assets"


class OutputBackend(buildbackend.BuildBackend):
    """Build backend collecting everything into a `BuildOutput`."""

    def __init__(self, output: BuildOutput) -> None:
        self.output = output
        self._extensions: dict[str, dict[str, Any]] = {}

    def collect_extensions(self, extensions: dict[str, dict[str, Any]]) -> None:
        for name, cfg in extensions.items():
            self.output.markdown_extensions[name] = dict(cfg or {})

    def write_files(self, files: dict[str, str | bytes]) -> None:
        for path, content in files.items():
            posix = pathlib.PurePosixPath(pathlib.PurePath(path).as_posix())
            if posix.name == "SUMMARY.md":
                continue
            if posix.suffix == ".md" and isinstance(content, str):
                self.output.pages[str(posix)] = content
            else:
                self.output.assets[str(posix)] = content

    def write_assets(self, assets: list[resources.Asset]) -> None:
        for asset in assets:
            if asset.target_dir == "docs_dir":
                path = asset.filename
            else:
                path = f"{ASSETS_DIR}/{asset.filename}"
            self.output.assets[path] = asset.content

    def write_css(self, css: list[resources.CSSType]) -> None:
        for item in css:
            if isinstance(item, resources.CSSText):
                path = f"{ASSETS_DIR}/{item.resolved_filename}"
                self.output.assets[path] = item.content
                self._add_css(path)
            else:
                self._add_css(str(item))

    def _add_css(self, path: str) -> None:
        if path not in self.output.extra_css:
            self.output.extra_css.append(path)

    def write_js_links(self, js_links: list[resources.JSFile]) -> None:
        for file in js_links:
            self._add_js(Script(str(file), file.defer, file.async_, file.typ or None))

    def write_js_files(self, js_files: list[resources.JSText]) -> None:
        for file in js_files:
            path = f"{ASSETS_DIR}/{file.resolved_filename}"
            self.output.assets[path] = file.content
            self._add_js(Script(path, file.defer, file.async_, file.typ or None))

    def _add_js(self, script: Script) -> None:
        if all(s.path != script.path for s in self.output.extra_javascript):
            self.output.extra_javascript.append(script)

    async def write_templates(self, templates: list[mk.PageTemplate]) -> None:
        exts = self.output.markdown_extensions
        md = mdconverter.MdConverter(extensions=list(exts), extension_configs=exts)
        for template in templates:
            if not template.filename:
                continue
            if html := await template.build_html(md):
                self.output.templates[template.filename] = html


def nav_from_dict(dct: dict[str, Any]) -> list[NavItem]:
    """Convert a MkNodes nav dict (`MkNav.nav.to_nav_dict()`) into `NavItem`s."""
    items = []
    for title, value in dct.items():
        if isinstance(value, dict):
            items.append(NavItem(title=str(title), children=nav_from_dict(value)))
        else:
            target = str(value)
            if "://" not in target:
                target = pathlib.PurePath(target).as_posix()
            items.append(NavItem(title=str(title), target=target))
    return items


def get_metadata(ctx: contexts.ProjectContext) -> SiteMetadata:
    info = ctx.metadata
    return SiteMetadata(
        site_name=info.distribution_name,
        site_description=info.summary,
        site_author=info.author_name,
        repo_url=info.repository_url,
        copyright=f"Copyright © {datetime.now().year} {info.author_name}",
        social=list(info.social_info or []),
    )


def _page_url(path: str) -> str:
    """Return the directory-style URL of a page path (`a/b.md`, `a/b/index.md` -> `a/b/`)."""
    p = pathlib.PurePosixPath(path)
    stem = p.with_suffix("")
    if p.name in {"index.md", "README.md"}:
        return f"{stem.parent.as_posix()}/".removeprefix("./")
    return f"{stem.as_posix()}/"


def resolve_url_collisions(output: BuildOutput) -> None:
    """Rename pages that would end up at the same URL as another page.

    MkDocs silently lets one of the pages win (`a/b.md` vs `a/b/index.md`, e.g. a class page
    and a sub-module nav with the same name), other engines refuse to build.
    The non-index page gets renamed (`a/b-1.md`) and the nav gets updated.
    """
    owners: dict[str, str] = {}
    renames: dict[str, str] = {}
    pages = sorted(output.pages, key=lambda p: not p.endswith(("index.md", "README.md")))
    for path in pages:
        url = _page_url(path)
        if url not in owners:
            owners[url] = path
            continue
        stem = pathlib.PurePosixPath(path).with_suffix("")
        i = 1
        while _page_url(new := f"{stem}-{i}.md") in owners:
            i += 1
        logger.warning("Page %s collides with %s, renaming to %s", path, owners[url], new)
        owners[_page_url(new)] = new
        renames[path] = new
    if not renames:
        return
    output.pages = {renames.get(k, k): v for k, v in output.pages.items()}
    output.edit_paths = {renames.get(k, k): v for k, v in output.edit_paths.items()}

    def rename(items: list[NavItem]) -> None:
        for item in items:
            if item.target in renames:
                item.target = renames[item.target]
            rename(item.children)

    rename(output.nav)


class SiteGenerator:
    """Runs the configured build function and returns an engine-neutral `BuildOutput`."""

    def __init__(self, settings: GeneratorSettings) -> None:
        self.settings = settings
        self.root: mk.MkNav | None = None
        self.theme: mk.Theme | None = None

    def create_theme(self) -> mk.Theme:
        theme_cfg = self.settings.theme_config
        name = theme_cfg.get("name") or "material"
        data = {k: v for k, v in theme_cfg.items() if not isinstance(v, yamlconfig.Tagged)}
        return mk.Theme.get_theme(theme_name=name, data=data)

    def create_context(self, theme: mk.Theme) -> contexts.ProjectContext:
        site_cfg = yamlconfig.resolve(self.settings.site_config)
        links = linkprovider.LinkProvider(
            base_url=site_cfg.get("site_url") or "",
            use_directory_urls=site_cfg.get("use_directory_urls", True),
            include_stdlib=True,
        )
        repo_path = self.settings.repo_path
        if repo_path == ".":
            repo_path = str(self.settings.project_dir)
        git_repo = reporegistry.get_repo(repo_path, clone_depth=self.settings.clone_depth)
        info = folderinfo.FolderInfo(git_repo.working_dir)
        self._links = links
        return contexts.ProjectContext(
            metadata=info.context,
            git=info.git.context,
            theme=theme.context,
            links=links,
            env_config=self.settings.get_jinja_config(),
        )

    def generate(self) -> BuildOutput:
        """Run the build function and collect pages, nav and resources.

        Like the MkDocs plugin, setup and the build function run synchronously (nodes may
        do blocking I/O on creation), only the collection step runs in an event loop.
        """
        theme = self.create_theme()
        ctx = self.create_context(theme)
        root = mk.MkNav(context=ctx)
        self.root, self.theme = root, theme
        logger.info("Running build function %s...", self.settings.build_fn)
        result = self.settings.get_builder()(theme=theme, root=root)
        if inspect.iscoroutine(result):
            run_sync(result)
        paths = [
            pathlib.Path(node.resolved_file_path).stem
            for _level, node in root.iter_nodes()
            if isinstance(node, mk.MkPage | mk.MkNav)
        ]
        self._links.set_excludes(paths)

        output = BuildOutput(metadata=get_metadata(root.ctx))
        backend = OutputBackend(output)
        collector = buildcollector.BuildCollector(
            backends=[backend],
            show_page_info=self.settings.show_page_info,
            global_resources=self.settings.global_resources,
            render_by_default=self.settings.render_by_default,
        )
        build_ctx = run_sync(collector.collect(root, theme))
        output.nav = nav_from_dict(root.nav.to_nav_dict())
        theme.adapt_extras(output.extra)
        for path, node in build_ctx.page_mapping.items():
            if isinstance(node, mk.MkPage) and node._edit_path:
                output.edit_paths[pathlib.PurePath(path).as_posix()] = node._edit_path
        resolve_url_collisions(output)
        self.replace_links(output)
        return output

    def replace_links(self, output: BuildOutput) -> None:
        """Point bare `[title](file.md)` links in generated pages to the actual page path."""
        replacer = linkreplacer.LinkReplacer()
        docs_dir = self.settings.resolved_docs_dir
        existing = [p.relative_to(docs_dir).as_posix() for p in _iter_files(docs_dir)]
        for path in [*existing, *output.files]:
            name = pathlib.PurePosixPath(path).name
            url = urllib.parse.unquote(path)
            if url not in replacer.mapping[name]:
                replacer.mapping[name].append(url)
        for path, md in output.pages.items():
            if re.search(linkreplacer.AUTOLINK_RE, md):
                output.pages[path] = replacer.replace(md, path)


def _iter_files(folder: pathlib.Path):
    if not folder.is_dir():
        return
    for p in folder.rglob("*"):
        if p.is_file() and not any(part.startswith(".") for part in p.parts[-1:]):
            yield p
