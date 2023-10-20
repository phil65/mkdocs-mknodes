"""Module containing the BuildCollector class."""

from __future__ import annotations

import collections
import itertools
import pathlib

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

    title = "Resources"
    pretty = mk.MkPrettyPrint(req)
    details = mk.MkAdmonition(pretty, title=title, collapsible=True, typ="quote")
    adm += details

    title = "Metadata"
    code = mk.MkCode(str(page.resolved_metadata), language="yaml")
    details = mk.MkAdmonition(code, title=title, collapsible=True, typ="quote")
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
        nav.metadata.template = html_path
        nav.page_template.filename = html_path
        if extends := _get_extends_from_parent(nav):
            nav.page_template.extends = extends


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
        render_all_pages: bool = True,
    ):
        """Constructor.

        Arguments:
            backends: A list of backends which should be used for building
            show_page_info: Add a admonition box containing page build info to each page
            render_all_pages: Whether to resolve all MkPages with their environment
        """
        self.backends = backends
        self.show_page_info = show_page_info
        self.render_all_pages = render_all_pages
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
        logger.debug("Collecting theme resources...")
        iterator = itertools.chain(theme.iter_nodes(), root.iter_nodes())
        for _, node in iterator:
            self.node_counter.update([node.__class__.__name__])
            self.extra_files |= node.files
            match node:
                case mk.MkPage() as page:
                    self.collect_page(page)
                case mk.MkNav() as nav:
                    self.collect_nav(nav)
        logger.debug("Setting default markdown extensions...")
        reqs = theme.get_resources()
        self.resources.merge(reqs)
        logger.debug("Adapting collected extensions to theme...")
        theme.adapt_extensions(self.resources.markdown_extensions)
        build_files = self.node_files | self.extra_files
        templates = [
            i.template if isinstance(i, mk.MkPage) else i.page_template
            for i in self.mapping.values()
        ]
        templates += theme.templates
        templates = [i for i in templates if i]
        for backend in self.backends:
            logger.info("%s: Collecting data..", type(backend).__name__)
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
        req = page.get_resources()

        # libs = [i for i in req.js_files if i.is_library]
        # req.remove(*libs)
        # for lib in libs:
        #     page.template.libs.add_script_file(lib)
        self.resources.merge(req)
        update_page_template(page)
        show_info = page.resolved_metadata.get("show_page_info")
        if show_info is None:
            show_info = self.show_page_info
        if show_info:
            add_page_info(page, req)
        md = page.to_markdown()
        render_all_pages = self.render_all_pages
        if (render := page.metadata.get("render_jinja")) is not None:
            render_all_pages = render
        if render_all_pages:
            md = page.env.render_string(md)

        self.node_files[path] = md

    def collect_nav(self, nav: mk.MkNav):
        """Preprocess nav and collect its data.

        Arguments:
            nav: Nav to collect the data from.
        """
        logger.info("Processing section %r...", nav.section)
        path = nav.resolved_file_path
        self.mapping[path] = nav
        req = nav.get_node_resources()
        self.resources.merge(req)
        update_nav_template(nav)
        md = nav.to_markdown()
        self.node_files[path] = md


if __name__ == "__main__":
    project = mk.Project.for_mknodes()
    from mkdocs_mknodes.manual import root

    log.basic()
    root.build(project)
    if project._root:
        collector = BuildCollector([])
        ctx = collector.collect(project._root, project.theme)
        print(ctx)
