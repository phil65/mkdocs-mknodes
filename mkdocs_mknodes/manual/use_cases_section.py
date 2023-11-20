import mknodes as mk

from mknodes.info import mkdocsconfigfile


nav = mk.MkNav("Use cases")


@nav.route.page(is_index=True, hide="toc")
def _(page: mk.MkPage):
    page += mk.MkTemplate("use_cases_index.jinja")


@nav.route.page("Creating a website via config", hide="toc")
def _(page: mk.MkPage):
    """Create the "Creating a sample website" MkPage."""
    file = mkdocsconfigfile.MkDocsConfigFile("configs/mkdocs_mkdocs.yml")
    section = file.get_section("plugins", "mknodes", keep_path=True)
    config = section.serialize("yaml")
    variables = dict(config=config)
    page += mk.MkTemplate("use_case_default_website.jinja", variables=variables)
