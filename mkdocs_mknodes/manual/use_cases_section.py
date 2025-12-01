import pathlib

import mknodes as mk


nav = mk.MkNav("Use cases")


@nav.route.page(is_index=True, hide="toc")
def _(page: mk.MkPage):
    page += mk.MkTemplate("use_cases_index.jinja")


@nav.route.page("Creating a website via config", hide="toc")
def _(page: mk.MkPage):
    """Create the "Creating a sample website" MkPage."""
    config = pathlib.Path("configs/mkdocs_mkdocs.yml").read_text("utf-8")
    variables = {"config": config}
    page += mk.MkTemplate("use_case_default_website.jinja", variables=variables)
