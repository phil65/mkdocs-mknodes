"""Module containing the BuildCollector class."""

from __future__ import annotations

import collections
import itertools
import pathlib
import pprint
from typing import TYPE_CHECKING

import logfire
import mknodes as mk
from mknodes.utils import log, resources

from mkdocs_mknodes import buildcontext


if TYPE_CHECKING:
    from mkdocs_mknodes.backends import buildbackend


logger = log.get_logger(__name__)


def add_page_info(page: mk.MkPage, req: resources.Resources):
    """Add a collapsed admonition box showing some page-related data.

    Args:
        page: Page which should get updated.
        req: Resources of the page (passed in to avoid having to collect them again)
    """
    adm = mk.MkAdmonition([], title="Page info", typ="theme", collapsible=True)

    if page.created_by:
        typ = "section" if page.is_index() else "page"
        code = mk.MkCode.for_object(page.created_by)
        title = f"Code for this {typ}"
        details = mk.MkAdmonition(code, title=title, collapsible=True, typ="quote")
        adm += details

    pretty = mk.MkCode(pprint.pformat(req))
    details = mk.MkAdmonition(pretty, title="Resources", collapsible=True, typ="quote")
    adm += details

    code = mk.MkCode(str(page.resolved_metadata), language="yaml")
    details = mk.MkAdmonition(code, title="Metadata", collapsible=True, typ="quote")
    adm += details

    page += adm


def update_page_template(page: mk.MkPage):
    """Set template filename, metadata reference and `extends` path for given page.

    Args:
        page: Page of the template
    """
    if page.template:
        node_path = pathlib.Path(page.resolved_file_path)
    elif any(i.page_template for i in page.parent_navs):
        nav = next(i for i in page.parent_navs if i.page_template)
        node_path = pathlib.Path(nav.resolved_file_path)
    else:
        node_path = None
    if node_path:
        html_path = node_path.with_suffix(".html").as_posix()
        logger.debug("Updated template for MkPage %r: %r", page.title, html_path)
        page.metadata.template = html_path
        if page.template:
            page.template.filename = html_path
            if extends := _get_extends_from_parent(page):
                page.template.extends = extends


def update_nav_template(nav: mk.MkNav):
    """Set template filename, metadata reference and `extends` path for given nav.

    Args:
        nav: Nav of the template
    """
    if nav.page_template:
        path = pathlib.Path(nav.resolved_file_path)
        html_path = path.with_suffix(".html").as_posix()
        logger.debug("Updated template for MkNav %r: %r", nav.title, html_path)
        nav.metadata.template = html_path
        nav.page_template.filename = html_path
        if extends := _get_extends_from_parent(nav):
            nav.page_template.extends = extends


async def process_resources(
    page: mk.MkPage, req: resources.Resources | None = None
) -> resources.Resources:
    """Add resources from page to its template and return the "filtered" resources.

    Args:
        page: Page to process resources for
        req: Pre-computed resources. If None, will call page.get_resources()
    """
    if req is None:
        req = await page.get_resources()
    js_reqs: list[resources.JSFile] = []
    prefix = "../" * (len(page.resolved_parts) + 1)
    for i in req.js:
        if isinstance(i, resources.JSText):
            js_file = resources.JSFile(
                link=f"{prefix}assets/{i.resolved_filename}",
                async_=i.async_,
                defer=i.defer,
                crossorigin=i.crossorigin,
                typ=i.typ,
                is_library=i.is_library,
            )
        else:
            js_file = i
        js_reqs.append(js_file)
    non_libs = [i for i in js_reqs if not i.is_library]
    libs = [i for i in js_reqs if i.is_library]
    assets = [i.get_asset() for i in req.js if isinstance(i, resources.JSText)]
    req.assets += assets
    req.js = []
    for lib in libs:
        msg = f"Adding {lib.link!r} lib to {page.resolved_file_path!r} template"
        logger.info(msg)
        if page.template:
            page.template.libs.add_script_file(lib)
    for lib in non_libs:
        msg = f"Adding {lib.link!r} script to {page.resolved_file_path!r} template"
        logger.info(msg)
        if page.template:
            page.template.scripts.add_script_file(lib)
    css_reqs: list[resources.CSSFile] = []
    for css_item in req.css:
        if isinstance(css_item, resources.CSSText):
            css_file = resources.CSSFile(link=f"{prefix}assets/{css_item.resolved_filename}")
        else:
            css_file = css_item
        css_reqs.append(css_file)
    assets = [i.get_asset() for i in req.css if isinstance(i, resources.CSSText)]
    req.assets += assets
    req.css = []
    for css_ in css_reqs:
        msg = f"Adding {css_.link!r} stylesheet to {page.resolved_file_path!r} template"
        logger.info(msg)
        if page.template:
            page.template.styles.add_stylesheet(css_)
    return req


