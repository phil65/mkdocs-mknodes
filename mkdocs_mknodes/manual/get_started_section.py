import mknodes as mk


nav = mk.MkNav("Get started")


INTRO = (
    "This section provides an overview about the sequence of operations applied by"
    " **MkNodes** when running the full build process."
)

# create temporary build directory
STEP_1 = (
    "### Set up working directory\nThe target repository gets cloned in case it is a"
    " remote one. If no explicit build directory for the later steps is provided by the"
    " config, a temporary build folder is created."
)
STEP_2 = (
    "### Create theme\nInitialize the theme object based on which theme is chosen in the"
    " **MkDocs** config / CLI."
)
STEP_3 = (
    "### Create project.\n The theme, the build function, the **Git**"
    " repository (in most cases the current working dir) and a URL linker are"
    " consolidated into one project instance."
)
STEP_4 = (
    "### Create context.\n All available information from following"
    " sources are extracted in order to build a context object:\n"
)

STEP_5 = (
    "### Create environment\nCreate the **jinja2** environment and populate it with all"
    " the data provided by the context object."
)
STEP_6 = (
    "### Build **MkNodes** tree\nNow, since all needed information is available, the"
    " user-coded build function is executed and the node tree is generated"
    " (alternatively, a website template like `MkDefaultWebSite` can be used)"
)
STEP_7 = (
    "### Initialize backends\nThe build backends are initialized. Right now there is one"
    " simple Markdown backend and one **MkDocs** build backend."
)
STEP_8 = (
    "### Collect build artifacts\nThe `BuildCollector` aggregates and preprocesses all"
    " the data from the node tree (navigation hierarchy, Markdown output, required"
    " resources, templates, ...) and passes the prepared data to the build backends."
)
STEP_9 = (
    "### Convert templates\nIf required, convert the template pages which were populated"
    " with Markdown by the user to HTML using the **Python-Markdown** parser."
)
STEP_10 = (
    "### Write to disk using backends\nThe Markdown backend creates plain Markdown pages"
    " and index files on disk.\nThe **MkDocs** backend updates the **Mkdocs**"
    " configuration with information from the node tree and adds the rquired CSS / JS /"
    " etc. resources as well as the required Markdown extensions. Also, all Markdown"
    " files and templates are written to the location where **MkDocs** expects them to"
    " be. In addition, `SUMMARY.md` files are generated to describe the hierarchy. These"
    " files get picked up by **mkdocs-literate-nav** plugin later on."
)

STEP_11 = (
    "### Set edit URIs\n Set the page edit URIs to the recorded caller location (gathered"
    " from `FrameInfo` objects)."
)
STEP_12 = (
    "### Render **jinja2** templates\nThe pages get rendered by **jinja2** and a custom"
    " `LinkReplacer` is doing a bit of work."
)
STEP_13 = "### Finished!\nAfter letting **MkDocs** do its work, the website is ready."
STEP_14 = "### Clean up\nRemove possible temporarily created HTML templates from disk."

INFO_PROVIDERS = [
    "metadata.Distribution",
    "PyProject File",
    "MkDocs Config file",
    "Other config files in the cwd",
    "Git repository info",
    "Information from GitHub",
]


def create_get_started_section(root_nav: mk.MkNav):
    root_nav += nav
    page = nav.add_index_page()
    page += "Welcome to MkNodes! (MkDocs-Plugin-Edition)"


@nav.route.page("Welcome to MkNodes", is_homepage=True)
def _(page: mk.MkPage):
    page += mk.MkCode.for_file(__file__)


@nav.route.page("What is MkNodes?")
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("why_should_i_use_mknodes.jinja")


@nav.route.page("Why should I use it?")
def _(page: mk.MkPage):
    page += mk.MkJinjaTemplate("why_should_i_use_mknodes.jinja")


@nav.route.page("The build process", hide="toc")
def _(page: mk.MkPage):
    ls = mk.MkList(INFO_PROVIDERS)
    node = mk.MkTimeline()
    node.add_item(date="Step 1", content=STEP_1)
    node.add_item(date="Step 2", content=STEP_2)
    node.add_item(date="Step 3", content=STEP_3)
    node.add_item(date="Step 4", content=mk.MkContainer([STEP_4, ls]))
    node.add_item(date="Step 5", content=STEP_5)
    node.add_item(date="Step 6", content=STEP_6)
    node.add_item(date="Step 7", content=STEP_7)
    node.add_item(date="Step 8", content=STEP_8)
    node.add_item(date="Step 9", content=STEP_9)
    node.add_item(date="Step 10", content=STEP_10)
    node.add_item(date="Step 11", content=STEP_11)
    node.add_item(date="Step 12", content=STEP_12)
    node.add_item(date="Step 13", content=STEP_13)
    node.add_item(date="Step 14", content=STEP_14)
    page += INTRO
    page += node


# @nav.route.page("The node tree")
# def _(page: mk.MkPage):
#     page += mk.MkJinjaTemplate("why_should_i_use_mknodes.jinja")
