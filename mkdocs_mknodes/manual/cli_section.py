import mknodes as mk


# this is the nav we will populate via decorators.
nav = mk.MkNav("CLI")

CLI_PATH = "mkdocs_mknodes.cli:cli"


def create_cli_section(root_nav: mk.MkNav):
    """Create the "Development" sub-MkNav and attach it to given MkNav."""
    # Now we will create the "Development" section.
    # You might notice that this whole section does not contain any specific
    # reference to mk. That is because all nodes containing metadata are
    # dynamically populated depending on the project the tree is connected to.
    # This means that this section could be imported by other packages and be
    # used without any further adaptation.
    root_nav += nav
    page = nav.add_page(is_index=True, hide="toc")
    page += mk.MkBinaryImage.for_file("docs/assets/cli.gif")
    page += mk.MkJinjaTemplate("cli_index.jinja")
    page.created_by = create_cli_section


@nav.route.page("build", icon="wrench")
def _(page: mk.MkPage):
    page += mk.MkClickDoc(CLI_PATH, prog_name="build")


@nav.route.page("serve", icon="web")
def _(page: mk.MkPage):
    page += mk.MkClickDoc(CLI_PATH, prog_name="serve")


@nav.route.page("create-config", icon="folder-wrench")
def _(page: mk.MkPage):
    page += mk.MkClickDoc(CLI_PATH, prog_name="create-config")
