from __future__ import annotations

from typing import TYPE_CHECKING

from mknodes.utils import log


if TYPE_CHECKING:
    from mknodes.utils import resources


logger = log.get_logger(__name__)


class BuildBackend:
    async def collect(
        self,
        files: dict[str, str | bytes],
        reqs: resources.Resources,
        templates: list,
    ):
        self.collect_extensions(reqs.markdown_extensions)
        self.write_js_links(reqs.js_links)
        self.write_js_files(reqs.js_files)
        self.write_css(reqs.css)
        await self.write_templates(templates)
        self.write_files(files)
        self.write_assets(reqs.assets)

    def write_files(self, files):
        pass

    def write_js_links(self, js_links):
        pass

    def write_js_files(self, js_files):
        pass

    def write_css(self, css):
        pass

    # def write_css_links(self, css):
    #     pass

    def collect_extensions(self, extensions):
        pass

    async def write_templates(self, templates):
        pass

    def write_assets(self, assets):
        pass


if __name__ == "__main__":
    b = BuildBackend()
