import mknodes as mk

from mkdocs_mknodes.appconfig import appconfig


nav = mk.MkNav("Use cases")


@nav.route.page(is_index=True, hide="toc")
def _(page: mk.MkPage):
    page += mk.MkTemplate("use_cases_index.jinja")


@nav.route.page("Creating a website via config", hide="toc")
def _(page: mk.MkPage):
    """Create the "Creating a sample website" MkPage."""
    file = appconfig.AppConfig.from_yaml_file("configs/mkdocs_mkdocs.yml")
    config = file.model_dump()
    variables = dict(config=config)
    page += mk.MkTemplate("use_case_default_website.jinja", variables=variables)
