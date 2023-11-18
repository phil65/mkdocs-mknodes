from __future__ import annotations

import collections
import os
import pathlib

import markdown

from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure import files as files_
from mknodes.utils import mergehelpers, pathhelpers, resources
import upath

from mkdocs_mknodes import mkdocsconfig
from mkdocs_mknodes.backends import buildbackend
from mkdocs_mknodes.plugin import mkdocsbuilder, mkdocshelpers


logger = get_plugin_logger(__name__)


class MkDocsBackend(buildbackend.BuildBackend):
    def __init__(
        self,
        files: files_.Files | None = None,
        config: mkdocsconfig.Config | MkDocsConfig | str | os.PathLike | None = None,
        directory: str | os.PathLike | None = None,
    ):
        """Constructor.

        Arguments:
            files: A Files collection to use for new files
            config: An MkDocs config
            directory: The build directory
        """
        match config:
            case mkdocsconfig.Config():
                self._config = config._config
            case MkDocsConfig():
                self._config = config
            case _:
                self._config = mkdocsconfig.Config(config)._config
        self.directory = upath.UPath(directory or ".")
        files_map = {pathlib.PurePath(f.src_path).as_posix(): f for f in files or []}
        self._mk_files: collections.ChainMap[str, files_.File] = collections.ChainMap(
            {},
            files_map,
        )
        self.builder = mkdocsbuilder.MkDocsBuilder(self._config)

    def _get_parser(self) -> markdown.Markdown:
        """Return a markdown instance based on given config."""
        return markdown.Markdown(
            extensions=self._config.markdown_extensions,
            extension_configs=self._config.mdx_configs,
        )

    @property
    def files(self) -> files_.Files:
        """Access the files as they currently are, as a MkDocs [Files][] collection.

        [Files]: https://github.com/mkdocs/mkdocs/blob/master/mkdocs/structure/files.py
        """
        files = sorted(self._mk_files.values(), key=mkdocshelpers.file_sorter)
        return files_.Files(files)

    def write_files(self, files):
        for k, v in files.items():
            if pathlib.Path(k).name == "SUMMARY.md":
                continue
            logger.debug("%s: Writing file to %r", type(self).__name__, str(k))
            self._write_file(k, v)

    def write_assets(self, assets):
        for asset in assets:
            if asset.target_dir == "docs_dir":
                abs_path = upath.UPath(self._config.docs_dir) / asset.filename
                logger.info("Writing asset %s...", abs_path)
                pathhelpers.write_file(asset.content, abs_path)
            else:
                path = (pathlib.Path("assets") / asset.filename).as_posix()
                abs_path = upath.UPath(self._config.site_dir) / path
                pathhelpers.write_file(asset.content, abs_path)

    def write_css(self, css_files):
        for css in css_files:
            if isinstance(css, resources.CSSText):
                path = (pathlib.Path("assets") / css.resolved_filename).as_posix()
                self._config.extra_css.append(path)
                abs_path = upath.UPath(self._config.site_dir) / path
                logger.info("Registering css file %s...", abs_path)
                pathhelpers.write_file(css.content, abs_path)
            else:
                logger.debug("Adding remote CSS file %s", css)
                self._config.extra_css.append(str(css))

    def write_js_links(self, js_links):
        for file in js_links:
            logger.debug("Adding remote JS file %s", str(file))
            val = config_options.ExtraScriptValue(str(file))
            val.async_ = file.async_
            val.defer = file.defer
            val.type = file.typ
            self._config.extra_javascript.append(val)

    def write_js_files(self, js_files):
        for file in js_files:
            path = (pathlib.Path("assets") / file.resolved_filename).as_posix()
            val = config_options.ExtraScriptValue(str(path))
            val.async_ = file.async_
            val.defer = file.defer
            val.type = file.typ
            self._config.extra_javascript.append(path)
            abs_path = upath.UPath(self._config.site_dir) / path
            logger.info("Registering js file %s...", abs_path)
            pathhelpers.write_file(file.content, abs_path)

    def collect_extensions(self, extensions):
        if extensions:
            for ext_name in extensions:
                if ext_name not in self._config.markdown_extensions:
                    logger.info("Adding %s to extensions", ext_name)
                    self._config.markdown_extensions.append(ext_name)
            self._config.mdx_configs = mergehelpers.merge_dicts(
                self._config.mdx_configs,
                extensions,
            )

    def write_templates(self, templates):
        if not self._config.theme.custom_dir:
            logger.warning("Cannot write template. No custom_dir set in config.")
            return
        path = upath.UPath(self._config.theme.custom_dir)
        for template in templates:
            md = self._get_parser()
            if html := template.build_html(md):
                target_path = path / template.filename
                logger.info("Creating %s...", target_path.as_posix())
                pathhelpers.write_file(html, target_path)

    def _write_file(self, path: str | os.PathLike, content: str | bytes):
        path = pathlib.PurePath(path).as_posix()
        file_for_path = self.builder.get_file(path, src_dir=self.directory)
        new_path = upath.UPath(file_for_path.abs_src_path)
        target_path = None
        if path not in self._mk_files:
            new_path.parent.mkdir(exist_ok=True, parents=True)
            self._mk_files[path] = file_for_path
            target_path = new_path

        f = self._mk_files[path]
        source_path = upath.UPath(f.abs_src_path)
        if source_path != new_path:
            self._mk_files[path] = file_for_path
            pathhelpers.copy(source_path, new_path)
            target_path = new_path
        pathhelpers.write_file(content, target_path or source_path)


if __name__ == "__main__":
    backend = MkDocsBackend()
