import mknodes as mk


nav = mk.MkNav("Internals")


STEP_1 = (
    "### Set up the working directory\nClone the repository (in case it is a remote one)"
)
STEP_2 = "### Aggregate info\nAggregate information about the repository from:"
INFO_PROVIDERS = [
    "metadata.Distribution",
    "PyProject File",
    "MkDocs Config file",
    "Other config-related files",
    "Git info (aquired from GitPython)",
    "GitHub info (using PyGitHub)",
]
STEP_3 = "### Build the tree\nBuild the MkNode tree based on Build script / function"
STEP_4 = (
    "### Populate the environment\n"
    "Populate mknodes-specific Jinja environment with all collected metadata"
)
STEP_5 = "### Render Jinja\nRender jinja stuff with our own environment on node level"
STEP_6 = (
    "### Serialize tree to markdown files\n"
    "Convert node tree to a file folder structure containing markdown files "
    "(using literate-nav-style SUMMARY.md files to describe the hierarchy)"
)
STEP_7 = (
    "### Collect requirements\n"
    "Gather information from the nodes about required Extensions / CSS / JavaScript"
)
STEP_8 = (
    "### Build project config\nMerge node requirements with provided MkDocs config file"
)
STEP_9 = (
    "### Menu generation\nLet mkdocs-literate-nav populate the Navigation based on"
    " generated SUMMARY.mds"
)
STEP_10 = (
    "### Convert to HTML\nLet MkDocs convert everything to HTML based on the composite"
    " config"
)


def create_internals_section(root_nav: mk.MkNav):
    """Create the "Internals" Sub-MkNav and attach it to given MkNav."""
    root_nav += nav
    page = nav.add_index_page(hide="toc")
    page += "TODO"


@nav.route.page("Build steps")
def _(page: mk.MkPage):
    node = mk.MkTimeline()
    node.add_item(date="Step 1", content=STEP_1)
    ls = mk.MkList(INFO_PROVIDERS)
    node.add_item(date="Step 2", content=mk.MkContainer([STEP_2, ls]))
    node.add_item(date="Step 3", content=STEP_3)
    node.add_item(date="Step 4", content=STEP_4)
    node.add_item(date="Step 5", content=STEP_5)
    node.add_item(date="Step 6", content=STEP_6)
    node.add_item(date="Step 7", content=STEP_7)
    node.add_item(date="Step 8", content=STEP_8)
    node.add_item(date="Step 9", content=STEP_9)
    node.add_item(date="Step 10", content=STEP_10)
    page += node
    page.created_by = create_internals_section


@nav.route.nav("Complete code")
def _(nav: mk.MkNav):
    nav.parse.module("mknodes/manual/", hide="toc")