def _get_extends_from_parent(node: mk.MkPage | mk.MkNav) -> str | None:
    """Check parent navs for a page template and return its path if one was found.

    Args:
        node: Node to get the `extends` path for
    """
    for nav in node.parent_navs:
        if nav.page_template:
            p = pathlib.Path(nav.resolved_file_path)
            return p.with_suffix(".html").as_posix()
    return None


class BuildCollector:
    """A class to assist in extracting build stuff from a Node tree + Theme."""

    def __init__(
        self,
        backends: list[buildbackend.BuildBackend],
        show_page_info: bool = False,
        global_resources: bool = True,
        render_by_default: bool = True,
    ):
        """Constructor.

        Args:
            backends: A list of backends which should be used for building
            show_page_info: Add a admonition box containing page build info to each page
            global_resources: If False, make page resources non-global by moving them
                              to the page template blocks
            render_by_default: Whether to resolve all MkPages with their environment
        """
        self.backends = backends
        self.show_page_info = show_page_info
        self.global_resources = global_resources
        self.render_by_default = render_by_default
        self.node_files: dict[str, str | bytes] = {}
        self.extra_files: dict[str, str | bytes] = {}
        self.node_counter: collections.Counter[str] = collections.Counter()
        self.resources = resources.Resources()
        self.mapping: dict[str, mk.MkPage | mk.MkNav] = {}

    async def collect(self, root: mk.MkNode, theme: mk.Theme):
        """Collect build stuff from given node + theme.

        Args:
            root: A node to collect build stuff from
            theme: A theme to collect build stuff from.
        """
        logger.debug("Collecting resources...")
        for _, node in itertools.chain(theme.iter_nodes(), root.iter_nodes()):
            self.node_counter.update([node.__class__.__name__])
            self.extra_files |= node.files
            match node:
                case mk.MkPage() as page:
                    await self.collect_and_render_page(page)
                case mk.MkNav() as nav:
                    await self.collect_and_render_nav(nav)
        # theme
        logger.debug("Collecting theme resources...")
        reqs = await theme.get_resources()
        self.resources.merge(reqs)
        logger.debug("Adapting collected extensions to theme...")
        theme.adapt_extensions(self.resources.markdown_extensions)
        # templates
        templates = [
            i.template if isinstance(i, mk.MkPage) else i.page_template
            for i in self.mapping.values()
        ]
        vals = theme.templates
        templates += list(vals)
        final_templates = [i for i in templates if i]
        build_files = self.node_files | self.extra_files
        for backend in self.backends:
            logger.info("%s: Writing data..", type(backend).__name__)
            await backend.collect(build_files, self.resources, final_templates)
        return buildcontext.BuildContext(
            page_mapping=self.mapping,
            resources=self.resources,
            node_counter=self.node_counter,
            build_files=build_files,
            templates=final_templates,
        )

    @logfire.instrument("collect_and_render_page: {page.title}")
    async def collect_and_render_page(self, page: mk.MkPage):
        """Collect and render page in single pass.

        Args:
            page: Page to process.
        """
        if page.resolved_metadata.inclusion_level is False:
            return
        path = page.resolved_file_path
        self.mapping[path] = page

        # Single-pass: get both markdown and resources together
        content = await page.get_content()

        # Apply page processors
        md = content.markdown
        for proc in page.get_processors():
            md = proc.run(md)

        # Handle resources
        if self.global_resources:
            req = content.resources
        else:
            req = await process_resources(page, content.resources)
        self.resources.merge(req)

        update_page_template(page)
        show_info = page.resolved_metadata.get("show_page_info")
        show_info = self.show_page_info if show_info is None else show_info
        if show_info:
            add_page_info(page, req)

        # Render with jinja if needed
        do_render = self.render_by_default
        if (render := page.metadata.get("render_macros")) is not None:
            do_render = render
        if do_render:
            md = await page.env.render_string_async(md)

        self.node_files[path] = md

    @logfire.instrument("collect_and_render_nav: {nav.title}")
    async def collect_and_render_nav(self, nav: mk.MkNav):
        """Collect and render nav in single pass.

        Args:
            nav: Nav to process.
        """
        logger.info("Processing section %r...", nav.title or "[ROOT]")
        path = nav.resolved_file_path
        self.mapping[path] = nav

        # Single-pass: get both markdown and resources together
        content = await nav.get_content()

        # Apply nav processors
        md = content.markdown
        for proc in nav.get_processors():
            md = proc.run(md)

        # Merge resources
        self.resources.merge(content.resources)
        update_nav_template(nav)

        # Store rendered markdown
        self.node_files[path] = md


if __name__ == "__main__":
    theme = mk.MaterialTheme()
    from mkdocs_mknodes.manual import root

    async def main():
        log.basic()
        build = root.Build()
        nav = mk.MkNav.with_context()
        build.on_root(nav)
        collector = BuildCollector([])
        ctx = await collector.collect(nav, mk.MaterialTheme())
        print(ctx)

    import asyncio

    asyncio.run(main())
