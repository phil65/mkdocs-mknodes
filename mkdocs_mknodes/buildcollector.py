"""Module containing the BuildCollector class."""

from __future__ import annotations

import collections
import itertools
import pathlib
import pprint

from typing import TYPE_CHECKING

import mknodes as mk

from mknodes.utils import log, resources

from mkdocs_mknodes import buildcontext


if TYPE_CHECKING:
    from mkdocs_mknodes.backends import buildbackend


logger = log.get_logger(__name__)


def add_page_info(page: mk.MkPage, req: resources.Resources):
    """Add a collapsed admonition box showing some page-related data.

    Arguments:
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

    Arguments:
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
        page.template.filename = html_path
        if extends := _get_extends_from_parent(page):
            page.template.extends = extends


def update_nav_template(nav: mk.MkNav):
    """Set template filename, metadata reference and `extends` path for given nav.

    Arguments:
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


def process_resources(page: mk.MkPage) -> resources.Resources:
    """Add resources from page to its template and return the "filtered" resources."""
    req = page.get_resources()
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
        page.template.libs.add_script_file(lib)
    for lib in non_libs:
        msg = f"Adding {lib.link!r} script to {page.resolved_file_path!r} template"
        logger.info(msg)
        page.template.scripts.add_script_file(lib)
    css_reqs: list[resources.CSSFile] = []
    for i in req.css:
        if isinstance(i, resources.CSSText):
            css_file = resources.CSSFile(link=f"{prefix}assets/{i.resolved_filename}")
        else:
            css_file = i
        css_reqs.append(css_file)
    assets = [i.get_asset() for i in req.css if isinstance(i, resources.CSSText)]
    req.assets += assets
    req.css = []
    for css_ in css_reqs:
        msg = f"Adding {css_.link!r} stylesheet to {page.resolved_file_path!r} template"
        logger.info(msg)
        page.template.styles.add_stylesheet(css_)
    return req


def _get_extends_from_parent(node: mk.MkPage | mk.MkNav) -> str | None:
    """Check parent navs for a page template and return its path if one was found.

    Arguments:
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

        Arguments:
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

    def collect(self, root: mk.MkNode, theme: mk.Theme):
        """Collect build stuff from given node + theme.

        Arguments:
            root: A node to collect build stuff from
            theme: A theme to collect build stuff from.
        """
        logger.debug("Collecting resources...")
        for _, node in itertools.chain(theme.iter_nodes(), root.iter_nodes()):
            self.node_counter.update([node.__class__.__name__])
            self.extra_files |= node.files
            match node:
                case mk.MkPage() as page:
                    self.collect_page(page)
                case mk.MkNav() as nav:
                    self.collect_nav(nav)
        for node in self.mapping.values():
            match node:
                case mk.MkPage() as page:
                    self.render_page(page)
                case mk.MkNav() as nav:
                    self.render_nav(nav)
        # theme
        logger.debug("Collecting theme resources...")
        reqs = theme.get_resources()
        self.resources.merge(reqs)
        logger.debug("Adapting collected extensions to theme...")
        theme.adapt_extensions(self.resources.markdown_extensions)
        # templates
        templates = [
            i.template if isinstance(i, mk.MkPage) else i.page_template
            for i in self.mapping.values()
        ]
        if isinstance(theme.templates, dict):
            vals = theme.templates.values()
        else:
            vals = theme.templates
        templates += list(vals)
        templates = [i for i in templates if i]
        build_files = self.node_files | self.extra_files
        for backend in self.backends:
            logger.info("%s: Writing data..", type(backend).__name__)
            backend.collect(build_files, self.resources, templates)
        return buildcontext.BuildContext(
            page_mapping=self.mapping,
            resources=self.resources,
            node_counter=self.node_counter,
            build_files=build_files,
            templates=templates,
        )

    def collect_page(self, page: mk.MkPage):
        """Preprocess page and collect its data.

        Arguments:
            page: Page to collect the data from.
        """
        if page.resolved_metadata.inclusion_level is False:
            return
        path = page.resolved_file_path
        self.mapping[path] = page
        req = page.get_resources() if self.global_resources else process_resources(page)
        self.resources.merge(req)
        update_page_template(page)
        show_info = page.resolved_metadata.get("show_page_info")
        show_info = self.show_page_info if show_info is None else show_info
        if show_info:
            add_page_info(page, req)

    def render_page(self, page: mk.MkPage):
        """Convert a page to markdown/HTML.

        Arguments:
            page: Page to render.
        """
        md = page.to_markdown()
        do_render = self.render_by_default
        if (render := page.metadata.get("render_macros")) is not None:
            do_render = render
        if do_render:
            md = page.env.render_string(md)

        self.node_files[page.resolved_file_path] = md

    def collect_nav(self, nav: mk.MkNav):
        """Preprocess nav and collect its data.

        Arguments:
            nav: Nav to collect the data from.
        """
        logger.info("Processing section %r...", nav.title or "[ROOT]")
        path = nav.resolved_file_path
        self.mapping[path] = nav
        req = nav.get_node_resources()
        self.resources.merge(req)
        update_nav_template(nav)

    def render_nav(self, nav: mk.MkNav):
        """Convert a nav to markdown/HTML.

        Arguments:
            nav: Nav to render.
        """
        md = nav.to_markdown()
        self.node_files[nav.resolved_file_path] = md


if __name__ == "__main__":
    theme = mk.MaterialTheme()
    from mkdocs_mknodes.manual import root

    log.basic()
    build = root.Build()
    nav = mk.MkNav.with_context()
    build.on_root(nav)
    collector = BuildCollector([])
    ctx = collector.collect(nav, mk.MaterialTheme())
    print(ctx)
