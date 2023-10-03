INTRO = (
    "This section provides an overview about the sequence of operations applied by"
    " **MkNodes** when running the full build process."
)

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
    " sources are extracted in order to build a context object:\n\n"
    "* metadata.Distribution\n"
    "* PyProject File\n"
    "* MkDocs Config file\n"
    "* Other config files in the cwd\n"
    "* Git repository info\n"
    "* Information from GitHub\n"
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

STEPS = [
    dict(step="Step 1", content=STEP_1),
    dict(step="Step 2", content=STEP_2),
    dict(step="Step 3", content=STEP_3),
    dict(step="Step 4", content=STEP_4),
    dict(step="Step 5", content=STEP_5),
    dict(step="Step 6", content=STEP_6),
    dict(step="Step 7", content=STEP_7),
    dict(step="Step 8", content=STEP_8),
    dict(step="Step 9", content=STEP_9),
    dict(step="Step 10", content=STEP_10),
    dict(step="Step 11", content=STEP_11),
    dict(step="Step 12", content=STEP_12),
    dict(step="Step 13", content=STEP_13),
    dict(step="Step 14", content=STEP_14),
]
