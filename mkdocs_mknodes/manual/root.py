import mknodes as mk

from mknodes import manual
from mknodes.theme import materialtheme


HEADER = r"{{metadata.summary}}"

INFO = "This is the source code for building this website:"

FOOTER = """We are done! This code created the whole website.
We will now go through each section and explain how we created it.
This is done by prepending the code used to create each section / page to the beginning
of every page of this website. We will now start by creating a fancy start page before
explaining all the MkNodes!
"""

DOCSTRING_INFO = """
You will encounter stuff like this quite often: Nodes displaying themselves,
and blurred borders between code, docs, markdown and rendered html.
It will be a quite inception-ish experience.
"""


def build(project: mk.Project[materialtheme.MaterialTheme]) -> mk.MkNav:
    # We will use annotations to explain things a bit.
    annotations = mk.MkAnnotations()  # Our first node! DocStrings: # (1)
    annotations[1] = mk.MkDocStrings(mk.MkAnnotations)

    # MkDocStrings is based on "mkdocstrings" and, well... it can display docstrings.
    # Who would have guessed that? Here are the docstrings for MkDocStrings:

    annotations[2] = mk.MkDocStrings(mk.MkDocStrings)  # (2)
    annotations[3] = mk.MkAdmonition(DOCSTRING_INFO)  # (3)

    # Let us start with building the page.
    # this Nav is basically the root of everything. It corresponds to your root
    # SUMMARY.md and is the root of the complete tree we are building during this tour.
    root_nav = project.get_root()
    project.theme.announcement_bar = mk.MkMetadataBadges("websites")
    project.theme.error_page.content = mk.MkAdmonition("Page does not exist!")
    project.theme.content_area_width = 1300
    project.theme.tooltip_width = 800
    project.linkprovider.add_inv_file("https://mkdocstrings.github.io/objects.inv")
    annotations[4] = mk.MkDocStrings(mk.MkNav)  # (4)

    # now we will create the nav sections and its pages one by one.
    # For demonstration purposes, this process is split up into several functions.
    # Each function here adds another Menu item to the root nav (aka the tabs at the top).
    # We will get there later.
    manual.create_use_cases_section(root_nav)
    manual.create_cli_section(root_nav)
    manual.create_development_section(root_nav)
    annotations[5] = str(root_nav)  # This is the root nav after it was modified: (5)

    # Lets begin with the start page (aka the root index.md).
    # This is the page you are lookin at right now.)
    page = root_nav.add_index_page(hide="toc,nav")

    # A MkPage can contain MkNodes which represent Markdown text.
    page += mk.MkHeader(HEADER, level=3)
    admonition = mk.MkAdmonition(INFO, typ="info", title="Built with MkNodes")
    page += admonition  # This adds (6) to the page.

    # Now we add the MkNode you are looking at right now.
    # DocStrings for for_object: (7)
    page += mk.MkCode.for_object(build)
    page += annotations  # here we add the (invisible) annotations block to the page.

    # We can still add more annotations, things only get written at the very end:
    annotations[6] = admonition
    annotations[7] = mk.MkDocStrings(mk.MkCode.for_object)
    admonition = mk.MkAdmonition(mk.MkCode(str(annotations)))
    annotations[8] = admonition  # annotations in raw text: (8)

    page += mk.MkAdmonition(FOOTER, typ="success")
    return root_nav
