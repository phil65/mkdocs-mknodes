import mknodes


DOC_URL = "https://phil65.github.io/mknodes/"


def create_github_index_md() -> mknodes.MkPage:
    page = mknodes.MkPage("Github index")
    page += mknodes.MkCode.for_object(create_github_index_md)
    page += mknodes.MkHeader("MkNodes", level=1)
    page += mknodes.MkHeader("Don't write docs. Code them.", level=4)
    page += mknodes.MkShields()
    page += mknodes.MkLink(DOC_URL, "Read the completely coded documentation!")
    page += mknodes.MkInstallGuide(header="How to install")
    page += mknodes.MkHeader("All the nodes!")
    page += mknodes.MkClassDiagram(mknodes.MkNode, mode="subclasses", direction="LR")
    return page
